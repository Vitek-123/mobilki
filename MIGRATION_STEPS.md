# 🔄 Шаги миграции: Удаление полей из таблицы products

## ✅ Что нужно сделать

### 1. Выполните SQL миграцию

Запустите файл для удаления колонок из БД:

```bash
# Вариант 1: Через MySQL
mysql -u root -p project_mobilki_aviasales < python/migrations/remove_fields_from_products.sql

# Вариант 2: Через Python
cd python
python -c "from database import engine; from sqlalchemy import text; conn = engine.connect(); conn.execute(text(open('migrations/remove_fields_from_products.sql').read())); conn.commit(); conn.close()"
```

### 2. Готово!

Код уже обновлен. После выполнения миграции все будет работать.

## 📋 Что изменилось

### Удалены поля:
- ❌ `brand` (бренд)
- ❌ `model` (модель)  
- ❌ `description` (описание)
- ❌ `last_updated` (дата обновления)

### Остались поля:
- ✅ `id_product` (ID)
- ✅ `title` (название)
- ✅ `image` (изображение)

## 📝 Как добавлять товары теперь

В `Base_data.sql`:

```sql
-- Только title и image
INSERT INTO products (title, image) VALUES 
('Ваш товар', 'https://example.com/image.jpg');
```

**Подробнее:** см. `python/MIGRATION_GUIDE.md`

