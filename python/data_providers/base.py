"""
Базовые классы для провайдеров данных
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import datetime
from dataclasses import dataclass


@dataclass
class ProductData:
    """Класс для представления данных о товаре из внешних источников"""
    title: str
    brand: str
    model: str
    price: float
    shop_name: str
    url: str
    image: Optional[str] = None
    description: Optional[str] = None
    scraped_at: Optional[datetime] = None
    product_id: Optional[str] = None  # ID товара в магазине
    
    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.utcnow()


class DataProvider(ABC):
    """Абстрактный базовый класс для провайдеров данных"""
    
    @abstractmethod
    def search_products(self, query: str, limit: int = 50) -> List[ProductData]:
        """
        Поиск товаров по запросу
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
        
        Returns:
            Список найденных товаров
        """
        pass
    
    @abstractmethod
    def get_product_by_id(self, product_id: str) -> Optional[ProductData]:
        """
        Получение товара по ID
        
        Args:
            product_id: ID товара в магазине
        
        Returns:
            Данные о товаре или None
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Название провайдера"""
        pass
