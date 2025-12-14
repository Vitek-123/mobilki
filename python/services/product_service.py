"""
Сервис для работы с товарами
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
import logging

from models import Product, Listing, Price, Shop
from schemas import ProductWithPrices, ProductResponse, PriceResponse
from services.price_service import PriceService

logger = logging.getLogger(__name__)


class ProductService:
    """Сервис для работы с товарами"""
    
    def __init__(self, db: Session):
        self.db = db
        self.price_service = PriceService(db)
    
    def get_product_with_prices(
        self,
        product: Product,
        include_url: bool = True
    ) -> ProductWithPrices:
        """
        Получение товара с ценами
        
        Args:
            product: Объект товара из БД
            include_url: Включать ли URL в ответ
        
        Returns:
            Товар с ценами
        """
        # Получаем listings с ценами
        listings = self.db.query(Listing).filter(
            Listing.product_id == product.id_product
        ).options(
            joinedload(Listing.prices),
            joinedload(Listing.shop)
        ).all()
        
        # Формируем цены
        price_responses = []
        prices_values = []
        
        for listing in listings:
            latest_price = self.price_service.get_latest_price(listing.id_listing)
            
            if latest_price and listing.shop:
                price_responses.append(PriceResponse(
                    price=float(latest_price.price),
                    scraped_at=latest_price.scraped_at,
                    shop_name=listing.shop.name,
                    shop_id=listing.shop.id_shop,
                    url=listing.url if include_url else None
                ))
                prices_values.append(float(latest_price.price))
        
        # Если нет цен, но есть price в products
        if not price_responses and product.price:
            # Создаем фиктивную цену для отображения
            shop_name = self._get_default_shop_name(listings)
            price_responses.append(PriceResponse(
                price=float(product.price),
                scraped_at=datetime.now(),
                shop_name=shop_name,
                shop_id=0,
                url=listings[0].url if listings and include_url else None
            ))
            prices_values.append(float(product.price))
        
        # Формируем ответ
        product_response = ProductResponse(
            id_product=product.id_product,
            title=product.title,
            image=product.image,
            price=float(product.price) if product.price else (
                min(prices_values) if prices_values else None
            )
        )
        
        min_price = min(prices_values) if prices_values else None
        max_price = max(prices_values) if prices_values else None
        
        return ProductWithPrices(
            product=product_response,
            prices=price_responses,
            min_price=min_price,
            max_price=max_price
        )
    
    def get_products_from_db(
        self,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[Dict], int]:
        """
        Получение товаров из БД
        
        Args:
            search: Поисковый запрос
            skip: Пропустить записей
            limit: Лимит записей
        
        Returns:
            Кортеж (список товаров, общее количество)
        """
        query = self.db.query(Product)
        
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(Product.title.ilike(search_term))
        
        total = query.count()
        products = query.offset(skip).limit(limit).all()
        
        # Преобразуем в формат для merger
        db_products = []
        for product in products:
            product_with_prices = self.get_product_with_prices(product)
            
            db_products.append({
                "id_product": product.id_product,
                "title": product.title,
                "brand": None,  # Поле удалено из БД
                "model": None,  # Поле удалено из БД
                "description": None,  # Поле удалено из БД
                "image": product.image,
                "price": product_with_prices.product.price,
                "prices": [
                    {
                        "price": p.price,
                        "shop_name": p.shop_name,
                        "url": p.url,
                        "scraped_at": p.scraped_at.isoformat()
                    }
                    for p in product_with_prices.prices
                ],
                "min_price": product_with_prices.min_price,
                "max_price": product_with_prices.max_price
            })
        
        return db_products, total
    
    def _get_default_shop_name(self, listings: List[Listing]) -> str:
        """Получение названия магазина по умолчанию"""
        if listings and listings[0].shop:
            return listings[0].shop.name
        
        # Ищем первый доступный магазин в БД
        first_shop = self.db.query(Shop).first()
        return first_shop.name if first_shop else "Магазин"

