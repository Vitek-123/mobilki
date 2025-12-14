-- Миграция: Удаление полей brand, model, description, last_updated из таблицы products
-- Безопасная версия (проверяет существование колонок перед удалением)
-- Выполните этот SQL скрипт в вашей базе данных

USE project_mobilki_aviasales;

-- Удаляем колонки только если они существуют
SET @dbname = DATABASE();
SET @tablename = "products";
SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = "brand")
  ) > 0,
  "ALTER TABLE products DROP COLUMN brand;",
  "SELECT 'Column brand does not exist' AS message;"
));
PREPARE alterIfExists FROM @preparedStatement;
EXECUTE alterIfExists;
DEALLOCATE PREPARE alterIfExists;

SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = "model")
  ) > 0,
  "ALTER TABLE products DROP COLUMN model;",
  "SELECT 'Column model does not exist' AS message;"
));
PREPARE alterIfExists FROM @preparedStatement;
EXECUTE alterIfExists;
DEALLOCATE PREPARE alterIfExists;

SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = "description")
  ) > 0,
  "ALTER TABLE products DROP COLUMN description;",
  "SELECT 'Column description does not exist' AS message;"
));
PREPARE alterIfExists FROM @preparedStatement;
EXECUTE alterIfExists;
DEALLOCATE PREPARE alterIfExists;

SET @preparedStatement = (SELECT IF(
  (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE
      (table_name = @tablename)
      AND (table_schema = @dbname)
      AND (column_name = "last_updated")
  ) > 0,
  "ALTER TABLE products DROP COLUMN last_updated;",
  "SELECT 'Column last_updated does not exist' AS message;"
));
PREPARE alterIfExists FROM @preparedStatement;
EXECUTE alterIfExists;
DEALLOCATE PREPARE alterIfExists;

-- Проверка
SELECT COLUMN_NAME, DATA_TYPE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'products' 
  AND TABLE_SCHEMA = DATABASE()
ORDER BY ORDINAL_POSITION;

