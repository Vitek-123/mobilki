"""
Репозиторий для работы с товарами в БД
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from models import Product


class ProductRepository:
    """Репозиторий для работы с товарами"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, product_id: int) -> Optional[Product]:
        """Получение товара по ID"""
        return self.db.query(Product).filter(Product.id_product == product_id).first()
    
    def search(self, search_term: str, limit: int = 100) -> List[Product]:
        """Поиск товаров по названию"""
        search_pattern = f"%{search_term.lower()}%"
        return self.db.query(Product).filter(
            Product.title.ilike(search_pattern)
        ).limit(limit).all()
    
    def get_all(self, skip: int = 0, limit: int = 50) -> List[Product]:
        """Получение всех товаров с пагинацией"""
        return self.db.query(Product).offset(skip).limit(limit).all()
    
    def count(self, search_term: Optional[str] = None) -> int:
        """Подсчет количества товаров"""
        query = self.db.query(Product)
        if search_term:
            search_pattern = f"%{search_term.lower()}%"
            query = query.filter(Product.title.ilike(search_pattern))
        return query.count()

