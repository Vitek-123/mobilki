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
    """Сервис для работы с внешними источниками данных (магазины одежды)"""
    
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
        
        # Инициализация Яндекс.Маркет OAuth API
        self.yandex_api = None
        oauth_token = os.getenv("YANDEX_OAUTH_TOKEN")
        if oauth_token:
            try:
                from yandex_market_oauth_api import YandexMarketOAuthAPI
                campaign_id = os.getenv("YANDEX_MARKET_CAMPAIGN_ID")
                self.yandex_api = YandexMarketOAuthAPI(oauth_token=oauth_token, campaign_id=campaign_id)
                
                # Если campaign_id не указан, пробуем получить автоматически
                if not campaign_id:
                    campaigns = self.yandex_api.get_campaigns()
                    if campaigns:
                        campaign_id = str(campaigns[0].get("id", ""))
                        self.yandex_api.campaign_id = campaign_id
                        logger.info(f"Автоматически получен campaign_id: {campaign_id}")
                
                logger.info("✅ Яндекс.Маркет OAuth API инициализирован")
            except Exception as e:
                logger.warning(f"Не удалось инициализировать Яндекс.Маркет OAuth API: {e}")
        else:
            logger.info("YANDEX_OAUTH_TOKEN не найден в переменных окружения")
        
        # Инициализация парсера (всегда доступен как fallback)
        try:
            from yandex_market_parser import YandexMarketParser
            # Пробуем использовать Selenium если доступен
            use_selenium = os.getenv("USE_SELENIUM_FOR_PARSING", "false").lower() in ("true", "1", "yes")
            self.yandex_parser = YandexMarketParser(use_selenium=use_selenium)
            if use_selenium:
                logger.info("✅ Яндекс.Маркет парсер инициализирован (с Selenium)")
            else:
                logger.info("✅ Яндекс.Маркет парсер инициализирован (без Selenium)")
        except Exception as e:
            logger.warning(f"Не удалось инициализировать парсер: {e}")
            self.yandex_parser = None
        
    def search_products(
        self,
        query: str,
        use_cache: bool = True,
        shops: Optional[List[str]] = None
    ) -> Dict[str, List[ProductData]]:
        """
        Поиск товаров
        
        Args:
            query: Поисковый запрос
            use_cache: Использовать ли кэш
            shops: Список магазинов (игнорируется)
        
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
        
        logger.info(f"🔍 Начинаю поиск товаров по запросу: '{query}'")
        logger.info(f"   Доступные источники: API={self.yandex_api is not None}, Парсер={self.yandex_parser is not None}")
        
        # Поиск через Яндекс.Маркет API
        if self.yandex_api:
            try:
                logger.info(f"📡 Пробую поиск через Яндекс.Маркет API...")
                products = self.yandex_api.search_products(query=query, limit=30)
                if products:
                    results["Яндекс.Маркет"] = products
                    logger.info(f"✅ Найдено {len(products)} товаров через API")
                    if products:
                        logger.info(f"   Примеры: {', '.join([p.title[:40] for p in products[:3]])}")
                else:
                    logger.warning("⚠️ API вернул пустой список товаров")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка API: {e}, пробую парсер")
        
        # Если API не сработал, используем парсер
        if "Яндекс.Маркет" not in results or not results["Яндекс.Маркет"]:
            if self.yandex_parser:
                try:
                    logger.info(f"🕷️ Пробую поиск через парсер Яндекс.Маркет...")
                    products = self.yandex_parser.search_products(query=query, limit=30)
                    if products:
                        results["Яндекс.Маркет"] = products
                        logger.info(f"✅ Найдено {len(products)} товаров через парсер")
                        if products:
                            logger.info(f"   Примеры: {', '.join([p.title[:40] for p in products[:3]])}")
                    else:
                        logger.warning("⚠️ Парсер вернул пустой список товаров")
                except Exception as e:
                    logger.error(f"❌ Ошибка парсера: {e}", exc_info=True)
            else:
                logger.error("❌ Парсер недоступен! Поиск невозможен.")
        
        # Итоговый результат
        total_found = sum(len(products) for products in results.values())
        if total_found > 0:
            logger.info(f"✅ Итого найдено {total_found} товаров из {len(results)} источников")
        else:
            logger.warning("⚠️ Товары не найдены ни через API, ни через парсер")
        
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
        
        # Логируем результаты из каждого источника
        total_products = 0
        for shop_name, products in all_results.items():
            logger.info(f"Источник '{shop_name}': найдено {len(products)} товаров")
            total_products += len(products)
        logger.info(f"Всего товаров из всех источников: {total_products}")
        
        # Группировка товаров по бренду и модели
        product_groups = {}
        
        for shop_name, products in all_results.items():
            logger.info(f"Обработка {len(products)} товаров из {shop_name}")
            for product in products:
                # Используем комбинацию бренда и модели как ключ
                # Нормализуем ключ: убираем лишние пробелы и приводим к нижнему регистру
                brand_normalized = product.brand.lower().strip() if product.brand else ""
                model_normalized = product.model.lower().strip() if product.model else ""
                
                # Если бренд "Не указан", пробуем извлечь из названия
                if brand_normalized in ["не указан", "", "unknown"]:
                    # Пробуем найти бренд в начале названия
                    title_lower = product.title.lower()
                    for known_brand in ["oneplus", "apple", "samsung", "xiaomi", "huawei", "google", "sony", "lg", "asus", "lenovo", "hp", "dell", "acer", "msi", "dyson"]:
                        if title_lower.startswith(known_brand) or f"смартфон {known_brand}" in title_lower or f"ноутбук {known_brand}" in title_lower:
                            brand_normalized = known_brand
                            break
                
                key = f"{brand_normalized}_{model_normalized}".strip('_')
                
                if not key or key == '_' or len(key) < 3:
                    # Если не удалось извлечь бренд/модель, используем нормализованное название
                    title_normalized = product.title.lower().strip()[:50]
                    # Убираем общие слова для лучшей группировки
                    title_normalized = title_normalized.replace("смартфон", "").replace("ноутбук", "").strip()
                    key = title_normalized if title_normalized else product.title.lower()[:50]
                
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
                    # Сохраняем URL в кэш для быстрого доступа
                    if product.url and product.url.strip():
                        try:
                            from url_cache_service import URLCacheService
                            url_cache = URLCacheService(redis_client=self.redis_client if self.redis_enabled else None)
                            url_cache.save_product_url(
                                url=product.url,
                                brand=product.brand,
                                model=product.model,
                                title=product.title
                            )
                        except Exception as e:
                            logger.debug(f"Не удалось сохранить URL в кэш: {e}")
                    
                    product_groups[key]["prices"].append({
                        "shop_name": product.shop_name,
                        "price": product.price,
                        "url": product.url,
                        "scraped_at": product.scraped_at.isoformat() if product.scraped_at else datetime.utcnow().isoformat()
                    })
                    logger.debug(f"Добавлена цена из {product.shop_name} для товара: {product.title[:50]}...")
                else:
                    logger.debug(f"Цена от {product.shop_name} уже существует для товара: {product.title[:50]}...")
        
        # Преобразование в список и сортировка по минимальной цене
        aggregated = []
        for key, data in product_groups.items():
            prices = data["prices"]
            if prices:
                price_values = [p["price"] for p in prices]
                shops_list = [p["shop_name"] for p in prices]
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
                logger.debug(f"Агрегирован товар: {data['title'][:50]}... из магазинов: {shops_list}")
        
        # Сортировка по минимальной цене
        aggregated.sort(key=lambda x: x["min_price"])
        
        # Возвращаем отсортированные товары
        # Подсчитываем статистику по магазинам
        shop_stats = {}
        for item in aggregated:
            for price_info in item["prices"]:
                shop_name = price_info["shop_name"]
                shop_stats[shop_name] = shop_stats.get(shop_name, 0) + 1
        
        logger.info(f"Итого агрегировано {len(aggregated)} уникальных товаров")
        logger.info(f"Статистика по магазинам: {shop_stats}")
        logger.info(f"Товаров с ценами из нескольких магазинов: {sum(1 for item in aggregated if len(item['prices']) > 1)}")
        
        return aggregated
    
    def get_popular_products(
        self,
        limit: int = 10,
        use_cache: bool = True,
        category: str = "электроника"
    ) -> List[Dict]:
        """
        Получение популярных товаров
        
        Args:
            limit: Количество товаров (по умолчанию 10)
            use_cache: Использовать ли кэш
            category: Категория товаров
        
        Returns:
            Список популярных товаров с ценами
        """
        cache_key = f"popular_products:{limit}"
        
        # Проверка кэша
        if use_cache and self.redis_enabled:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    logger.info(f"✅ Популярные товары найдены в кэше")
                    return json.loads(cached_data)
            except Exception as e:
                logger.error(f"Ошибка чтения из кэша: {e}")
        
        # Получаем товары из Яндекс.Маркет
        products = []
        
        # Проверяем доступность API и парсера
        logger.info(f"🔍 Проверка доступности источников данных:")
        logger.info(f"   - yandex_api: {'✅ Доступен' if self.yandex_api else '❌ Недоступен'}")
        logger.info(f"   - yandex_parser: {'✅ Доступен' if self.yandex_parser else '❌ Недоступен'}")
        
        # Сначала пробуем через API (если доступен)
        if self.yandex_api:
            try:
                logger.info(f"📡 Пробую получить товары через Яндекс.Маркет API (категория: {category}, лимит: {limit})")
                products_data = self.yandex_api.get_popular_products(category=category, limit=limit)
                if products_data:
                    products = products_data
                    logger.info(f"✅ Получено {len(products)} товаров через API")
                    if products:
                        logger.info(f"   Примеры товаров: {', '.join([p.title[:30] for p in products[:3]])}")
                else:
                    logger.warning("⚠️ API вернул пустой список, пробую парсер")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка API: {e}, пробую парсер", exc_info=True)
        else:
            logger.info("ℹ️ Яндекс.Маркет API недоступен (YANDEX_OAUTH_TOKEN не настроен), пробую парсер")
        
        # Если API не сработал или недоступен, используем парсер
        if not products and self.yandex_parser:
            try:
                logger.info(f"🕷️ Получение товаров через парсер (категория: {category}, лимит: {limit})")
                products_data = self.yandex_parser.get_popular_products(category=category, limit=limit)
                if products_data:
                    products = products_data
                    logger.info(f"✅ Получено {len(products)} товаров через парсер")
                    if products:
                        logger.info(f"   Примеры товаров: {', '.join([p.title[:30] for p in products[:3]])}")
                else:
                    logger.warning("⚠️ Парсер вернул пустой список товаров")
            except Exception as e:
                logger.error(f"❌ Ошибка парсера: {e}", exc_info=True)
        elif not products and not self.yandex_parser:
            logger.error("❌ Парсер недоступен! Товары из Яндекс.Маркет не могут быть получены.")
        
        if not products:
            logger.warning("⚠️ Не удалось получить товары ни через API, ни через парсер")
        
        # Преобразуем в формат для API
        result = []
        for product in products:
            brand = product.brand if product.brand is not None else "Не указан"
            model = product.model if product.model is not None else "Не указана"
            
            result.append({
                "title": product.title,
                "brand": brand,
                "model": model,
                "image": product.image,
                "description": product.description,
                "prices": [{
                    "shop_name": product.shop_name,
                    "price": product.price,
                    "url": product.url,
                    "scraped_at": product.scraped_at.isoformat() if product.scraped_at else datetime.utcnow().isoformat()
                }],
                "min_price": product.price,
                "max_price": product.price,
                "shops_count": 1
            })
        
        # Сохранение в кэш
        if self.redis_enabled and result:
            try:
                self.redis_client.setex(
                    cache_key,
                    min(self.cache_ttl, 3600),  # Максимум 1 час для популярных товаров
                    json.dumps(result, default=str)
                )
                logger.info(f"Популярные товары сохранены в кэш")
            except Exception as e:
                logger.error(f"Ошибка записи в кэш: {e}")
        
        return result
    
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
    
    def clear_cache(self, pattern: str = "*") -> int:
        """
        Очистка кэша
        
        Args:
            pattern: Паттерн для поиска ключей (по умолчанию "*" - все ключи)
        
        Returns:
            Количество удаленных ключей
        """
        if not self.redis_enabled:
            logger.warning("Redis не доступен, очистка кэша невозможна")
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"✅ Очищено {deleted} ключей из кэша (паттерн: {pattern})")
                return deleted
            else:
                logger.info(f"ℹ️ Ключи не найдены (паттерн: {pattern})")
                return 0
        except Exception as e:
            logger.error(f"❌ Ошибка очистки кэша: {e}")
            return 0
    
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
