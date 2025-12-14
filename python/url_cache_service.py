"""
Сервис для кэширования URL товаров
Позволяет быстро находить URL товаров по бренду/модели или названию
"""
import redis
import json
import logging
import hashlib
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class URLCacheService:
    """Сервис для кэширования URL товаров"""
    
    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        cache_ttl: int = 604800  # 7 дней по умолчанию
    ):
        """
        Инициализация сервиса кэширования
        
        Args:
            redis_client: Клиент Redis (если None, создается новый)
            cache_ttl: Время жизни кэша в секундах (по умолчанию 7 дней)
        """
        self.redis_client = redis_client
        self.cache_ttl = cache_ttl
        
        if not self.redis_client:
            try:
                import os
                self.redis_client = redis.Redis(
                    host=os.getenv("REDIS_HOST", "localhost"),
                    port=int(os.getenv("REDIS_PORT", "6379")),
                    db=int(os.getenv("REDIS_DB", "0")),
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                self.redis_client.ping()
                logger.info("✅ URL Cache Service: Redis подключен")
            except Exception as e:
                logger.warning(f"URL Cache Service: Redis недоступен: {e}")
                self.redis_client = None
    
    def _generate_cache_key(self, brand: Optional[str] = None, model: Optional[str] = None, title: Optional[str] = None) -> str:
        """
        Генерация ключа кэша
        
        Args:
            brand: Бренд товара
            model: Модель товара
            title: Название товара
        
        Returns:
            Ключ для кэша
        """
        if brand and model:
            # Приоритет: бренд + модель (самый точный)
            key = f"url:{brand.lower().strip()}:{model.lower().strip()}"
        elif title:
            # Fallback: хеш названия
            title_hash = hashlib.md5(title.lower().strip().encode()).hexdigest()[:12]
            key = f"url:title:{title_hash}"
        else:
            return None
        
        return key
    
    def get_product_url(
        self,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        title: Optional[str] = None
    ) -> Optional[str]:
        """
        Получение URL товара из кэша
        
        Args:
            brand: Бренд товара
            model: Модель товара
            title: Название товара
        
        Returns:
            URL товара или None
        """
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(brand=brand, model=model, title=title)
            if not cache_key:
                return None
            
            cached_url = self.redis_client.get(cache_key)
            if cached_url:
                logger.debug(f"URL найден в кэше: {cache_key}")
                return cached_url
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка чтения URL из кэша: {e}")
            return None
    
    def save_product_url(
        self,
        url: str,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        title: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Сохранение URL товара в кэш
        
        Args:
            url: URL товара
            brand: Бренд товара
            model: Модель товара
            title: Название товара
            ttl: Время жизни в секундах (если None, используется self.cache_ttl)
        
        Returns:
            True если успешно сохранено, False иначе
        """
        if not self.redis_client:
            return False
        
        if not url or not url.strip():
            return False
        
        try:
            cache_key = self._generate_cache_key(brand=brand, model=model, title=title)
            if not cache_key:
                return False
            
            ttl_to_use = ttl if ttl is not None else self.cache_ttl
            
            self.redis_client.setex(cache_key, ttl_to_use, url.strip())
            logger.debug(f"URL сохранен в кэш: {cache_key} -> {url[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения URL в кэш: {e}")
            return False
    
    def build_search_url(
        self,
        query: str,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        partner_id: Optional[str] = None
    ) -> str:
        """
        Формирование URL поиска с фильтрами
        
        Args:
            query: Поисковый запрос
            brand: Бренд для фильтра (опционально)
            model: Модель для фильтра (опционально)
            partner_id: Партнерский ID (опционально)
        
        Returns:
            URL для поиска
        """
        from urllib.parse import quote
        
        base_url = ""
        params = []
        
        # Основной поисковый запрос
        if query:
            params.append(f"text={quote(query)}")
        
        # Фильтр по бренду (если есть)
        if brand and brand != "Не указан":
            params.append(f"vendor={quote(brand)}")
        
        # Партнерский ID (если есть)
        if partner_id:
            params.append(f"partner_id={partner_id}")
        
        # Сортировка по релевантности
        params.append("how=aprice")
        
        return f"{base_url}?{'&'.join(params)}"
    
    def get_or_build_url(
        self,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        title: Optional[str] = None,
        existing_url: Optional[str] = None,
        partner_id: Optional[str] = None
    ) -> str:
        """
        Получение URL товара с приоритетами:
        1. Существующий URL (если передан)
        2. URL из кэша
        3. Поиск
        
        Args:
            brand: Бренд товара
            model: Модель товара
            title: Название товара
            existing_url: Существующий URL (если есть)
            partner_id: Партнерский ID (для добавления к ссылкам)
        
        Returns:
            URL для открытия товара
        """
        # Приоритет 1: Используем существующий URL
        if existing_url and existing_url.strip():
            url = existing_url.strip()
            # Валидация URL
            if self._is_valid_url(url):
                # Добавляем партнерский ID если есть
                if partner_id:
                    url = self._add_partner_id(url, partner_id)
                return url
        
        # Приоритет 2: Пробуем получить из кэша
        cached_url = self.get_product_url(brand=brand, model=model, title=title)
        if cached_url and self._is_valid_url(cached_url):
            # Добавляем партнерский ID если есть
            if partner_id:
                cached_url = self._add_partner_id(cached_url, partner_id)
            return cached_url
        
        # Приоритет 3: Формируем поисковый URL
        search_query = self._build_search_query(brand=brand, model=model, title=title)
        return self.build_search_url(
            query=search_query,
            brand=brand,
            model=model,
            partner_id=partner_id
        )
    
    def _is_valid_url(self, url: str) -> bool:
        """Проверка валидности URL"""
        if not url or len(url) < 10:
            return False
        
        # Проверяем формат URL
        if not (url.startswith("http://") or url.startswith("https://")):
            return False
        
        # Проверяем на подозрительные пути
        suspicious_paths = ['/proc', '/error', '/404', '/common', '/Common', '/NotFound']
        if any(path in url for path in suspicious_paths):
            return False
        
        # Проверяем формат URL
        if url.startswith("http://") or url.startswith("https://"):
            return True
        
        return False
    
    def _add_partner_id(self, url: str, partner_id: str) -> str:
        """Добавление партнерского ID к URL"""
        if not partner_id:
            return url
        
        if "?" in url:
            return f"{url}&partner_id={partner_id}"
        else:
            return f"{url}?partner_id={partner_id}"
    
    def _build_search_query(
        self,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        title: Optional[str] = None
    ) -> str:
        """Построение поискового запроса с приоритетами"""
        # Приоритет 1: Бренд + Модель (самый точный)
        if brand and model and brand != "Не указан" and model != "Не указана":
            return f"{brand} {model}".strip()
        
        # Приоритет 2: Название товара
        if title:
            return title.strip()
        
        # Fallback
        return ""
