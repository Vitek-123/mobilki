"""
Сервис для работы с ценами
"""
from sqlalchemy.orm import Session
from models import Price
from typing import Optional


class PriceService:
    """Сервис для работы с ценами"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_latest_price(self, listing_id: int) -> Optional[Price]:
        """
        Получение последней цены для listing
        
        Args:
            listing_id: ID listing
        
        Returns:
            Последняя цена или None
        """
        return self.db.query(Price).filter(
            Price.listing_id == listing_id
        ).order_by(Price.scraped_at.desc()).first()
    
    def get_prices_for_listing(self, listing_id: int) -> list[Price]:
        """
        Получение всех цен для listing
        
        Args:
            listing_id: ID listing
        
        Returns:
            Список цен
        """
        return self.db.query(Price).filter(
            Price.listing_id == listing_id
        ).order_by(Price.scraped_at.desc()).all()

