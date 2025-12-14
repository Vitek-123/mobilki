-- Миграция: Обновление структуры таблицы products
-- Удаляем лишние поля и добавляем price
-- Выполните этот SQL скрипт в вашей базе данных

USE project_mobilki_aviasales;

-- Удаляем лишние колонки
-- Если колонки не существуют, будет ошибка, но она будет обработана скриптом
ALTER TABLE products 
DROP COLUMN brand,
DROP COLUMN model,
DROP COLUMN description,
DROP COLUMN last_updated;

-- Добавляем колонку price
-- Если колонка уже существует, будет ошибка, но она будет обработана скриптом
ALTER TABLE products 
ADD COLUMN price DECIMAL(12,2) DEFAULT NULL;

-- Проверка структуры таблицы
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'products' 
  AND TABLE_SCHEMA = DATABASE()
ORDER BY ORDINAL_POSITION;

