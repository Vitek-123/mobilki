-- Миграция: Удаление полей brand, model, description, last_updated из таблицы products
-- Выполните этот SQL скрипт в вашей базе данных

USE project_mobilki_aviasales;

-- Удаляем колонки
-- В MySQL нет IF EXISTS для DROP COLUMN, поэтому проверяем через информацию о схеме
ALTER TABLE products 
DROP COLUMN brand,
DROP COLUMN model,
DROP COLUMN description,
DROP COLUMN last_updated;

-- Проверка
SELECT COLUMN_NAME, DATA_TYPE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'products' 
ORDER BY ORDINAL_POSITION;

