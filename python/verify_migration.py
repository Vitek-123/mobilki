"""
Скрипт для проверки структуры таблицы products после миграции
Использование: python verify_migration.py
"""
import logging
from database import SessionLocal, engine
from sqlalchemy import text
from models import Product

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verify_migration():
    """Проверка структуры таблицы products"""
    logger.info("=" * 60)
    logger.info("🔍 Проверка структуры таблицы products")
    logger.info("=" * 60)
    
    connection = engine.connect()
    
    try:
        # Получаем информацию о колонках
        result = connection.execute(text("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'products' 
              AND TABLE_SCHEMA = DATABASE()
            ORDER BY ORDINAL_POSITION
        """))
        
        columns = result.fetchall()
        
        logger.info("\n📊 Структура таблицы products:")
        for col in columns:
            logger.info(f"  - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
        
        # Проверяем, что нужные колонки удалены
        column_names = [col[0] for col in columns]
        
        removed_fields = ['brand', 'model', 'description', 'last_updated']
        existing_removed = [field for field in removed_fields if field in column_names]
        
        if existing_removed:
            logger.warning(f"\n⚠️  Найдены колонки, которые должны быть удалены: {existing_removed}")
            logger.warning("   Выполните миграцию еще раз")
        else:
            logger.info("\n✅ Все ненужные колонки удалены")
        
        # Проверяем, что нужные колонки есть
        required_fields = ['id_product', 'title', 'image']
        missing_fields = [field for field in required_fields if field not in column_names]
        
        if missing_fields:
            logger.error(f"\n❌ Отсутствуют необходимые колонки: {missing_fields}")
        else:
            logger.info("✅ Все необходимые колонки присутствуют")
        
        # Проверяем данные
        db = SessionLocal()
        try:
            product_count = db.query(Product).count()
            logger.info(f"\n📦 Товаров в БД: {product_count}")
            
            if product_count > 0:
                sample_product = db.query(Product).first()
                logger.info(f"📝 Пример товара:")
                logger.info(f"  - ID: {sample_product.id_product}")
                logger.info(f"  - Название: {sample_product.title}")
                logger.info(f"  - Изображение: {sample_product.image[:50] if sample_product.image else 'Нет'}...")
                
                # Пробуем получить доступ к удаленным полям (должна быть ошибка)
                try:
                    _ = sample_product.brand
                    logger.warning("⚠️  Поле 'brand' все еще доступно! Проверьте модель Product")
                except AttributeError:
                    logger.info("✅ Поле 'brand' недоступно (как и должно быть)")
                
                try:
                    _ = sample_product.model
                    logger.warning("⚠️  Поле 'model' все еще доступно! Проверьте модель Product")
                except AttributeError:
                    logger.info("✅ Поле 'model' недоступно (как и должно быть)")
                
                try:
                    _ = sample_product.description
                    logger.warning("⚠️  Поле 'description' все еще доступно! Проверьте модель Product")
                except AttributeError:
                    logger.info("✅ Поле 'description' недоступно (как и должно быть)")
        
        finally:
            db.close()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Проверка завершена")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке: {e}", exc_info=True)
    finally:
        connection.close()


if __name__ == "__main__":
    verify_migration()

