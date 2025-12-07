"""
Сервис для работы с внешними источниками данных с кэшированием
"""
import redis
import json
import logging
import os
from typing import List, Dict, Optional
from datetime import datetime

from data_providers import ProductData

logger = logging.getLogger(__name__)


class ExternalDataService:
    """Сервис для работы с внешними источниками данных (использует только mock данные)"""
    
    def __init__(
        self,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        cache_ttl: int = 10800,  # 3 часа по умолчанию
        redis_enabled: bool = True
    ):
        """
        Инициализация сервиса
        
        Args:
            redis_host: Хост Redis
            redis_port: Порт Redis
            redis_db: Номер БД Redis
            cache_ttl: Время жизни кэша в секундах (по умолчанию 3 часа = 10800 сек)
            redis_enabled: Включить ли Redis (по умолчанию True)
        """
        # Инициализация Redis
        self.redis_enabled = False
        self.redis_client = None
        
        if redis_enabled:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                self.redis_client.ping()
                logger.info("Подключение к Redis установлено")
                self.redis_enabled = True
            except Exception as e:
                logger.info(f"Redis недоступен ({redis_host}:{redis_port}). Кэширование отключено. Приложение работает без кэша.")
                self.redis_client = None
                self.redis_enabled = False
        else:
            logger.info("Redis отключен. Кэширование не используется.")
        
        self.cache_ttl = cache_ttl
        
        # Инициализация провайдеров
        self.providers = {}
        
        # Пробуем использовать Яндекс.Маркет парсер (Selenium)
        use_selenium = os.getenv("USE_SELENIUM", "auto").lower()
        if use_selenium == "auto":
            try:
                import selenium
                use_selenium = "true"
                logger.info("Selenium обнаружен, будет использован для Яндекс.Маркет")
            except ImportError:
                use_selenium = "false"
                logger.info("Selenium не установлен, Яндекс.Маркет недоступен")
        
        use_selenium = use_selenium in ("true", "1", "yes")
        
        if use_selenium:
            try:
                from yandex_market_selenium import YandexMarketSeleniumParser
                self.providers["yandex_market"] = YandexMarketSeleniumParser(headless=True)
                logger.info("✅ Яндекс.Маркет парсер инициализирован (Selenium)")
            except Exception as e:
                logger.warning(f"Не удалось создать Яндекс.Маркет парсер: {e}")
                self.providers["yandex_market"] = None
    
    def search_products(
        self,
        query: str,
        use_cache: bool = True,
        shops: Optional[List[str]] = None
    ) -> Dict[str, List[ProductData]]:
        """
        Поиск товаров в Яндекс.Маркет
        
        Args:
            query: Поисковый запрос
            use_cache: Использовать ли кэш
            shops: Список магазинов (игнорируется, используется Яндекс.Маркет)
        
        Returns:
            Словарь {название_магазина: список_товаров}
        """
        cache_key = f"search:{query.lower().strip()}"
        
        # Проверка кэша
        if use_cache and self.redis_enabled:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    logger.info(f"Данные найдены в кэше для запроса: {query}")
                    return self._deserialize_products(json.loads(cached_data))
            except Exception as e:
                logger.error(f"Ошибка чтения из кэша: {e}")
        
        results = {}
        
        # Используем Яндекс.Маркет
        yandex_provider = self.providers.get("yandex_market")
        if yandex_provider:
            try:
                products = yandex_provider.search_products(query, limit=50)
                if products:
                    results["yandex_market"] = products
                    logger.info(f"Найдено {len(products)} товаров в Яндекс.Маркет")
            except Exception as e:
                logger.error(f"Ошибка поиска в Яндекс.Маркет: {e}", exc_info=True)
                results["yandex_market"] = []
        else:
            logger.warning("Яндекс.Маркет парсер недоступен (Selenium не установлен)")
            results["yandex_market"] = []
        
        # Сохранение в кэш
        if self.redis_enabled and results:
            try:
                serialized = self._serialize_products(results)
                self.redis_client.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(serialized, default=str)
                )
                logger.info(f"Данные сохранены в кэш для запроса: {query}")
            except Exception as e:
                logger.error(f"Ошибка записи в кэш: {e}")
        
        return results
    
    def aggregate_by_product(
        self,
        query: str,
        use_cache: bool = True,
        shops: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Агрегация товаров по названию (группировка одинаковых товаров)
        
        Args:
            query: Поисковый запрос
            use_cache: Использовать ли кэш
            shops: Список магазинов (игнорируется)
        
        Returns:
            Список агрегированных товаров с ценами
        """
        all_results = self.search_products(query, use_cache=use_cache, shops=shops)
        
        # Группировка товаров по бренду и модели
        product_groups = {}
        
        for shop_name, products in all_results.items():
            for product in products:
                # Используем комбинацию бренда и модели как ключ
                key = f"{product.brand.lower()}_{product.model.lower()}".strip('_')
                
                if not key or key == '_':
                    # Если не удалось извлечь бренд/модель, используем название
                    key = product.title.lower()[:50]
                
                if key not in product_groups:
                    product_groups[key] = {
                        "title": product.title,
                        "brand": product.brand,
                        "model": product.model,
                        "image": product.image,
                        "description": product.description,
                        "prices": []
                    }
                
                # Добавляем цену, если её еще нет от этого магазина
                shop_exists = any(
                    p["shop_name"] == product.shop_name
                    for p in product_groups[key]["prices"]
                )
                
                if not shop_exists:
                    product_groups[key]["prices"].append({
                        "shop_name": product.shop_name,
                        "price": product.price,
                        "url": product.url,
                        "scraped_at": product.scraped_at.isoformat() if product.scraped_at else datetime.utcnow().isoformat()
                    })
        
        # Преобразование в список и сортировка по минимальной цене
        aggregated = []
        for key, data in product_groups.items():
            prices = data["prices"]
            if prices:
                price_values = [p["price"] for p in prices]
                aggregated.append({
                    "title": data["title"],
                    "brand": data["brand"],
                    "model": data["model"],
                    "image": data.get("image"),
                    "description": data.get("description"),
                    "prices": prices,
                    "min_price": min(price_values),
                    "max_price": max(price_values),
                    "shops_count": len(prices)
                })
        
        # Сортировка по минимальной цене
        aggregated.sort(key=lambda x: x["min_price"])
        
        return aggregated
    
    def get_popular_phones(
        self,
        limit: int = 3,
        use_cache: bool = True,
        fallback_to_other_shops: bool = True
    ) -> List[Dict]:
        """
        Получение популярных телефонов из Яндекс.Маркет
        
        Args:
            limit: Количество телефонов (по умолчанию 3)
            use_cache: Использовать ли кэш
            fallback_to_other_shops: Игнорируется
        
        Returns:
            Список популярных телефонов с ценами
        """
        cache_key = f"popular_phones:{limit}"
        
        # Проверка кэша
        if use_cache and self.redis_enabled:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    logger.info("Популярные телефоны найдены в кэше")
                    return json.loads(cached_data)
            except Exception as e:
                logger.error(f"Ошибка чтения из кэша: {e}")
        
        # Пробуем получить из Яндекс.Маркет
        phones = []
        yandex_provider = self.providers.get("yandex_market")
        
        if yandex_provider:
            try:
                phones = yandex_provider.get_popular_phones(limit=limit)
                logger.info(f"Получено {len(phones)} телефонов из Яндекс.Маркет")
            except Exception as e:
                logger.warning(f"Ошибка получения телефонов из Яндекс.Маркет: {e}")
                phones = []
        
        # Если не получилось, используем mock данные
        if not phones:
            logger.warning("Не удалось получить телефоны из Яндекс.Маркет, используем mock данные")
            phones = self._get_mock_phones(limit=limit)
        
        # Преобразуем в формат для API
        result = []
        for phone in phones:
            result.append({
                "title": phone.title,
                "brand": phone.brand,
                "model": phone.model,
                "image": phone.image,
                "description": phone.description,
                "prices": [{
                    "shop_name": phone.shop_name,
                    "price": phone.price,
                    "url": phone.url,
                    "scraped_at": datetime.utcnow().isoformat()
                }],
                "min_price": phone.price,
                "max_price": phone.price,
                "shops_count": 1
            })
        
        logger.info(f"Сформировано {len(result)} товаров для ответа (mock данные)")
        
        # Сохранение в кэш
        if self.redis_enabled and result:
            try:
                self.redis_client.setex(
                    cache_key,
                    min(self.cache_ttl, 3600),  # Максимум 1 час для популярных товаров
                    json.dumps(result, default=str)
                )
                logger.info(f"Популярные телефоны сохранены в кэш")
            except Exception as e:
                logger.error(f"Ошибка записи в кэш: {e}")
        
        return result
    
    def _get_mock_phones(self, limit: int = 3) -> List[ProductData]:
        """Возвращает тестовые данные популярных телефонов для демонстрации (fallback)"""
        mock_phones = [
            ProductData(
                title="Смартфон Apple iPhone 15 128GB",
                brand="Apple",
                model="iPhone 15",
                price=79990.0,
                shop_name="Mock Shop",
                url="https://example.com/iphone15",
                image="https://via.placeholder.com/400x400/000000/FFFFFF?text=iPhone+15",
                description="Смартфон Apple iPhone 15 с дисплеем 6.1 дюйма, процессором A16 Bionic и камерой 48 МП",
                product_id="mock_iphone15"
            ),
            ProductData(
                title="Смартфон Samsung Galaxy S23 256GB",
                brand="Samsung",
                model="Galaxy S23",
                price=69990.0,
                shop_name="Mock Shop",
                url="https://example.com/galaxy-s23",
                image="https://via.placeholder.com/400x400/1428A0/FFFFFF?text=Galaxy+S23",
                description="Смартфон Samsung Galaxy S23 с камерой 50 МП, процессором Snapdragon 8 Gen 2",
                product_id="mock_samsung_s23"
            ),
            ProductData(
                title="Смартфон Xiaomi 13 256GB",
                brand="Xiaomi",
                model="13",
                price=49990.0,
                shop_name="Mock Shop",
                url="https://example.com/xiaomi13",
                image="https://via.placeholder.com/400x400/FF6900/FFFFFF?text=Xiaomi+13",
                description="Смартфон Xiaomi 13 с процессором Snapdragon 8 Gen 2, камерой Leica 50 МП",
                product_id="mock_xiaomi13"
            ),
        ]
        return mock_phones[:limit]
    
    def _serialize_products(self, results: Dict[str, List[ProductData]]) -> Dict:
        """Сериализация продуктов для кэша"""
        serialized = {}
        for shop_name, products in results.items():
            serialized[shop_name] = [
                {
                    "title": p.title,
                    "brand": p.brand,
                    "model": p.model,
                    "price": p.price,
                    "shop_name": p.shop_name,
                    "url": p.url,
                    "image": p.image,
                    "description": p.description,
                    "scraped_at": p.scraped_at.isoformat() if p.scraped_at else None,
                    "product_id": p.product_id
                }
                for p in products
            ]
        return serialized
    
    def _deserialize_products(self, data: Dict) -> Dict[str, List[ProductData]]:
        """Десериализация продуктов из кэша"""
        results = {}
        for shop_name, products_data in data.items():
            results[shop_name] = [
                ProductData(
                    title=p["title"],
                    brand=p["brand"],
                    model=p["model"],
                    price=p["price"],
                    shop_name=p["shop_name"],
                    url=p["url"],
                    image=p.get("image"),
                    description=p.get("description"),
                    scraped_at=datetime.fromisoformat(p["scraped_at"]) if p.get("scraped_at") else None,
                    product_id=p.get("product_id")
                )
                for p in products_data
            ]
        return results
    
    def get_product_prices(
        self,
        brand: str,
        model: str,
        use_cache: bool = True
    ) -> List[Dict]:
        """
        Получение цен на конкретный товар
        
        Args:
            brand: Бренд товара
            model: Модель товара
            use_cache: Использовать ли кэш
        
        Returns:
            Список цен из разных магазинов
        """
        query = f"{brand} {model}"
        cache_key = f"product:{brand.lower()}:{model.lower()}"
        
        # Проверка кэша
        if use_cache and self.redis_enabled:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    logger.info(f"Цены найдены в кэше для {brand} {model}")
                    return json.loads(cached_data)
            except Exception as e:
                logger.error(f"Ошибка чтения из кэша: {e}")
        
        # Поиск товара
        results = self.search_products(query, use_cache=False)
        
        # Фильтрация и агрегация цен
        prices = []
        for shop_name, products in results.items():
            for product in products:
                # Проверяем соответствие бренда и модели
                if (brand.lower() in product.brand.lower() and
                    model.lower() in product.model.lower()):
                    prices.append({
                        "shop_name": product.shop_name,
                        "price": product.price,
                        "url": product.url,
                        "scraped_at": product.scraped_at.isoformat() if product.scraped_at else datetime.utcnow().isoformat()
                    })
        
        # Сохранение в кэш
        if self.redis_enabled and prices:
            try:
                self.redis_client.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(prices, default=str)
                )
            except Exception as e:
                logger.error(f"Ошибка записи в кэш: {e}")
        
        return prices
    
    def clear_cache(self, pattern: str = "*"):
        """Очистка кэша"""
        if not self.redis_enabled:
            return
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Очищено {len(keys)} ключей из кэша")
        except Exception as e:
            logger.error(f"Ошибка очистки кэша: {e}")
    
    def get_cache_stats(self) -> Dict:
        """Получение статистики кэша"""
        if not self.redis_enabled:
            return {"status": "disabled"}
        
        try:
            info = self.redis_client.info()
            return {
                "status": "enabled",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики кэша: {e}")
            return {"status": "error", "error": str(e)}
