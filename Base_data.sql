-- ============================================
-- БАЗА ДАННЫХ ДЛЯ ПРОЕКТА MOBILKI
-- ============================================
-- Этот файл содержит структуру БД и данные
-- Для загрузки данных выполните: python load_from_sql.py
-- ============================================

show databases;
use project_mobilki_aviasales;
show tables;

-- ============================================
-- СОЗДАНИЕ ТАБЛИЦ
-- ============================================

create table User (id_user int primary key auto_increment,
	login varchar(255),
    password varchar(255),
    email varchar (255));
    
drop table User;

CREATE TABLE products (
    id_product INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    image varchar(500),
    price DECIMAL(12,2) DEFAULT NULL);
    
drop table products;

CREATE TABLE shops (
    id_shop INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255));
    
drop table shops;

CREATE TABLE listings (
    id_listing INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    shop_id INT NOT NULL,
    url TEXT,
    FOREIGN KEY (product_id) REFERENCES products(id_product) ON DELETE CASCADE,
    FOREIGN KEY (shop_id) REFERENCES shops(id_shop) ON DELETE CASCADE);
    
drop table listings;

CREATE TABLE prices (
    id_price INT AUTO_INCREMENT PRIMARY KEY,
    listing_id INT NOT NULL,
    price DECIMAL(12,2) NOT NULL,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (listing_id) REFERENCES listings(id_listing) ON DELETE CASCADE);
    
drop table prices;

-- ============================================
-- ДАННЫЕ
-- ============================================
    
USE project_mobilki_aviasales;

-- Добавляем магазины
INSERT INTO shops (name) VALUES 
('DNS'),
('М.Видео'),
('Ситилинк'),
('Эльдорадо'),
('Яндекс.Маркет');

-- ============================================
-- ДОБАВЛЕНИЕ ТОВАРОВ
-- ============================================
-- Для добавления нового товара:
-- 1. Добавьте INSERT в products
-- 2. Добавьте INSERT в listings (связь с магазином)
-- 3. Добавьте INSERT в prices (цена)
-- 
-- ВАЖНО: Используйте NULL для id_product, id_shop, id_listing, id_price
-- БД сама сгенерирует ID автоматически
-- ============================================

-- Добавляем продукты
INSERT INTO products (title, image, price) VALUES 
('Смартфон Samsung Galaxy S23', 'https://static.re-store.ru/upload/resize_cache/iblock/425/100500_800_140cd750bba9870f18aada2478b24840a/63zba8vr1pr1qx83hjr8hq3qd76uj8of.jpg', 79990.00),
('iPhone 15 Pro', 'https://static.re-store.ru/upload/resize_cache/iblock/425/100500_800_140cd750bba9870f18aada2478b24840a/63zba8vr1pr1qx83hjr8hq3qd76uj8of.jpg', 99990.00),
('Xiaomi Redmi Note 13', 'https://static.re-store.ru/upload/resize_cache/iblock/3e7/100500_800_140cd750bba9870f18aada2478b24840a/c6b0ndzv7rqf8u9c456xwvgolvkkdf11.jpg', 24990.00),
('Телевизор LG OLED55', 'https://static.re-store.ru/upload/resize_cache/iblock/425/100500_800_140cd750bba9870f18aada2478b24840a/63zba8vr1pr1qx83hjr8hq3qd76uj8of.jpg', 129990.00),
('Ноутбук ASUS VivoBook 15', 'https://static.re-store.ru/upload/resize_cache/iblock/e85/100500_800_140cd750bba9870f18aada2478b24840a/yrkukzmdild23d24dndqd62c00sin6iz.jpg', 59990.00);

-- ============================================
-- ДОБАВЛЕНИЕ НОВОГО ТОВАРА (ПРИМЕР)
-- ============================================
-- Раскомментируйте и заполните:
--
-- INSERT INTO products (title, image) VALUES 
-- ('Название товара', 'https://example.com/image.jpg');
--
-- Затем добавьте объявление (связь с магазином):
-- INSERT INTO listings (product_id, shop_id, url) VALUES 
-- (LAST_INSERT_ID(), 1, 'https://www.dns-shop.ru/product/ваша-ссылка/');
--
-- И добавьте цену:
-- INSERT INTO prices (listing_id, price) VALUES 
-- (LAST_INSERT_ID(), 50000.00);
-- ============================================

-- Добавляем listings (связи товаров с магазинами)
-- ВАЖНО: Используйте конкретные ID товаров или LAST_INSERT_ID() если добавляете товар последовательно
-- ID магазинов: 1=DNS, 2=М.Видео, 3=Ситилинк, 4=Эльдорадо, 5=Яндекс.Маркет
INSERT INTO listings (product_id, shop_id, url) VALUES 
(1, 1, 'https://www.dns-shop.ru/product/samsung-galaxy-s23/'),
(1, 2, 'https://www.mvideo.ru/products/samsung-galaxy-s23'),
(1, 3, 'https://www.citilink.ru/product/samsung-galaxy-s23/'),
(2, 1, 'https://www.dns-shop.ru/product/iphone-15-pro/'),
(2, 4, 'https://www.eldorado.ru/product/iphone-15-pro'),
(3, 2, 'https://www.mvideo.ru/products/xiaomi-redmi-note-13'),
(3, 3, 'https://www.citilink.ru/product/xiaomi-redmi-note-13/'),
(4, 1, 'https://www.dns-shop.ru/product/lg-oled55/'),
(4, 2, 'https://www.mvideo.ru/products/lg-oled55'),
(5, 3, 'https://www.citilink.ru/product/asus-vivobook-15/');

-- Добавляем цены
-- ВАЖНО: listing_id должен соответствовать существующему listing
INSERT INTO prices (listing_id, price) VALUES 
(1, 79999.00),
(2, 78999.00),
(3, 82999.00),
(4, 99999.00),
(5, 101999.00),
(6, 24999.00),
(7, 23999.00),
(8, 89999.00),
(9, 87999.00),
(10, 45999.00);

-- ============================================
-- КОНЕЦ ФАЙЛА
-- ============================================
