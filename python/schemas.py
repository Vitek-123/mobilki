from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# Существующие схемы для пользователя
class UserBase(BaseModel):
    login: str
    email: str


class CreateUser(UserBase):
    password: str


class UserResponse(UserBase):
    id_user: int

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    login: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class TokenData(BaseModel):
    username: Optional[str] = None


# Новые схемы для продуктов
class ProductBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None  # Added field
    brand: Optional[str] = None
    model: Optional[str] = None
    image: Optional[str] = None


class ProductResponse(ProductBase):
    id_product: int

    class Config:
        from_attributes = True


class ShopBase(BaseModel):
    name: str


class ShopResponse(ShopBase):
    id_shop: int

    class Config:
        from_attributes = True


class PriceResponse(BaseModel):
    price: float
    scraped_at: datetime
    shop_name: str
    shop_id: int
    url: Optional[str] = None

    class Config:
        from_attributes = True


class ProductWithPrices(BaseModel):
    product: ProductResponse
    prices: List[PriceResponse]
    min_price: Optional[float] = None
    max_price: Optional[float] = None


class ProductsResponse(BaseModel):
    products: List[ProductWithPrices]
    total: int