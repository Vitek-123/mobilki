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
    image: Optional[str] = None
    price: Optional[float] = None


class ProductResponse(ProductBase):
    id_product: int
    brand: Optional[str] = None
    model: Optional[str] = None
    url: Optional[str] = None  # URL товара (для товаров из внешних источников)

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


# Схемы для истории просмотров
class ViewHistoryResponse(BaseModel):
    id_view: int
    product: ProductWithPrices
    viewed_at: datetime

    class Config:
        from_attributes = True


class ViewHistoryListResponse(BaseModel):
    views: List[ViewHistoryResponse]
    total: int


# Схемы для избранного
class FavoriteResponse(BaseModel):
    id_favorite: int
    product: ProductWithPrices
    added_at: datetime

    class Config:
        from_attributes = True


class FavoritesListResponse(BaseModel):
    favorites: List[FavoriteResponse]
    total: int


# Схемы для отслеживания цен
class PriceAlertCreate(BaseModel):
    product_id: int
    target_price: float


class PriceAlertResponse(BaseModel):
    id_alert: int
    product: ProductWithPrices
    target_price: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PriceAlertsListResponse(BaseModel):
    alerts: List[PriceAlertResponse]
    total: int


# Схемы для списков покупок
class ShoppingListCreate(BaseModel):
    name: str
    budget: Optional[float] = None


class ShoppingListItemResponse(BaseModel):
    id_item: int
    product: ProductResponse
    quantity: int
    is_purchased: bool
    added_at: datetime

    class Config:
        from_attributes = True


class ShoppingListResponse(BaseModel):
    id_list: int
    name: str
    budget: Optional[float] = None
    items: List[ShoppingListItemResponse]
    created_at: datetime

    class Config:
        from_attributes = True


class ShoppingListsListResponse(BaseModel):
    lists: List[ShoppingListResponse]
    total: int


# Схемы для сравнения товаров
class ComparisonCreate(BaseModel):
    name: Optional[str] = None
    product_ids: List[int]


class ComparisonResponse(BaseModel):
    id_comparison: int
    name: Optional[str] = None
    products: List[ProductWithPrices]
    created_at: datetime

    class Config:
        from_attributes = True


class ComparisonsListResponse(BaseModel):
    comparisons: List[ComparisonResponse]
    total: int


# Схемы для отзывов
class ReviewCreate(BaseModel):
    product_id: int
    rating: int  # 1-5
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    id_review: int
    user: UserResponse
    product: ProductResponse
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReviewsListResponse(BaseModel):
    reviews: List[ReviewResponse]
    total: int


# Схемы для реферальной программы
class ReferralResponse(BaseModel):
    id_referral: int
    referral_code: str
    referred_count: int
    bonus_earned: float

    class Config:
        from_attributes = True


# Схемы для подписки
class SubscriptionResponse(BaseModel):
    is_premium: bool
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Схемы для статистики
class UserStatsResponse(BaseModel):
    viewed_count: int
    favorites_count: int
    alerts_count: int
    shopping_lists_count: int
    comparisons_count: int
    reviews_count: int