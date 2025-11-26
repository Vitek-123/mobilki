from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from sqlalchemy import func
import uvicorn
from typing import List, Optional
from passlib.context import CryptContext

import models
from models import User, Product, Shop, Listing, Price
import schemas
from database import *

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mobil Api", version="0.1.0")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# Разрешаем CORS (важно для мобильного приложения)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Существующие эндпоинты для пользователя
@app.post("/add_user", response_model=schemas.UserResponse)
def create_user(user: schemas.CreateUser, db: Session = Depends(get_db)):
    user_exists = db.query(User).filter((User.login == user.login) | (User.email == user.email)).first()

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

    new_user = User(
        login=user.login,
        password=get_password_hash(user.password),  # Пароль хеширован
        email=user.email
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login", response_model=schemas.UserResponse)
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

    return db_user


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
                product=schemas.ProductResponse.from_orm(product),
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
            product=schemas.ProductResponse.from_orm(product),
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