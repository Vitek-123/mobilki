"""
Тестовый скрипт для проверки поиска товаров в Яндекс.Маркет
"""
import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

from external_data_service import ExternalDataService
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_search():
    """Тестирование поиска товаров"""
    
    # Инициализация сервиса
    logger.info("=" * 80)
    logger.info("🔍 ТЕСТ ПОИСКА ТОВАРОВ В ЯНДЕКС.МАРКЕТ")
    logger.info("=" * 80)
    
    redis_enabled = os.getenv("REDIS_ENABLED", "true").lower() in ("true", "1", "yes")
    service = ExternalDataService(
        redis_host=os.getenv("REDIS_HOST", "localhost"),
        redis_port=int(os.getenv("REDIS_PORT", "6379")),
        redis_db=int(os.getenv("REDIS_DB", "0")),
        cache_ttl=int(os.getenv("CACHE_TTL", "10800")),
        redis_enabled=redis_enabled
    )
    
    # Тестовые запросы
    test_queries = [
        "смартфон",
        "наушники",
        "ноутбук"
    ]
    
    for query in test_queries:
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"🔍 Тестирую поиск по запросу: '{query}'")
        logger.info("=" * 80)
        
        try:
            # Поиск товаров
            results = service.search_products(query=query, use_cache=False)
            
            # Выводим результаты
            total_products = 0
            for shop_name, products in results.items():
                logger.info(f"📦 Магазин: {shop_name}")
                logger.info(f"   Найдено товаров: {len(products)}")
                total_products += len(products)
                
                if products:
                    logger.info("   Примеры товаров:")
                    for i, product in enumerate(products[:5], 1):
                        logger.info(f"      {i}. {product.title[:60]}")
                        logger.info(f"         Бренд: {product.brand}, Модель: {product.model}")
                        logger.info(f"         Цена: {product.price} ₽")
                        logger.info(f"         URL: {product.url[:80]}...")
            
            logger.info("")
            logger.info(f"✅ Итого найдено: {total_products} товаров")
            
            if total_products == 0:
                logger.warning("⚠️ Товары не найдены! Проверьте:")
                logger.warning("   1. Установлен ли Selenium и Chrome")
                logger.warning("   2. Включен ли USE_SELENIUM_FOR_PARSING=true в .env")
                logger.warning("   3. Доступен ли Яндекс.Маркет")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при поиске: {e}", exc_info=True)
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    logger.info("=" * 80)

if __name__ == "__main__":
    test_search()

