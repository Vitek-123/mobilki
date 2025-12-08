-- Миграция для добавления индексов в базу данных
-- Улучшает производительность запросов

-- Индекс для поиска товаров по бренду и модели
CREATE INDEX IF NOT EXISTS idx_products_brand_model ON products(brand, model);

-- Индекс для поиска товаров по названию
CREATE INDEX IF NOT EXISTS idx_products_title ON products(title);

-- Индекс для поиска листингов по ID товара
CREATE INDEX IF NOT EXISTS idx_listings_product_id ON listings(product_id);

-- Индекс для поиска листингов по ID магазина
CREATE INDEX IF NOT EXISTS idx_listings_shop_id ON listings(shop_id);

-- Индекс для поиска цен по ID листинга
CREATE INDEX IF NOT EXISTS idx_prices_listing_id ON prices(listing_id);

-- Индекс для сортировки цен по дате парсинга
CREATE INDEX IF NOT EXISTS idx_prices_scraped_at ON prices(scraped_at DESC);

-- Индекс для поиска истории просмотров по ID пользователя
CREATE INDEX IF NOT EXISTS idx_view_history_user_id ON view_history(user_id);

-- Индекс для сортировки истории просмотров по дате
CREATE INDEX IF NOT EXISTS idx_view_history_viewed_at ON view_history(viewed_at DESC);

-- Индекс для поиска избранного по ID пользователя
CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id);

-- Индекс для поиска отслеживаний цен по ID пользователя
CREATE INDEX IF NOT EXISTS idx_price_alerts_user_id ON price_alerts(user_id);

-- Индекс для поиска активных отслеживаний
CREATE INDEX IF NOT EXISTS idx_price_alerts_active ON price_alerts(is_active, user_id);

