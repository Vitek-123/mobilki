from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
import uvicorn
from typing import List, Optional
from passlib.context import CryptContext
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import logging

import models
from models import (
    User, Product, Shop, Listing, Price,
    ViewHistory, Favorite, PriceAlert,
    ShoppingList, ShoppingListItem,
    Comparison, ComparisonProduct,
    Review
)
import schemas
from database import *

# Импорт сервиса внешних данных
from external_data_service import ExternalDataService
from product_merger import merge_products_alternating

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,  # INFO для нормальной работы, DEBUG слишком много логов
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Уменьшаем уровень логирования для urllib3 (слишком много DEBUG логов)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

# Создание таблиц БД (только если БД доступна)
try:
    models.Base.metadata.create_all(bind=engine)
    logging.info("Таблицы БД созданы/проверены")
except Exception as e:
    logging.warning(f"Не удалось подключиться к БД: {e}. Приложение будет работать, но функции, требующие БД, будут недоступны.")

app = FastAPI(title="Mobil Api", version="0.10.4")

# Инициализация сервиса внешних данных
# Redis можно отключить, установив REDIS_ENABLED=false в .env
redis_enabled = os.getenv("REDIS_ENABLED", "true").lower() in ("true", "1", "yes")
external_data_service = ExternalDataService(
    redis_host=os.getenv("REDIS_HOST", "localhost"),
    redis_port=int(os.getenv("REDIS_PORT", "6379")),
    redis_db=int(os.getenv("REDIS_DB", "0")),
    cache_ttl=int(os.getenv("CACHE_TTL", "10800")),  # 3 часа (10800 секунд)
    redis_enabled=redis_enabled
)

# JWT настройки
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production-min-32-chars")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# OAuth2 схема
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Password hashing
# Используем bcrypt с явной конфигурацией
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Стандартное количество раундов
)


def get_password_hash(password):
    """
    Хеширует пароль с использованием bcrypt.
    Bcrypt имеет ограничение в 72 байта для пароля.
    Обрезает пароль до 72 байт перед хешированием.
    Использует bcrypt напрямую для избежания проблем с passlib.
    """
    if not password:
        raise ValueError("Пароль не может быть пустым")
    
    # Обрезаем пароль до 72 байт ПЕРЕД хешированием
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Обрезаем до 72 байт
        password_bytes = password_bytes[:72]
    
    # Используем bcrypt напрямую, минуя passlib
    # Это позволяет избежать проблем с проверкой длины в passlib
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Возвращаем хеш как строку (passlib ожидает строку)
    return hashed.decode('utf-8')


def verify_password(plain_password, hashed_password):
    """
    Проверяет пароль против хеша.
    Работает как с хешами от passlib, так и с хешами от bcrypt напрямую.
    """
    # Обрезаем пароль до 72 байт перед проверкой (как при хешировании)
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Пробуем проверить через passlib (для старых хешей)
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except:
        # Если не получилось через passlib, пробуем через bcrypt напрямую
        try:
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except:
            return False


# JWT функции
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return user_id
    except JWTError:
        raise credentials_exception


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = verify_token(token, credentials_exception)
    user = db.query(User).filter(User.id_user == user_id).first()
    if user is None:
        raise credentials_exception
    return user


# Разрешаем CORS (важно для мобильного приложения)
from fastapi.middleware.cors import CORSMiddleware

# cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://172.20.10.2:8000,http://172.20.10.3:8000") #house
# cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000") #iphone
# cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://10.201.241.230:8000") #ranepa
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://192.168.0.16:8000") #houme
cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Используем переменные окружения
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Существующие эндпоинты для пользователя
@app.post("/add_user", response_model=schemas.UserResponse)
def create_user(user: schemas.CreateUser, db: Session = Depends(get_db)):
    try:
        # Валидация входных данных
        if not user.login or not user.login.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Логин не может быть пустым"
            )
        
        if not user.email or not user.email.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email не может быть пустым"
            )
        
        # Валидация пароля
        # Сначала проверяем минимальную длину
        if not user.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пароль не может быть пустым"
            )
        
        password_length = len(user.password)
        if password_length < 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пароль должен содержать минимум 4 символа"
            )
        
        # Затем проверяем максимальную длину в байтах (ограничение bcrypt - 72 байта)
        # Проверяем только если пароль явно длинный (больше 70 символов)
        # Для коротких паролей проверка не нужна
        if password_length > 70:
            password_bytes = user.password.encode('utf-8')
            password_bytes_length = len(password_bytes)
            if password_bytes_length > 91:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Пароль слишком длинный ({password_bytes_length} байт, максимум 72 байта)"
                )

        # Проверка существования пользователя
        user_exists = db.query(User).filter(
            (User.login == user.login) | (User.email == user.email)
        ).first()

        if user_exists:
            if user_exists.login == user.login:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Пользователь с таким логином уже существует"
                )
            elif user_exists.email == user.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Пользователь с такой почтой уже существует"
                )

        # Хеширование пароля с обработкой ошибок
        # Если мы дошли сюда, пароль прошел валидацию
        try:
            # Обрезаем пароль до 72 байт ПЕРЕД передачей в функцию хеширования
            # Это важно, так как passlib проверяет длину до хеширования
            password_for_hash = user.password
            password_bytes_check = password_for_hash.encode('utf-8')
            password_bytes_len = len(password_bytes_check)
            
            # Если пароль длиннее 72 байт, обрезаем его
            if password_bytes_len > 72:
                password_for_hash = password_bytes_check[:72].decode('utf-8', errors='ignore')
                # После обрезки проверяем, что пароль не стал слишком коротким
                if len(password_for_hash) < 4:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Пароль слишком длинный. После обрезки до 72 байт он стал слишком коротким."
                    )
            
            # Хешируем пароль (функция get_password_hash также обрежет пароль, если нужно)
            hashed_password = get_password_hash(password_for_hash)
        except HTTPException:
            raise
        except Exception as e:
            # Обрабатываем все ошибки от passlib/bcrypt
            error_msg = str(e).lower()
            
            # Проверяем, связана ли ошибка с длиной пароля
            if "72" in error_msg or "bytes" in error_msg or "too long" in error_msg or "truncate" in error_msg:
                # Это ошибка о длине пароля - возвращаем понятное сообщение
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Пароль слишком длинный (максимум 72 байта). Попробуйте более короткий пароль."
                )
            
            # Другие ошибки
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при хешировании пароля: {str(e)}"
            )
        
        # Создание нового пользователя
        new_user = User(
            login=user.login.strip(),
            password=hashed_password,
            email=user.email.strip()
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    
    except HTTPException:
        # Пробрасываем HTTP исключения как есть
        raise
    except Exception as e:
        # Обрабатываем все остальные исключения (ошибки БД и т.д.)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании пользователя: {str(e)}"
        )


@app.post("/login", response_model=schemas.TokenResponse)
def come_in(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.login == user.login).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )

    if not verify_password(user.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный пароль"
        )

    # Создаем JWT токен
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.id_user}, expires_delta=access_token_expires
    )
    
    return schemas.TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=schemas.UserResponse(
            id_user=db_user.id_user,
            login=db_user.login,
            email=db_user.email
        )
    )


# Эндпоинты для продуктов (только внешние источники - API и парсинг)
@app.get("/products", response_model=schemas.ProductsResponse)
def get_products(
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=100),
        search: Optional[str] = Query(None, description="Поисковый запрос"),
        use_cache: bool = Query(True, description="Использовать кэш"),
        db: Session = Depends(get_db)
):
    """
    Поиск товаров с чередованием
    Если search не указан, возвращает пустой результат
    """
    try:
        if not search:
            return schemas.ProductsResponse(products=[], total=0)
        
        logging.info("=" * 80)
        logging.info(f"🔍 ПОИСК ТОВАРОВ ПО ЗАПРОСУ: '{search}'")
        logging.info(f"   Параметры: skip={skip}, limit={limit}, use_cache={use_cache}")
        logging.info("=" * 80)
        
        # Получаем товары из внешнего источника
        external_products = []
        try:
            logging.info(f"📡 Запрос к внешнему источнику данных (Яндекс.Маркет)...")
            external_raw = external_data_service.aggregate_by_product(
                query=search,
                use_cache=use_cache
            )
            logging.info(f"✅ Получено {len(external_raw)} товаров из внешнего источника")
            # Преобразуем в формат для merger
            for item in external_raw:
                external_products.append({
                    "id_product": abs(hash(f"{item['brand']}_{item['model']}")) % 1000000,
                    "title": item['title'],
                    "brand": item['brand'],
                    "model": item['model'],
                    "description": item.get('description'),
                    "image": item.get('image'),
                    "prices": item['prices'],
                    "min_price": item.get('min_price'),
                    "max_price": item.get('max_price')
                })
        except Exception as e:
            logging.error(f"Ошибка при получении товаров из внешнего источника: {e}")
        
        # Получаем товары из БД
        db_products = []
        try:
            query = db.query(Product)
            if search:
                search_term = f"%{search.lower()}%"
                query = query.filter(Product.title.ilike(search_term))
            
            products = query.limit(100).all()  # Берем больше для чередования
            
            for product in products:
                listings = db.query(Listing).filter(Listing.product_id == product.id_product).all()
                prices = []
                prices_values = []
                product_url = None  # URL товара из listings
                
                # Получаем URL из первого listing, если есть
                if listings:
                    product_url = listings[0].url
                
                for listing in listings:
                    latest_price = db.query(Price).filter(
                        Price.listing_id == listing.id_listing
                    ).order_by(Price.scraped_at.desc()).first()
                    
                    if latest_price and listing.shop:
                        prices.append({
                            "price": float(latest_price.price),
                            "shop_name": listing.shop.name,
                            "url": listing.url,  # URL из таблицы listings
                            "scraped_at": latest_price.scraped_at.isoformat()
                        })
                        prices_values.append(float(latest_price.price))
                    elif listing.shop and listing.url:
                        # Если нет цены в prices, но есть listing с URL, добавляем его
                        # Это важно для товаров из БД, у которых может не быть записей в prices
                        prices.append({
                            "price": float(product.price) if product.price else 0.0,
                            "shop_name": listing.shop.name,
                            "url": listing.url,  # URL из таблицы listings
                            "scraped_at": datetime.now().isoformat()
                        })
                        if product.price:
                            prices_values.append(float(product.price))
                
                # Добавляем товар даже если нет цен в prices, используем price из products
                # Если есть цены в prices, используем их, иначе используем price из products
                if prices_values:
                    # Есть цены в таблице prices
                    product_price = min(prices_values)
                    min_price = min(prices_values)
                    max_price = max(prices_values)
                elif product.price:
                    # Нет цен в prices, но есть price в products
                    product_price = float(product.price)
                    min_price = product_price
                    max_price = product_price
                    # Создаем фиктивную цену для отображения, если еще не создана
                    if not prices:
                        # Используем магазин из listings, если есть
                        shop_name = None
                        if listings and listings[0].shop:
                            shop_name = listings[0].shop.name
                        else:
                            # Если нет listings, ищем первый доступный магазин в БД
                            first_shop = db.query(Shop).first()
                            if first_shop:
                                shop_name = first_shop.name
                            else:
                                shop_name = "Магазин"  # Дефолтное значение
                        
                        prices.append({
                            "price": product_price,
                            "shop_name": shop_name,
                            "url": product_url if product_url else None,  # URL из listings
                            "scraped_at": datetime.now().isoformat()
                        })
                else:
                    # Нет ни цен в prices, ни price в products
                    product_price = None
                    min_price = None
                    max_price = None
                
                # Добавляем товар в любом случае (даже без цен)
                db_products.append({
                    "id_product": product.id_product,
                    "title": product.title,
                    "brand": None,  # Поле удалено из БД
                    "model": None,  # Поле удалено из БД
                    "description": None,  # Поле удалено из БД
                    "image": product.image,
                    "price": product_price,
                    "prices": prices,
                    "min_price": min_price,
                    "max_price": max_price
                })
        except Exception as e:
            logging.error(f"Ошибка при получении товаров из БД: {e}")
        
        # Логируем количество товаров перед чередованием
        logging.info(f"📦 Перед чередованием (поиск '{search}'): внешний источник={len(external_products)}, БД={len(db_products)}")
        
        # Объединяем товары с чередованием
        merged_products = merge_products_alternating(
            external_products=external_products,
            db_products=db_products,
            static_products=[]  # Статические товары уже в БД
        )
        
        logging.info(f"🔄 После чередования: {len(merged_products)} товаров")
        
        # Применяем пагинацию
        total = len(merged_products)
        paginated_products = merged_products[skip:skip + limit]
        
        
        # Преобразование в формат API
        products_with_prices = []
        for item in paginated_products:
            # Получаем URL из первой цены, если есть (для товаров из Яндекс.Маркет)
            product_url = None
            if item.get('prices') and len(item['prices']) > 0:
                product_url = item['prices'][0].get('url')
            
            product_response = schemas.ProductResponse(
                id_product=item['id_product'],
                title=item['title'],
                brand=item.get('brand'),
                model=item.get('model'),
                image=item.get('image'),
                description=item.get('description'),
                price=item.get('price'),
                url=product_url  # URL товара для кнопки "Купить"
            )
            
            # Преобразование цен
            price_responses = []
            for price_data in item['prices']:
                price_response = schemas.PriceResponse(
                    price=price_data['price'],
                    scraped_at=datetime.fromisoformat(price_data['scraped_at']) if isinstance(price_data['scraped_at'], str) else price_data['scraped_at'],
                    shop_name=price_data['shop_name'],
                    shop_id=abs(hash(price_data['shop_name'])) % 10000,
                    url=price_data.get('url')
                )
                price_responses.append(price_response)
            
            product_with_prices = schemas.ProductWithPrices(
                product=product_response,
                prices=price_responses,
                min_price=item.get('min_price'),
                max_price=item.get('max_price')
            )
            products_with_prices.append(product_with_prices)
        
        logging.info(f"Возвращено {len(products_with_prices)} товаров (внешний источник: {len(external_products)}, БД: {len(db_products)}, всего: {total})")
        return schemas.ProductsResponse(
            products=products_with_prices,
            total=total
        )
    except Exception as e:
        logging.error(f"Ошибка при получении продуктов: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении продуктов: {str(e)}"
        )


@app.get("/products/popular", response_model=schemas.ProductsResponse)
def get_popular_products(
    limit: int = Query(10, ge=1, le=50, description="Количество популярных товаров"),
    use_cache: bool = Query(True, description="Использовать кэш"),
    category: str = Query("электроника", description="Категория товаров"),
    db: Session = Depends(get_db)
):
    """
    Получение топ популярных товаров
    """
    try:
        logging.info("=" * 80)
        logging.info(f"🔵 ПОЛУЧЕН ЗАПРОС на /products/popular")
        logging.info(f"   Параметры: limit={limit}, category={category}, use_cache={use_cache}")
        logging.info("=" * 80)
        
        # Получаем популярные товары с таймаутом
        external_products = []
        try:
            import threading
            import queue
            
            result_queue = queue.Queue()
            exception_queue = queue.Queue()
            
            def fetch_external_products():
                try:
                    products = external_data_service.get_popular_products(
                        limit=limit,
                        use_cache=use_cache,
                        category=category
                    )
                    result_queue.put(products)
                except Exception as e:
                    exception_queue.put(e)
            
            # Запускаем получение товаров в отдельном потоке
            thread = threading.Thread(target=fetch_external_products, daemon=True)
            thread.start()
            thread.join(timeout=60)  # Увеличиваем таймаут до 60 секунд
            
            if thread.is_alive():
                logging.warning("⏱️ Таймаут при получении товаров (60 сек). Товары не получены.")
                products = []
            elif not exception_queue.empty():
                exception = exception_queue.get()
                logging.error(f"❌ Исключение при получении товаров: {exception}", exc_info=exception)
                products = []
            elif not result_queue.empty():
                products = result_queue.get()
                logging.info(f"✅ Получено {len(products)} товаров")
                
                if not products:
                    logging.warning("⚠️ Получен пустой список товаров")
                
                if products:
                    logging.info(f"   Примеры товаров: {', '.join([p.get('title', 'Unknown')[:30] for p in products[:3]])}")
                
                # Преобразуем в формат для merger
                logging.info(f"🔄 Обрабатываем {len(products)} товаров для добавления в список")
                for item in products:
                    try:
                        # Товары из external_data_service.get_popular_products всегда имеют brand и model
                        # Если они None, устанавливаем значения по умолчанию
                        brand = item.get('brand')
                        model = item.get('model')
                        
                        # Если brand или model отсутствуют (None), устанавливаем значения по умолчанию
                        # Это товары из внешнего источника, поэтому они должны быть добавлены
                        if brand is None:
                            brand = "Не указан"
                            logging.debug(f"⚠️ Товар без brand, устанавливаем 'Не указан': {item.get('title', 'Unknown')[:50]}")
                        if model is None:
                            model = "Не указана"
                            logging.debug(f"⚠️ Товар без model, устанавливаем 'Не указана': {item.get('title', 'Unknown')[:50]}")
                        
                        # Добавляем товар из внешнего источника
                        external_products.append({
                            "id_product": abs(hash(f"{brand}_{model}_{item.get('title', '')}")) % 1000000,
                            "title": item.get('title', 'Без названия'),
                            "brand": brand,
                            "model": model,
                            "description": item.get('description'),
                            "image": item.get('image'),
                            "prices": item.get('prices', []),
                            "min_price": item.get('min_price'),
                            "max_price": item.get('max_price')
                        })
                        logging.info(f"✅ Добавлен товар: {item.get('title', 'Unknown')[:50]} (brand={brand}, model={model})")
                    except Exception as e:
                        logging.error(f"❌ Ошибка при обработке товара: {e}, товар: {item}", exc_info=True)
                
                logging.info(f"📊 Итого добавлено товаров: {len(external_products)}")
                
                # Если товаров нет, логируем предупреждение
                if len(external_products) == 0:
                    logging.warning("⚠️ Нет товаров из внешнего источника")
            else:
                logging.warning("⚠️ Не получено товаров (пустая очередь)")
                products = []
        except Exception as e:
            logging.error(f"❌ Критическая ошибка при получении товаров: {e}", exc_info=True)
        
        # Финальная проверка: если товаров нет, логируем предупреждение
        if len(external_products) == 0:
            logging.warning("=" * 80)
            logging.warning("⚠️ КРИТИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ: Нет товаров из внешнего источника (Яндекс.Маркет)")
            logging.warning("   Это означает, что:")
            logging.warning("   1. Яндекс.Маркет API не настроен (YANDEX_OAUTH_TOKEN не установлен)")
            logging.warning("   2. ИЛИ парсер Яндекс.Маркет не работает")
            logging.warning("   3. ИЛИ произошла ошибка при загрузке товаров")
            logging.warning("   На главном экране будут отображаться только товары из БД")
            logging.warning("=" * 80)
        
        # Получаем товары из БД (включая статические)
        db_products = []
        try:
            # Берем больше товаров из БД для чередования
            db_limit = max(limit * 2, 20)  # Берем минимум 20 товаров из БД
            products = db.query(Product).limit(db_limit).all()
            logging.info(f"Загружено {len(products)} товаров из таблицы products для обработки")
            
            for product in products:
                listings = db.query(Listing).filter(Listing.product_id == product.id_product).all()
                prices = []
                prices_values = []
                product_url = None  # URL товара из listings
                
                # Получаем URL из первого listing, если есть
                if listings:
                    product_url = listings[0].url
                
                for listing in listings:
                    latest_price = db.query(Price).filter(
                        Price.listing_id == listing.id_listing
                    ).order_by(Price.scraped_at.desc()).first()
                    
                    if latest_price and listing.shop:
                        prices.append({
                            "price": float(latest_price.price),
                            "shop_name": listing.shop.name,
                            "url": listing.url,
                            "scraped_at": latest_price.scraped_at.isoformat()
                        })
                        prices_values.append(float(latest_price.price))
                
                # Добавляем товар даже если нет цен в prices, используем price из products
                # Если есть цены в prices, используем их, иначе используем price из products
                if prices_values:
                    # Есть цены в таблице prices
                    product_price = min(prices_values)
                    min_price = min(prices_values)
                    max_price = max(prices_values)
                elif product.price:
                    # Нет цен в prices, но есть price в products
                    product_price = float(product.price)
                    min_price = product_price
                    max_price = product_price
                    # Создаем фиктивную цену для отображения
                    if not prices:
                        # Используем магазин из listings, если есть
                        shop_name = None
                        if listings and listings[0].shop:
                            shop_name = listings[0].shop.name
                        else:
                            # Если нет listings, ищем первый доступный магазин в БД
                            first_shop = db.query(Shop).first()
                            if first_shop:
                                shop_name = first_shop.name
                            else:
                                shop_name = "Магазин"  # Дефолтное значение, если нет магазинов
                        
                        prices.append({
                            "price": product_price,
                            "shop_name": shop_name,
                            "url": product_url if product_url else None,  # URL из listings, если есть
                            "scraped_at": datetime.now().isoformat()
                        })
                else:
                    # Нет ни цен в prices, ни price в products
                    product_price = None
                    min_price = None
                    max_price = None
                    # Но все равно создаем запись цены для отображения, если есть URL
                    if not prices and product_url:
                        # Используем магазин из listings, если есть
                        shop_name = None
                        if listings and listings[0].shop:
                            shop_name = listings[0].shop.name
                        else:
                            # Если нет listings, ищем первый доступный магазин в БД
                            first_shop = db.query(Shop).first()
                            if first_shop:
                                shop_name = first_shop.name
                            else:
                                shop_name = "Магазин"  # Дефолтное значение
                        
                        prices.append({
                            "price": 0.0,  # Цена неизвестна
                            "shop_name": shop_name,
                            "url": product_url if product_url else None,  # URL из listings, если есть
                            "scraped_at": datetime.now().isoformat()
                        })
                
                # Добавляем товар в любом случае (даже без цен)
                db_products.append({
                    "id_product": product.id_product,
                    "title": product.title,
                    "brand": None,  # Поле удалено из БД
                    "model": None,  # Поле удалено из БД
                    "description": None,  # Поле удалено из БД
                    "image": product.image,
                    "price": product_price,
                    "prices": prices,
                    "min_price": min_price,
                    "max_price": max_price,
                    "url": product_url  # Добавляем URL товара
                })
            
            logging.info(f"✅ Получено {len(db_products)} товаров из БД (из {len(products)} обработанных)")
            if db_products:
                logging.info(f"   Примеры товаров из БД: {', '.join([p['title'][:30] for p in db_products[:3]])}")
        except Exception as e:
            logging.error(f"Ошибка при получении товаров из БД: {e}")
        
        # Логируем количество товаров перед чередованием
        logging.info(f"📦 Перед чередованием: внешний источник={len(external_products)}, БД={len(db_products)}")
        if external_products:
            logging.info(f"   ✅ Примеры товаров: {', '.join([p.get('title', 'Unknown')[:30] for p in external_products[:3]])}")
            # Детальное логирование товаров
            for i, p in enumerate(external_products[:3], 1):
                logging.info(f"      {i}. {p.get('title', 'Unknown')[:50]} (brand={p.get('brand', 'None')}, model={p.get('model', 'None')})")
        else:
            logging.warning(f"   ⚠️ Нет товаров из внешнего источника!")
        if db_products:
            logging.info(f"   ✅ Примеры товаров из БД: {', '.join([p.get('title', 'Unknown')[:30] for p in db_products[:3]])}")
        
        # Объединяем товары с чередованием
        merged_products = merge_products_alternating(
            external_products=external_products,
            db_products=db_products,
            static_products=[]  # Статические товары уже в БД
        )
        
        logging.info(f"🔄 После чередования: {len(merged_products)} товаров")
        
        # Ограничиваем количество до limit
        final_products = merged_products[:limit]
        
        # Логируем источники товаров в финальном списке
        external_count = sum(1 for p in final_products if p.get('brand') is not None and p.get('brand') != "Не указан")
        db_count = sum(1 for p in final_products if p.get('brand') is None or p.get('brand') == "Не указан")
        logging.info(f"📊 Финальный список: {len(final_products)} товаров (внешний источник: {external_count}, БД: {db_count})")
        
        # Детальное логирование первых 5 товаров для отладки
        if final_products:
            logging.info("🔍 Первые 5 товаров в финальном списке:")
            for i, p in enumerate(final_products[:5], 1):
                brand = p.get('brand')
                source = "Внешний источник" if (brand is not None and brand != "Не указан") else "БД"
                logging.info(f"   {i}. [{source}] {p.get('title', 'Unknown')[:50]} (brand={brand}, model={p.get('model', 'None')})")
        else:
            logging.warning("⚠️ Финальный список товаров пуст!")
        
        # Преобразование в формат API
        products_with_prices = []
        for item in final_products:
            # Получаем URL из первой цены, если есть (для товаров из Яндекс.Маркет)
            product_url = None
            if item.get('prices') and len(item['prices']) > 0:
                product_url = item['prices'][0].get('url')
            
            product_response = schemas.ProductResponse(
                id_product=item['id_product'],
                title=item['title'],
                brand=item.get('brand'),
                model=item.get('model'),
                image=item.get('image'),
                description=item.get('description'),
                price=item.get('price'),
                url=product_url  # URL товара для кнопки "Купить"
            )
            
            # Преобразование цен
            price_responses = []
            for price_data in item['prices']:
                price_response = schemas.PriceResponse(
                    price=price_data['price'],
                    scraped_at=datetime.fromisoformat(price_data['scraped_at']) if isinstance(price_data['scraped_at'], str) else price_data['scraped_at'],
                    shop_name=price_data['shop_name'],
                    shop_id=abs(hash(price_data['shop_name'])) % 10000,
                    url=price_data.get('url')
                )
                price_responses.append(price_response)
            
            product_with_prices = schemas.ProductWithPrices(
                product=product_response,
                prices=price_responses,
                min_price=item.get('min_price'),
                max_price=item.get('max_price')
            )
            products_with_prices.append(product_with_prices)
        
        # Подсчитываем источники в финальном списке
        external_final = sum(1 for p in final_products if p.get('brand') is not None)
        db_final = sum(1 for p in final_products if p.get('brand') is None)
        logging.info(f"✅ Возвращаем {len(products_with_prices)} товаров клиенту (внешний источник: {external_final}, БД: {db_final})")
        return schemas.ProductsResponse(
            products=products_with_prices,
            total=len(merged_products)
        )
    except Exception as e:
        logging.error(f"Ошибка при получении популярных товаров: {e}", exc_info=True)
        # Возвращаем пустой список вместо ошибки, чтобы приложение не падало
        return schemas.ProductsResponse(
            products=[],
            total=0
        )


# ==================== ИСТОРИЯ ПРОСМОТРОВ ====================

@app.post("/user/view-history", response_model=schemas.ViewHistoryResponse)
def add_view_history(
    product_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Добавить товар в историю просмотров"""
    try:
        # Проверяем, существует ли товар
        product = db.query(Product).filter(Product.id_product == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        # Проверяем, есть ли уже запись за сегодня (опционально - можно убрать)
        existing_view = db.query(ViewHistory).filter(
            ViewHistory.user_id == current_user.id_user,
            ViewHistory.product_id == product_id
        ).order_by(ViewHistory.viewed_at.desc()).first()
        
        # Если есть недавняя запись (менее часа назад), обновляем время
        if existing_view:
            from datetime import timedelta
            if existing_view.viewed_at > datetime.utcnow() - timedelta(hours=1):
                existing_view.viewed_at = datetime.utcnow()
                db.commit()
                db.refresh(existing_view)
                # Получаем продукт с ценами для ответа
                product = db.query(Product).options(
                    joinedload(Product.listings).joinedload(Listing.prices),
                    joinedload(Product.listings).joinedload(Listing.shop)
                ).filter(Product.id_product == product_id).first()
                
                if product:
                    latest_prices = []
                    shop_prices = {}
                    for listing in product.listings:
                        if listing.prices:
                            latest_price = max(listing.prices, key=lambda x: x.scraped_at)
                            if listing.shop_id not in shop_prices:
                                latest_prices.append(schemas.PriceResponse(
                                    price=float(latest_price.price),
                                    scraped_at=latest_price.scraped_at,
                                    shop_name=listing.shop.name,
                                    shop_id=listing.shop_id,
                                    url=listing.url
                                ))
                                shop_prices[listing.shop_id] = latest_price
                    
                    prices_values = [p.price for p in latest_prices]
                    min_price = min(prices_values) if prices_values else None
                    max_price = max(prices_values) if prices_values else None
                    
                    product_with_prices = schemas.ProductWithPrices(
                        product=schemas.ProductResponse.model_validate(product),
                        prices=latest_prices,
                        min_price=min_price,
                        max_price=max_price
                    )
                    
                    return schemas.ViewHistoryResponse(
                        id_view=existing_view.id_view,
                        product=product_with_prices,
                        viewed_at=existing_view.viewed_at
                    )
        
        # Создаем новую запись
        new_view = ViewHistory(
            user_id=current_user.id_user,
            product_id=product_id
        )
        db.add(new_view)
        db.commit()
        db.refresh(new_view)
        
        # Получаем продукт с ценами для ответа
        product = db.query(Product).options(
            joinedload(Product.listings).joinedload(Listing.prices),
            joinedload(Product.listings).joinedload(Listing.shop)
        ).filter(Product.id_product == product_id).first()
        
        if product:
            latest_prices = []
            shop_prices = {}
            for listing in product.listings:
                if listing.prices:
                    latest_price = max(listing.prices, key=lambda x: x.scraped_at)
                    if listing.shop_id not in shop_prices:
                        latest_prices.append(schemas.PriceResponse(
                            price=float(latest_price.price),
                            scraped_at=latest_price.scraped_at,
                            shop_name=listing.shop.name,
                            shop_id=listing.shop_id,
                            url=listing.url
                        ))
                        shop_prices[listing.shop_id] = latest_price
            
            prices_values = [p.price for p in latest_prices]
            min_price = min(prices_values) if prices_values else None
            max_price = max(prices_values) if prices_values else None
            
            product_with_prices = schemas.ProductWithPrices(
                product=schemas.ProductResponse.model_validate(product),
                prices=latest_prices,
                min_price=min_price,
                max_price=max_price
            )
            
            return schemas.ViewHistoryResponse(
                id_view=new_view.id_view,
                product=product_with_prices,
                viewed_at=new_view.viewed_at
            )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при добавлении в историю: {str(e)}"
        )


@app.get("/user/view-history", response_model=schemas.ViewHistoryListResponse)
def get_view_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить историю просмотров пользователя"""
    try:
        views = db.query(ViewHistory).filter(
            ViewHistory.user_id == current_user.id_user
        ).order_by(ViewHistory.viewed_at.desc()).offset(skip).limit(limit).all()
        
        total = db.query(ViewHistory).filter(
            ViewHistory.user_id == current_user.id_user
        ).count()
        
        views_response = []
        for view in views:
            # Получаем продукт с ценами
            product = db.query(Product).options(
                joinedload(Product.listings).joinedload(Listing.prices),
                joinedload(Product.listings).joinedload(Listing.shop)
            ).filter(Product.id_product == view.product_id).first()
            
            if product:
                # Формируем цены
                latest_prices = []
                shop_prices = {}
                for listing in product.listings:
                    if listing.prices:
                        latest_price = max(listing.prices, key=lambda x: x.scraped_at)
                        if listing.shop_id not in shop_prices:
                            latest_prices.append(schemas.PriceResponse(
                                price=float(latest_price.price),
                                scraped_at=latest_price.scraped_at,
                                shop_name=listing.shop.name,
                                shop_id=listing.shop_id,
                                url=listing.url
                            ))
                            shop_prices[listing.shop_id] = latest_price
                
                prices_values = [p.price for p in latest_prices]
                min_price = min(prices_values) if prices_values else None
                max_price = max(prices_values) if prices_values else None
                
                product_with_prices = schemas.ProductWithPrices(
                    product=schemas.ProductResponse.model_validate(product),
                    prices=latest_prices,
                    min_price=min_price,
                    max_price=max_price
                )
                
                views_response.append(schemas.ViewHistoryResponse(
                    id_view=view.id_view,
                    product=product_with_prices,
                    viewed_at=view.viewed_at
                ))
        
        return schemas.ViewHistoryListResponse(views=views_response, total=total)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении истории: {str(e)}"
        )


@app.delete("/user/view-history")
def clear_view_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Очистить историю просмотров"""
    try:
        db.query(ViewHistory).filter(
            ViewHistory.user_id == current_user.id_user
        ).delete()
        db.commit()
        return {"message": "История просмотров очищена"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при очистке истории: {str(e)}"
        )


# ==================== ИЗБРАННОЕ ====================

@app.post("/favorites/{product_id}", response_model=schemas.FavoriteResponse)
def add_to_favorites(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Добавить товар в избранное"""
    try:
        # Проверяем, существует ли товар
        product = db.query(Product).filter(Product.id_product == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        # Проверяем, не добавлен ли уже
        existing = db.query(Favorite).filter(
            Favorite.user_id == current_user.id_user,
            Favorite.product_id == product_id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Товар уже в избранном")
        
        # Создаем новую запись
        new_favorite = Favorite(
            user_id=current_user.id_user,
            product_id=product_id
        )
        db.add(new_favorite)
        db.commit()
        db.refresh(new_favorite)
        
        # Получаем продукт с ценами
        product = db.query(Product).options(
            joinedload(Product.listings).joinedload(Listing.prices),
            joinedload(Product.listings).joinedload(Listing.shop)
        ).filter(Product.id_product == product_id).first()
        
        latest_prices = []
        shop_prices = {}
        for listing in product.listings:
            if listing.prices:
                latest_price = max(listing.prices, key=lambda x: x.scraped_at)
                if listing.shop_id not in shop_prices:
                    latest_prices.append(schemas.PriceResponse(
                        price=float(latest_price.price),
                        scraped_at=latest_price.scraped_at,
                        shop_name=listing.shop.name,
                        shop_id=listing.shop_id,
                        url=listing.url
                    ))
                    shop_prices[listing.shop_id] = latest_price
        
        prices_values = [p.price for p in latest_prices]
        min_price = min(prices_values) if prices_values else None
        max_price = max(prices_values) if prices_values else None
        
        product_with_prices = schemas.ProductWithPrices(
            product=schemas.ProductResponse.model_validate(product),
            prices=latest_prices,
            min_price=min_price,
            max_price=max_price
        )
        
        return schemas.FavoriteResponse(
            id_favorite=new_favorite.id_favorite,
            product=product_with_prices,
            added_at=new_favorite.added_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при добавлении в избранное: {str(e)}"
        )


@app.get("/favorites", response_model=schemas.FavoritesListResponse)
def get_favorites(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить избранное пользователя"""
    try:
        favorites = db.query(Favorite).filter(
            Favorite.user_id == current_user.id_user
        ).order_by(Favorite.added_at.desc()).offset(skip).limit(limit).all()
        
        total = db.query(Favorite).filter(
            Favorite.user_id == current_user.id_user
        ).count()
        
        favorites_response = []
        for favorite in favorites:
            product = db.query(Product).options(
                joinedload(Product.listings).joinedload(Listing.prices),
                joinedload(Product.listings).joinedload(Listing.shop)
            ).filter(Product.id_product == favorite.product_id).first()
            
            if product:
                latest_prices = []
                shop_prices = {}
                for listing in product.listings:
                    if listing.prices:
                        latest_price = max(listing.prices, key=lambda x: x.scraped_at)
                        if listing.shop_id not in shop_prices:
                            latest_prices.append(schemas.PriceResponse(
                                price=float(latest_price.price),
                                scraped_at=latest_price.scraped_at,
                                shop_name=listing.shop.name,
                                shop_id=listing.shop_id,
                                url=listing.url
                            ))
                            shop_prices[listing.shop_id] = latest_price
                
                prices_values = [p.price for p in latest_prices]
                min_price = min(prices_values) if prices_values else None
                max_price = max(prices_values) if prices_values else None
                
                product_with_prices = schemas.ProductWithPrices(
                    product=schemas.ProductResponse.model_validate(product),
                    prices=latest_prices,
                    min_price=min_price,
                    max_price=max_price
                )
                
                favorites_response.append(schemas.FavoriteResponse(
                    id_favorite=favorite.id_favorite,
                    product=product_with_prices,
                    added_at=favorite.added_at
                ))
        
        return schemas.FavoritesListResponse(favorites=favorites_response, total=total)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении избранного: {str(e)}"
        )


@app.delete("/favorites/{product_id}")
def remove_from_favorites(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удалить товар из избранного"""
    try:
        favorite = db.query(Favorite).filter(
            Favorite.user_id == current_user.id_user,
            Favorite.product_id == product_id
        ).first()
        
        if not favorite:
            raise HTTPException(status_code=404, detail="Товар не найден в избранном")
        
        db.delete(favorite)
        db.commit()
        return {"message": "Товар удален из избранного"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении из избранного: {str(e)}"
        )


# ==================== ОТСЛЕЖИВАНИЕ ЦЕН ====================

@app.post("/user/price-alerts", response_model=schemas.PriceAlertResponse)
def create_price_alert(
    alert: schemas.PriceAlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создать отслеживание цены"""
    try:
        # Проверяем, существует ли товар
        product = db.query(Product).filter(Product.id_product == alert.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        
        # Проверяем, не создано ли уже отслеживание
        existing = db.query(PriceAlert).filter(
            PriceAlert.user_id == current_user.id_user,
            PriceAlert.product_id == alert.product_id,
            PriceAlert.is_active == 1
        ).first()
        
        if existing:
            # Обновляем целевую цену
            existing.target_price = alert.target_price
            db.commit()
            db.refresh(existing)
        else:
            # Создаем новое отслеживание
            new_alert = PriceAlert(
                user_id=current_user.id_user,
                product_id=alert.product_id,
                target_price=alert.target_price,
                is_active=1
            )
            db.add(new_alert)
            db.commit()
            db.refresh(new_alert)
            existing = new_alert
        
        # Получаем продукт с ценами
        product = db.query(Product).options(
            joinedload(Product.listings).joinedload(Listing.prices),
            joinedload(Product.listings).joinedload(Listing.shop)
        ).filter(Product.id_product == alert.product_id).first()
        
        latest_prices = []
        shop_prices = {}
        for listing in product.listings:
            if listing.prices:
                latest_price = max(listing.prices, key=lambda x: x.scraped_at)
                if listing.shop_id not in shop_prices:
                    latest_prices.append(schemas.PriceResponse(
                        price=float(latest_price.price),
                        scraped_at=latest_price.scraped_at,
                        shop_name=listing.shop.name,
                        shop_id=listing.shop_id,
                        url=listing.url
                    ))
                    shop_prices[listing.shop_id] = latest_price
        
        prices_values = [p.price for p in latest_prices]
        min_price = min(prices_values) if prices_values else None
        max_price = max(prices_values) if prices_values else None
        
        product_with_prices = schemas.ProductWithPrices(
            product=schemas.ProductResponse.model_validate(product),
            prices=latest_prices,
            min_price=min_price,
            max_price=max_price
        )
        
        return schemas.PriceAlertResponse(
            id_alert=existing.id_alert,
            product=product_with_prices,
            target_price=float(existing.target_price),
            is_active=bool(existing.is_active),
            created_at=existing.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании отслеживания: {str(e)}"
        )


@app.get("/user/price-alerts", response_model=schemas.PriceAlertsListResponse)
def get_price_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить отслеживания цен пользователя"""
    try:
        alerts = db.query(PriceAlert).filter(
            PriceAlert.user_id == current_user.id_user,
            PriceAlert.is_active == 1
        ).order_by(PriceAlert.created_at.desc()).offset(skip).limit(limit).all()
        
        total = db.query(PriceAlert).filter(
            PriceAlert.user_id == current_user.id_user,
            PriceAlert.is_active == 1
        ).count()
        
        alerts_response = []
        for alert in alerts:
            product = db.query(Product).options(
                joinedload(Product.listings).joinedload(Listing.prices),
                joinedload(Product.listings).joinedload(Listing.shop)
            ).filter(Product.id_product == alert.product_id).first()
            
            if product:
                latest_prices = []
                shop_prices = {}
                for listing in product.listings:
                    if listing.prices:
                        latest_price = max(listing.prices, key=lambda x: x.scraped_at)
                        if listing.shop_id not in shop_prices:
                            latest_prices.append(schemas.PriceResponse(
                                price=float(latest_price.price),
                                scraped_at=latest_price.scraped_at,
                                shop_name=listing.shop.name,
                                shop_id=listing.shop_id,
                                url=listing.url
                            ))
                            shop_prices[listing.shop_id] = latest_price
                
                prices_values = [p.price for p in latest_prices]
                min_price = min(prices_values) if prices_values else None
                max_price = max(prices_values) if prices_values else None
                
                product_with_prices = schemas.ProductWithPrices(
                    product=schemas.ProductResponse.model_validate(product),
                    prices=latest_prices,
                    min_price=min_price,
                    max_price=max_price
                )
                
                alerts_response.append(schemas.PriceAlertResponse(
                    id_alert=alert.id_alert,
                    product=product_with_prices,
                    target_price=float(alert.target_price),
                    is_active=bool(alert.is_active),
                    created_at=alert.created_at
                ))
        
        return schemas.PriceAlertsListResponse(alerts=alerts_response, total=total)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении отслеживаний: {str(e)}"
        )


@app.delete("/user/price-alerts/{alert_id}")
def delete_price_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удалить отслеживание цены"""
    try:
        alert = db.query(PriceAlert).filter(
            PriceAlert.id_alert == alert_id,
            PriceAlert.user_id == current_user.id_user
        ).first()
        
        if not alert:
            raise HTTPException(status_code=404, detail="Отслеживание не найдено")
        
        alert.is_active = 0
        db.commit()
        return {"message": "Отслеживание удалено"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении отслеживания: {str(e)}"
        )


# ==================== СТАТИСТИКА ====================

@app.get("/user/stats", response_model=schemas.UserStatsResponse)
def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить статистику пользователя"""
    try:
        viewed_count = db.query(ViewHistory).filter(
            ViewHistory.user_id == current_user.id_user
        ).count()
        
        favorites_count = db.query(Favorite).filter(
            Favorite.user_id == current_user.id_user
        ).count()
        
        alerts_count = db.query(PriceAlert).filter(
            PriceAlert.user_id == current_user.id_user,
            PriceAlert.is_active == 1
        ).count()
        
        shopping_lists_count = db.query(ShoppingList).filter(
            ShoppingList.user_id == current_user.id_user
        ).count()
        
        comparisons_count = db.query(Comparison).filter(
            Comparison.user_id == current_user.id_user
        ).count()
        
        reviews_count = db.query(Review).filter(
            Review.user_id == current_user.id_user
        ).count()
        
        return schemas.UserStatsResponse(
            viewed_count=viewed_count,
            favorites_count=favorites_count,
            alerts_count=alerts_count,
            shopping_lists_count=shopping_lists_count,
            comparisons_count=comparisons_count,
            reviews_count=reviews_count
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении статистики: {str(e)}"
        )


# ==================== УПРАВЛЕНИЕ КЭШЕМ ====================


@app.delete("/cache/clear-all")
def clear_all_cache():
    """
    Полная очистка всего кэша приложения
    
    Очищает:
    - Redis кэш (все ключи)
    - Кэш товаров
    - Кэш URL
    """
    try:
        import redis
        
        # Подключение к Redis
        redis_client = None
        if external_data_service.redis_enabled:
            redis_client = external_data_service.redis_client
        
        if not redis_client:
            return {
                "message": "Redis не доступен",
                "cleared_keys": 0
            }
        
        # Подсчет ключей перед очисткой
        all_keys = redis_client.keys("*")
        keys_count = len(all_keys)
        
        # Очистка всех ключей
        if all_keys:
            deleted = 0
            for key in all_keys:
                try:
                    redis_client.delete(key)
                    deleted += 1
                except Exception as e:
                    logging.error(f"Ошибка при удалении ключа {key}: {e}")
            
            logging.info(f"✅ Полная очистка кэша: удалено {deleted} ключей")
            return {
                "message": "Весь кэш очищен",
                "cleared_keys": deleted,
                "total_keys_before": keys_count
            }
        else:
            return {
                "message": "Кэш уже пуст",
                "cleared_keys": 0,
                "total_keys_before": 0
            }
            
    except Exception as e:
        logging.error(f"Ошибка при полной очистке кэша: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при очистке кэша: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)