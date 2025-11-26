show databases;
use project_mobilki_aviasales;
show tables;

create table User (id_user int primary key auto_increment,
	login varchar(255),
    password varchar(255),
    email varchar (255));
    
drop table User;

CREATE TABLE products (
    id_product INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    description text,
    brand VARCHAR(255),
    model VARCHAR(255),
    image varchar(500));
    
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
    
USE project_mobilki_aviasales;

-- Добавляем магазины
INSERT INTO shops (name) VALUES 
('DNS'),
('М.Видео'),
('Ситилинк'),
('Эльдорадо');

-- Добавляем продукты
INSERT INTO products (title, brand, model, description, image) VALUES 
('Смартфон Samsung Galaxy S23', 'Samsung', 'Galaxy S23', "телефон бомба често говоря", "https://static.re-store.ru/upload/resize_cache/iblock/425/100500_800_140cd750bba9870f18aada2478b24840a/63zba8vr1pr1qx83hjr8hq3qd76uj8of.jpg"),
('iPhone 15 Pro', 'Apple', 'iPhone 15 Pro', "кто создал это  величие, уййййй", "https://static.re-store.ru/upload/resize_cache/iblock/425/100500_800_140cd750bba9870f18aada2478b24840a/63zba8vr1pr1qx83hjr8hq3qd76uj8of.jpg"),
('Xiaomi Redmi Note 13', 'Xiaomi', 'Redmi Note 13', "апарат тема, базару нет", "https://static.re-store.ru/upload/resize_cache/iblock/3e7/100500_800_140cd750bba9870f18aada2478b24840a/c6b0ndzv7rqf8u9c456xwvgolvkkdf11.jpg"),
('Телевизор LG OLED55', 'LG', 'OLED55C3', "кто спустил это величие на землю", "https://static.re-store.ru/upload/resize_cache/iblock/425/100500_800_140cd750bba9870f18aada2478b24840a/63zba8vr1pr1qx83hjr8hq3qd76uj8of.jpg"),
('Ноутбук ASUS VivoBook 15', 'ASUS', 'VivoBook 15', "мааааммм, купиииии", "https://static.re-store.ru/upload/resize_cache/iblock/e85/100500_800_140cd750bba9870f18aada2478b24840a/yrkukzmdild23d24dndqd62c00sin6iz.jpg");

-- Добавляем listings (связи товаров с магазинами)
INSERT INTO listings (product_id, shop_id, url) VALUES 
(1, 1, 'https://dns-shop.ru/product1'),
(1, 2, 'https://mvideo.ru/product1'),
(1, 3, 'https://citilink.ru/product1'),
(2, 1, 'https://dns-shop.ru/product2'),
(2, 4, 'https://eldorado.ru/product2'),
(3, 2, 'https://mvideo.ru/product3'),
(3, 3, 'https://citilink.ru/product3'),
(4, 1, 'https://dns-shop.ru/product4'),
(4, 2, 'https://mvideo.ru/product4'),
(5, 3, 'https://citilink.ru/product5');

-- Добавляем цены
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


    



    
