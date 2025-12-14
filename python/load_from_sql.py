"""
Скрипт для загрузки данных из SQL файла Base_data.sql в базу данных
Использование: python load_from_sql.py
"""
import os
import sys
import logging
from pathlib import Path
from sqlalchemy import text
from database import engine, SessionLocal
from models import Product, Shop, Listing, Price

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_sql_file(file_path: str) -> str:
    """Чтение SQL файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Файл {file_path} не найден!")
        return None
    except Exception as e:
        logger.error(f"Ошибка при чтении файла {file_path}: {e}")
        return None


def parse_sql_statements(sql_content: str) -> list:
    """
    Парсинг SQL файла на отдельные команды
    Игнорирует комментарии и пустые строки
    """
    statements = []
    current_statement = []
    
    for line in sql_content.split('\n'):
        line = line.strip()
        
        # Пропускаем пустые строки и комментарии
        if not line or line.startswith('--') or line.startswith('#'):
            continue
        
        # Пропускаем команды show, use, drop
        if any(line.upper().startswith(cmd) for cmd in ['SHOW', 'USE', 'DROP']):
            continue
        
        current_statement.append(line)
        
        # Если строка заканчивается на ;, завершаем команду
        if line.endswith(';'):
            statement = ' '.join(current_statement)
            if statement.strip():
                statements.append(statement)
            current_statement = []
    
    # Добавляем последнюю команду, если она не закончилась на ;
    if current_statement:
        statement = ' '.join(current_statement)
        if statement.strip():
            statements.append(statement)
    
    return statements


def execute_sql_file(file_path: str):
    """Выполнение SQL файла"""
    logger.info("=" * 60)
    logger.info("🚀 Начало загрузки данных из SQL файла")
    logger.info("=" * 60)
    
    # Получаем абсолютный путь к файлу
    if not os.path.isabs(file_path):
        # Ищем файл в корне проекта
        project_root = Path(__file__).parent.parent
        file_path = project_root / file_path
    
    logger.info(f"📄 Чтение файла: {file_path}")
    
    sql_content = read_sql_file(str(file_path))
    if not sql_content:
        logger.error("❌ Не удалось прочитать SQL файл")
        return False
    
    # Парсим SQL на отдельные команды
    statements = parse_sql_statements(sql_content)
    logger.info(f"📝 Найдено {len(statements)} SQL команд")
    
    # Выполняем команды
    connection = engine.connect()
    transaction = connection.begin()
    
    try:
        executed_count = 0
        skipped_count = 0
        last_insert_id = None  # Для хранения последнего вставленного ID
        
        for i, statement in enumerate(statements, 1):
            try:
                # Пропускаем команды создания таблиц (они уже должны существовать)
                if any(keyword in statement.upper() for keyword in ['CREATE TABLE', 'ALTER TABLE']):
                    logger.debug(f"⏭️  Пропущена команда создания таблицы: {statement[:50]}...")
                    skipped_count += 1
                    continue
                
                # Выполняем INSERT команды
                if statement.upper().startswith('INSERT'):
                    # Заменяем LAST_INSERT_ID() на реальное значение, если оно есть
                    if 'LAST_INSERT_ID()' in statement:
                        if last_insert_id is None:
                            logger.warning(f"⚠️  LAST_INSERT_ID() используется, но предыдущий INSERT не найден. Команда: {statement[:80]}...")
                            # Пытаемся выполнить как есть
                            result = connection.execute(text(statement))
                        else:
                            # Заменяем LAST_INSERT_ID() на реальное значение
                            modified_statement = statement.replace('LAST_INSERT_ID()', str(last_insert_id))
                            logger.debug(f"Замена LAST_INSERT_ID() на {last_insert_id}")
                            result = connection.execute(text(modified_statement))
                    else:
                        result = connection.execute(text(statement))
                    
                    # Получаем ID последней вставленной записи для следующей команды
                    last_insert_id = connection.execute(text("SELECT LAST_INSERT_ID()")).scalar()
                    
                    executed_count += 1
                    logger.debug(f"✅ Выполнена команда {i}/{len(statements)}: {statement[:80]}...")
                else:
                    logger.debug(f"⏭️  Пропущена команда: {statement[:50]}...")
                    skipped_count += 1
                    
            except Exception as e:
                # Игнорируем ошибки дубликатов (если данные уже есть)
                if 'Duplicate entry' in str(e) or '1062' in str(e):
                    logger.debug(f"⏭️  Пропущено (дубликат): {statement[:50]}...")
                    skipped_count += 1
                else:
                    logger.warning(f"⚠️  Ошибка при выполнении команды {i}: {e}")
                    logger.debug(f"Команда: {statement[:100]}")
        
        transaction.commit()
        logger.info(f"\n✅ Выполнено команд: {executed_count}")
        logger.info(f"⏭️  Пропущено команд: {skipped_count}")
        
        return True
        
    except Exception as e:
        transaction.rollback()
        logger.error(f"❌ Ошибка при выполнении SQL: {e}", exc_info=True)
        return False
    finally:
        connection.close()


def verify_data(db):
    """Проверка загруженных данных"""
    try:
        total_products = db.query(Product).count()
        total_shops = db.query(Shop).count()
        total_listings = db.query(Listing).count()
        total_prices = db.query(Price).count()
        
        logger.info(f"\n📊 Статистика базы данных:")
        logger.info(f"  - Товаров: {total_products}")
        logger.info(f"  - Магазинов: {total_shops}")
        logger.info(f"  - Объявлений: {total_listings}")
        logger.info(f"  - Цен: {total_prices}")
        
        # Показываем примеры товаров
        if total_products > 0:
            logger.info(f"\n📦 Примеры товаров:")
            products = db.query(Product).limit(5).all()
            for product in products:
                listings_count = db.query(Listing).filter(Listing.product_id == product.id_product).count()
                logger.info(f"  - {product.title} (ID: {product.id_product}, объявлений: {listings_count})")
        
    except Exception as e:
        logger.error(f"Ошибка при проверке данных: {e}")


def main():
    """Основная функция"""
    # Путь к SQL файлу
    sql_file = "Base_data.sql"
    
    # Выполняем SQL файл
    success = execute_sql_file(sql_file)
    
    if success:
        logger.info("\n" + "=" * 60)
        logger.info("✅ Данные успешно загружены из SQL файла!")
        logger.info("=" * 60)
        
        # Проверяем данные
        db = SessionLocal()
        try:
            verify_data(db)
        finally:
            db.close()
    else:
        logger.error("\n❌ Ошибка при загрузке данных из SQL файла")
        sys.exit(1)


if __name__ == "__main__":
    main()

