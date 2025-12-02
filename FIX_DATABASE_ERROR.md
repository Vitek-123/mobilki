# Исправление ошибки базы данных

## Проблема
Ошибка при создании таблиц: `Invalid default value for 'viewed_at'`

## Причина
MySQL не принимает `server_default='CURRENT_TIMESTAMP'` как строку. Нужно использовать `text('CURRENT_TIMESTAMP')`.

## Решение

### Вариант 1: Удалить проблемные таблицы (рекомендуется)

Если таблицы уже созданы с ошибкой, удалите их вручную:

```sql
-- Подключитесь к MySQL и выполните:
DROP TABLE IF EXISTS view_history;
DROP TABLE IF EXISTS favorites;
DROP TABLE IF EXISTS price_alerts;
DROP TABLE IF EXISTS shopping_lists;
DROP TABLE IF EXISTS shopping_list_items;
DROP TABLE IF EXISTS comparisons;
DROP TABLE IF EXISTS comparison_products;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS referrals;
DROP TABLE IF EXISTS subscriptions;
```

Затем перезапустите `main.py` - таблицы создадутся автоматически с правильным синтаксисом.

### Вариант 2: Исправить существующие таблицы

Если хотите сохранить данные, исправьте таблицы вручную:

```sql
-- Для каждой таблицы с TIMESTAMP полями:
ALTER TABLE view_history MODIFY viewed_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE favorites MODIFY added_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE price_alerts MODIFY created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP;
-- И так далее для всех таблиц...
```

## После исправления

1. Перезапустите `main.py`
2. Проверьте, что таблицы созданы без ошибок
3. Проверьте, что карточки товаров загружаются

## Что было исправлено

В файле `python/models.py` все `server_default='CURRENT_TIMESTAMP'` заменены на `server_default=text('CURRENT_TIMESTAMP')`.

Исправлены следующие таблицы:
- ✅ view_history
- ✅ favorites
- ✅ price_alerts
- ✅ shopping_lists
- ✅ shopping_list_items
- ✅ comparisons
- ✅ comparison_products
- ✅ reviews
- ✅ referrals
- ✅ subscriptions
- ✅ prices (уже была правильной, но для консистентности)

