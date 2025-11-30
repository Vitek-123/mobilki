from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from sqlalchemy import func
import uvicorn
from typing import List, Optional
from passlib.context import CryptContext
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

import models
from models import User, Product, Shop, Listing, Price
import schemas
from database import *

# Загружаем переменные окружения
load_dotenv()

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mobil Api", version="0.5.0")

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


# Новые эндпоинты для продуктов
@app.get("/products", response_model=schemas.ProductsResponse)
def get_products(
        skip: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=100),
        search: Optional[str] = None,
        db: Session = Depends(get_db)
):
    try:
        # Базовый запрос с eager loading
        query = db.query(Product).options(
            joinedload(Product.listings).joinedload(Listing.prices),
            joinedload(Product.listings).joinedload(Listing.shop)
        )

        # Поиск по названию, бренду или модели
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Product.title.ilike(search_term)) |
                (Product.brand.ilike(search_term)) |
                (Product.model.ilike(search_term))
            )

        # Получаем общее количество
        total = query.count()

        # Получаем продукты с пагинацией
        products = query.offset(skip).limit(limit).all()

        # Формируем ответ с ценами
        products_with_prices = []
        for product in products:
            # Получаем актуальные цены для продукта из eager loaded данных
            latest_prices = []
            shop_prices = {}

            for listing in product.listings:
                if listing.prices:
                    # Берем последнюю цену для каждого листинга
                    latest_price = max(listing.prices, key=lambda x: x.scraped_at)
                    if listing.shop_id not in shop_prices:
                        price_response = schemas.PriceResponse(
                            price=float(latest_price.price),
                            scraped_at=latest_price.scraped_at,
                            shop_name=listing.shop.name,
                            shop_id=listing.shop_id,
                            url=listing.url
                        )
                        latest_prices.append(price_response)
                        shop_prices[listing.shop_id] = price_response

            # Вычисляем мин и макс цены
            prices_values = [p.price for p in latest_prices]
            min_price = min(prices_values) if prices_values else None
            max_price = max(prices_values) if prices_values else None

            product_with_prices = schemas.ProductWithPrices(
                product=schemas.ProductResponse.model_validate(product),
                prices=latest_prices,
                min_price=min_price,
                max_price=max_price
            )
            products_with_prices.append(product_with_prices)

        return schemas.ProductsResponse(
            products=products_with_prices,
            total=total
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении продуктов: {str(e)}"
        )


@app.get("/products/{product_id}", response_model=schemas.ProductWithPrices)
def get_product(product_id: int, db: Session = Depends(get_db)):
    try:
        product = db.query(Product).options(
            joinedload(Product.listings).joinedload(Listing.prices),
            joinedload(Product.listings).joinedload(Listing.shop)
        ).filter(Product.id_product == product_id).first()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Получаем все цены для продукта из eager loaded данных
        latest_prices = []
        shop_prices = {}

        for listing in product.listings:
            if listing.prices:
                # Берем последнюю цену для каждого листинга
                latest_price = max(listing.prices, key=lambda x: x.scraped_at)
                if listing.shop_id not in shop_prices:
                    price_response = schemas.PriceResponse(
                        price=float(latest_price.price),
                        scraped_at=latest_price.scraped_at,
                        shop_name=listing.shop.name,
                        shop_id=listing.shop_id,
                        url=listing.url
                    )
                    latest_prices.append(price_response)
                    shop_prices[listing.shop_id] = price_response

        # Вычисляем мин и макс цены
        prices_values = [p.price for p in latest_prices]
        min_price = min(prices_values) if prices_values else None
        max_price = max(prices_values) if prices_values else None

        return schemas.ProductWithPrices(
            product=schemas.ProductResponse.model_validate(product),
            prices=latest_prices,
            min_price=min_price,
            max_price=max_price
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении продукта: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)