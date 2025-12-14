from sqlalchemy import Column, Integer, String, Text, DECIMAL, TIMESTAMP, ForeignKey, text
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "User"

    id_user = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String(255))
    password = Column(String(255))
    email = Column(String(255))


class Product(Base):
    __tablename__ = "products"

    id_product = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255))
    image = Column(String(500))
    price = Column(DECIMAL(12, 2), nullable=True)

    listings = relationship("Listing", back_populates="product", cascade="all, delete-orphan")


class Shop(Base):
    __tablename__ = "shops"

    id_shop = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))

    listings = relationship("Listing", back_populates="shop", cascade="all, delete-orphan")


class Listing(Base):
    __tablename__ = "listings"

    id_listing = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id_product', ondelete='CASCADE'))
    shop_id = Column(Integer, ForeignKey('shops.id_shop', ondelete='CASCADE'))
    url = Column(Text)

    product = relationship("Product", back_populates="listings")
    shop = relationship("Shop", back_populates="listings")
    prices = relationship("Price", back_populates="listing", cascade="all, delete-orphan")


class Price(Base):
    __tablename__ = "prices"

    id_price = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(Integer, ForeignKey('listings.id_listing', ondelete='CASCADE'))
    price = Column(DECIMAL(12, 2))
    scraped_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    listing = relationship("Listing", back_populates="prices")


# История просмотров
class ViewHistory(Base):
    __tablename__ = "view_history"

    id_view = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('User.id_user', ondelete='CASCADE'))
    product_id = Column(Integer, ForeignKey('products.id_product', ondelete='CASCADE'))
    viewed_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    user = relationship("User")
    product = relationship("Product")


# Избранное
class Favorite(Base):
    __tablename__ = "favorites"

    id_favorite = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('User.id_user', ondelete='CASCADE'))
    product_id = Column(Integer, ForeignKey('products.id_product', ondelete='CASCADE'))
    added_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    user = relationship("User")
    product = relationship("Product")


# Отслеживание цен
class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id_alert = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('User.id_user', ondelete='CASCADE'))
    product_id = Column(Integer, ForeignKey('products.id_product', ondelete='CASCADE'))
    target_price = Column(DECIMAL(12, 2))
    is_active = Column(Integer, default=1)  # 1 - активен, 0 - неактивен
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    user = relationship("User")
    product = relationship("Product")


# Списки покупок
class ShoppingList(Base):
    __tablename__ = "shopping_lists"

    id_list = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('User.id_user', ondelete='CASCADE'))
    name = Column(String(255))
    budget = Column(DECIMAL(12, 2), nullable=True)
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    user = relationship("User")
    items = relationship("ShoppingListItem", back_populates="shopping_list", cascade="all, delete-orphan")


# Элементы списка покупок
class ShoppingListItem(Base):
    __tablename__ = "shopping_list_items"

    id_item = Column(Integer, primary_key=True, autoincrement=True)
    list_id = Column(Integer, ForeignKey('shopping_lists.id_list', ondelete='CASCADE'))
    product_id = Column(Integer, ForeignKey('products.id_product', ondelete='CASCADE'))
    quantity = Column(Integer, default=1)
    is_purchased = Column(Integer, default=0)  # 0 - не куплен, 1 - куплен
    added_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    shopping_list = relationship("ShoppingList", back_populates="items")
    product = relationship("Product")


# Сравнение товаров
class Comparison(Base):
    __tablename__ = "comparisons"

    id_comparison = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('User.id_user', ondelete='CASCADE'))
    name = Column(String(255), nullable=True)  # Название сравнения (опционально)
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    user = relationship("User")
    products = relationship("ComparisonProduct", back_populates="comparison", cascade="all, delete-orphan")


# Товары в сравнении
class ComparisonProduct(Base):
    __tablename__ = "comparison_products"

    id_comparison_product = Column(Integer, primary_key=True, autoincrement=True)
    comparison_id = Column(Integer, ForeignKey('comparisons.id_comparison', ondelete='CASCADE'))
    product_id = Column(Integer, ForeignKey('products.id_product', ondelete='CASCADE'))
    added_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    comparison = relationship("Comparison", back_populates="products")
    product = relationship("Product")


# Отзывы
class Review(Base):
    __tablename__ = "reviews"

    id_review = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('User.id_user', ondelete='CASCADE'))
    product_id = Column(Integer, ForeignKey('products.id_product', ondelete='CASCADE'))
    rating = Column(Integer)  # 1-5
    comment = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(TIMESTAMP, nullable=True)

    user = relationship("User")
    product = relationship("Product")


# Реферальная программа
class Referral(Base):
    __tablename__ = "referrals"

    id_referral = Column(Integer, primary_key=True, autoincrement=True)
    referrer_id = Column(Integer, ForeignKey('User.id_user', ondelete='CASCADE'))  # Тот, кто пригласил
    referred_id = Column(Integer, ForeignKey('User.id_user', ondelete='CASCADE'))  # Тот, кого пригласили
    referral_code = Column(String(50), unique=True)
    bonus_earned = Column(DECIMAL(12, 2), default=0)
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    referrer = relationship("User", foreign_keys=[referrer_id])
    referred = relationship("User", foreign_keys=[referred_id])


# Подписка/Premium
class Subscription(Base):
    __tablename__ = "subscriptions"

    id_subscription = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('User.id_user', ondelete='CASCADE'), unique=True)
    is_premium = Column(Integer, default=0)  # 0 - Free, 1 - Premium
    started_at = Column(TIMESTAMP, nullable=True)
    expires_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))

    user = relationship("User")