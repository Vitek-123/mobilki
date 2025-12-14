# 📋 Работа с данными через SQL файл

## 🎯 Как это работает

Теперь вы можете добавлять товары напрямую в файл **`Base_data.sql`**, а не в Python файлы.

## 🚀 Быстрый старт

### 1. Откройте файл `Base_data.sql`

### 2. Добавьте товар в конец файла:

```sql
-- Товар
INSERT INTO products (title, image) VALUES 
('Ваш товар', 'https://example.com/image.jpg');

-- Объявление (связь с магазином)
INSERT INTO listings (product_id, shop_id, url) VALUES 
(LAST_INSERT_ID(), 1, 'https://www.dns-shop.ru/product/ваша-ссылка/');

-- Цена
INSERT INTO prices (listing_id, price) VALUES 
(LAST_INSERT_ID(), 50000.00);
```

### 3. Загрузите в БД:

```bash
cd python
python load_from_sql.py
```

### 4. Готово!

Товар появится в приложении.

## 📊 ID магазинов

- `1` = DNS
- `2` = М.Видео
- `3` = Ситилинк
- `4` = Эльдорадо
- `5` = Яндекс.Маркет

## 📝 Пример

```sql
-- Добавляем товар
INSERT INTO products (title, image) VALUES 
('Смартфон Samsung Galaxy S24 Ultra', 'https://example.com/image.jpg');

-- Добавляем объявление в DNS
INSERT INTO listings (product_id, shop_id, url) VALUES 
(LAST_INSERT_ID(), 1, 'https://www.dns-shop.ru/product/samsung-s24-ultra/');

-- Добавляем цену
INSERT INTO prices (listing_id, price) VALUES 
(LAST_INSERT_ID(), 99999.00);
```

## ⚠️ Важно

1. **LAST_INSERT_ID()** работает только если команды идут последовательно
2. **URL должен быть полным**: `https://www.dns-shop.ru/product/123/`
3. **Цена в формате**: `99999.00` (с точкой)

## 📚 Подробнее

- `python/HOW_TO_ADD_PRODUCT_TO_SQL.md` - подробная инструкция
- `python/EXAMPLE_SQL_PRODUCT.sql` - примеры товаров
- `python/QUICK_START_SQL.md` - быстрый старт

