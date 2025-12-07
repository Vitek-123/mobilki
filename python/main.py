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
    Review, Referral, Subscription
)
import schemas
from database import *

# Импорт сервиса внешних данных
from external_data_service import ExternalDataService

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

app = FastAPI(title="Mobil Api", version="0.9.3")

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

# Получаем разрешенные origins из переменных окружения
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000")
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
):
    """
    Поиск товаров во внешних источниках
    Если search не указан, возвращает пустой результат
    """
    try:
        if not search:
            return schemas.ProductsResponse(products=[], total=0)
        
        logging.info(f"Поиск товаров по запросу '{search}'")
        
        # Получаем данные из внешних источников
        aggregated_products = external_data_service.aggregate_by_product(
            query=search,
            use_cache=use_cache
        )
        
        # Применяем пагинацию
        total = len(aggregated_products)
        paginated_products = aggregated_products[skip:skip + limit]
        
        # Преобразование в формат API
        products_with_prices = []
        for item in paginated_products:
            # Генерируем ID на основе хеша бренда и модели
            product_id = abs(hash(f"{item['brand']}_{item['model']}")) % 1000000
            
            product_response = schemas.ProductResponse(
                id_product=product_id,
                title=item['title'],
                brand=item['brand'],
                model=item['model'],
                image=item.get('image'),
                description=item.get('description')
            )
            
            # Преобразование цен
            price_responses = []
            for price_data in item['prices']:
                price_response = schemas.PriceResponse(
                    price=price_data['price'],
                    scraped_at=datetime.fromisoformat(price_data['scraped_at']),
                    shop_name=price_data['shop_name'],
                    shop_id=abs(hash(price_data['shop_name'])) % 10000,  # Временный ID магазина
                    url=price_data['url']
                )
                price_responses.append(price_response)
            
            product_with_prices = schemas.ProductWithPrices(
                product=product_response,
                prices=price_responses,
                min_price=item.get('min_price'),
                max_price=item.get('max_price')
            )
            products_with_prices.append(product_with_prices)
        
        return schemas.ProductsResponse(
            products=products_with_prices,
            total=total
        )
    except Exception as e:
        logging.error(f"Ошибка при получении продуктов: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении продуктов: {str(e)}"
        )


@app.get("/products/popular-phones", response_model=schemas.ProductsResponse)
def get_popular_phones(
    limit: int = Query(3, ge=1, le=10, description="Количество популярных телефонов"),
    use_cache: bool = Query(True, description="Использовать кэш")
):
    """
    Получение топ популярных телефонов
    Возвращает 3 самых популярных телефона по умолчанию (mock данные)
    """
    try:
        logging.info(f"Запрос популярных телефонов: limit={limit}, use_cache={use_cache}")
        # Получаем популярные телефоны (mock данные)
        phones = external_data_service.get_popular_phones(
            limit=limit, 
            use_cache=use_cache
        )
        logging.info(f"Получено {len(phones)} телефонов из сервиса")
        
        # Преобразование в формат API
        products_with_prices = []
        for item in phones:
            # Генерируем ID на основе хеша бренда и модели
            product_id = abs(hash(f"{item['brand']}_{item['model']}")) % 1000000
            
            product_response = schemas.ProductResponse(
                id_product=product_id,
                title=item['title'],
                brand=item['brand'],
                model=item['model'],
                image=item.get('image'),
                description=item.get('description')
            )
            
            # Преобразование цен
            price_responses = []
            for price_data in item['prices']:
                price_response = schemas.PriceResponse(
                    price=price_data['price'],
                    scraped_at=datetime.fromisoformat(price_data['scraped_at']),
                    shop_name=price_data['shop_name'],
                    shop_id=abs(hash(price_data['shop_name'])) % 10000,
                    url=price_data['url']
                )
                price_responses.append(price_response)
            
            product_with_prices = schemas.ProductWithPrices(
                product=product_response,
                prices=price_responses,
                min_price=item.get('min_price'),
                max_price=item.get('max_price')
            )
            products_with_prices.append(product_with_prices)
        
        logging.info(f"Возвращаем {len(products_with_prices)} товаров клиенту")
        return schemas.ProductsResponse(
            products=products_with_prices,
            total=len(products_with_prices)
        )
    except Exception as e:
        logging.error(f"Ошибка при получении популярных телефонов: {e}", exc_info=True)
        # Возвращаем пустой список вместо ошибки, чтобы приложение не падало
        return schemas.ProductsResponse(
            products=[],
            total=0
        )


@app.get("/products/{brand}/{model}", response_model=schemas.ProductWithPrices)
def get_product(
    brand: str,
    model: str,
    use_cache: bool = Query(True, description="Использовать кэш")
):
    """
    Получение цен на конкретный товар по бренду и модели
    """
    try:
        # Получаем цены из внешних источников
        prices = external_data_service.get_product_prices(
            brand=brand,
            model=model,
            use_cache=use_cache
        )
        
        if not prices:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Товар {brand} {model} не найден"
            )
        
        # Группировка по магазинам (берем минимальную цену для каждого магазина)
        shop_prices = {}
        for price_data in prices:
            shop_name = price_data['shop_name']
            if shop_name not in shop_prices or price_data['price'] < shop_prices[shop_name]['price']:
                shop_prices[shop_name] = price_data
        
        # Создание объекта продукта
        product_response = schemas.ProductResponse(
            id_product=abs(hash(f"{brand}_{model}")) % 1000000,
            title=f"{brand} {model}",
            brand=brand,
            model=model,
            image=None,
            description=None
        )
        
        # Преобразование цен
        price_responses = []
        for shop_name, price_data in shop_prices.items():
            price_response = schemas.PriceResponse(
                price=price_data['price'],
                scraped_at=datetime.fromisoformat(price_data['scraped_at']),
                shop_name=shop_name,
                shop_id=abs(hash(shop_name)) % 10000,
                url=price_data['url']
            )
            price_responses.append(price_response)
        
        prices_values = [p.price for p in price_responses]
        min_price = min(prices_values) if prices_values else None
        max_price = max(prices_values) if prices_values else None
        
        return schemas.ProductWithPrices(
            product=product_response,
            prices=price_responses,
            min_price=min_price,
            max_price=max_price
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Ошибка при получении продукта: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении продукта: {str(e)}"
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


@app.get("/external/cache/stats")
def get_cache_stats():
    """Получение статистики кэша"""
    try:
        stats = external_data_service.get_cache_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении статистики: {str(e)}"
        )


@app.delete("/external/cache/clear")
def clear_cache(
    pattern: str = Query("*", description="Паттерн для очистки кэша")
):
    """Очистка кэша"""
    try:
        external_data_service.clear_cache(pattern=pattern)
        return {"message": f"Кэш очищен (паттерн: {pattern})"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при очистке кэша: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)