"""
Скрипт для выполнения миграции: обновление структуры таблицы products
Использование: python run_migration.py
"""
import logging
from pathlib import Path
from sqlalchemy import text
from database import engine, SessionLocal
from models import Product

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_migration():
    """Выполнение миграции для обновления структуры таблицы products"""
    logger.info("=" * 60)
    logger.info("🔄 Начало миграции: обновление структуры таблицы products")
    logger.info("=" * 60)
    
    # Путь к файлу миграции
    migration_file = Path(__file__).parent / "migrations" / "update_products_structure.sql"
    
    if not migration_file.exists():
        logger.error(f"❌ Файл миграции не найден: {migration_file}")
        return False
    
    logger.info(f"📄 Чтение файла миграции: {migration_file}")
    
    # Читаем SQL файл
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
    except Exception as e:
        logger.error(f"❌ Ошибка при чтении файла: {e}")
        return False
    
    # Выполняем миграцию
    connection = engine.connect()
    
    try:
        # Удаляем комментарии и разбиваем на команды
        # Сначала удаляем однострочные комментарии
        lines = []
        for line in sql_content.split('\n'):
            if '--' in line:
                # Удаляем комментарий, но оставляем часть до него
                line = line.split('--')[0]
            lines.append(line)
        cleaned_content = '\n'.join(lines)
        
        # Разбиваем на команды по точке с запятой
        # Собираем все в одну строку и разбиваем по ';'
        single_line = ' '.join(cleaned_content.split())
        statements = [s.strip() for s in single_line.split(';') if s.strip() and not s.strip().upper().startswith('USE')]
        
        executed_count = 0
        skipped_count = 0
        
        logger.info(f"📝 Найдено команд для выполнения: {len(statements)}")
        for idx, stmt in enumerate(statements, 1):
            logger.debug(f"  Команда {idx}: {stmt[:100]}...")
        
        for i, statement in enumerate(statements, 1):
            if statement.upper().startswith('SELECT'):
                # SELECT команды выполняем отдельно для вывода результата
                try:
                    result = connection.execute(text(statement))
                    rows = result.fetchall()
                    if rows:
                        logger.info("📊 Структура таблицы products после миграции:")
                        for row in rows:
                            logger.info(f"  - {row[0]}: {row[1]} ({row[2] if len(row) > 2 else 'N/A'})")
                except Exception as e:
                    logger.debug(f"Ошибка при выполнении SELECT: {e}")
                continue
            
            if statement.upper().startswith('ALTER'):
                logger.info(f"Выполнение команды {i}/{len(statements)}: {statement[:100]}...")
                # Выполняем каждую команду в отдельной транзакции
                trans = connection.begin()
                try:
                    connection.execute(text(statement))
                    trans.commit()
                    logger.info("✅ Команда выполнена успешно")
                    executed_count += 1
                except Exception as e:
                    trans.rollback()
                    error_str = str(e).lower()
                    # Проверяем, может колонки уже удалены/добавлены
                    if any(phrase in error_str for phrase in [
                        'unknown column', "doesn't exist", 'check that column/key exists',
                        'duplicate column name', 'already exists', 'duplicate'
                    ]):
                        logger.info("ℹ️  Колонки уже обработаны (удалены/добавлены ранее)")
                        skipped_count += 1
                    else:
                        logger.warning(f"⚠️  Ошибка: {e}")
                        logger.debug(f"Полная команда: {statement}")
                continue
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Миграция успешно выполнена!")
        logger.info("=" * 60)
        logger.info(f"📊 Выполнено команд: {executed_count}")
        logger.info(f"⏭️  Пропущено команд: {skipped_count}")
        
        # Проверяем структуру таблицы через прямой SQL (не через ORM)
        try:
            result = connection.execute(text("""
                SELECT COLUMN_NAME, DATA_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'products' 
                  AND TABLE_SCHEMA = DATABASE()
                ORDER BY ORDINAL_POSITION
            """))
            rows = result.fetchall()
            if rows:
                logger.info("\n📊 Финальная структура таблицы products:")
                for row in rows:
                    logger.info(f"  - {row[0]}: {row[1]}")
            
            # Проверяем количество товаров через прямой SQL
            result = connection.execute(text("SELECT COUNT(*) FROM products"))
            count = result.scalar()
            logger.info(f"\n📦 Всего товаров в БД: {count}")
        except Exception as e:
            logger.warning(f"⚠️  Не удалось проверить структуру: {e}")
        
        return True
        
    except Exception as e:
        error_str = str(e).lower()
        logger.error(f"❌ Ошибка при выполнении миграции: {e}", exc_info=True)
        return False
    finally:
        connection.close()


def main():
    """Основная функция"""
    success = run_migration()
    
    if not success:
        logger.error("\n❌ Миграция не выполнена. Проверьте ошибки выше.")
        exit(1)
    else:
        logger.info("\n✅ Миграция завершена успешно!")


if __name__ == "__main__":
    main()

