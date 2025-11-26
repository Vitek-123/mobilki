from sqlalchemy import Column, Integer, String, Text, DECIMAL, TIMESTAMP, ForeignKey
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
    description = Column(Text)
    brand = Column(String(255))
    model = Column(String(255))
    image = Column(String(500))

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
    scraped_at = Column(TIMESTAMP, server_default='CURRENT_TIMESTAMP')

    listing = relationship("Listing", back_populates="prices")