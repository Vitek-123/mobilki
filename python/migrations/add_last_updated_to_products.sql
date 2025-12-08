-- Миграция: Добавление колонки last_updated в таблицу products
-- Выполните этот SQL скрипт в вашей базе данных

ALTER TABLE products 
ADD COLUMN last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

-- Проверка
SELECT COLUMN_NAME, DATA_TYPE, COLUMN_DEFAULT, EXTRA 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'products' AND COLUMN_NAME = 'last_updated';

