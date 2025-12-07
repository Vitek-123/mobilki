"""
Парсер для Яндекс.Маркет (HTML парсинг)
Можно использовать пока ждете одобрения партнерской программы
"""
import requests
from bs4 import BeautifulSoup
import time
import logging
from typing import List, Dict, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)


class YandexMarketParser:
    """Парсер для получения данных с Яндекс.Маркет"""
    
    def __init__(self):
        self.base_url = "https://market.yandex.ru"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
    
    def search_products(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Поиск товаров на Яндекс.Маркет
        
        Args:
            query: Поисковый запрос
            limit: Количество товаров
        
        Returns:
            Список товаров с данными
        """
        try:
            # Формируем URL для поиска
            search_url = f"{self.base_url}/search"
            params = {
                "text": query,
                "local-offers-first": "0"
            }
            
            logger.info(f"Поиск товаров по запросу: '{query}'")
            
            # Делаем запрос
            response = requests.get(
                search_url,
                params=params,
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code != 200:
                logger.error(f"Ошибка запроса: статус {response.status_code}")
                return []
            
            # Парсим HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем карточки товаров
            # Структура может меняться, нужно адаптировать селекторы
            products = []
            
            # Попробуем разные селекторы
            product_cards = soup.find_all(['div', 'article'], class_=lambda x: x and ('product' in x.lower() or 'offer' in x.lower() or 'card' in x.lower()))
            
            if not product_cards:
                # Альтернативный способ - ищем по data-атрибутам
                product_cards = soup.find_all(attrs={"data-zone-name": "productSnippet"})
            
            logger.info(f"Найдено {len(product_cards)} карточек товаров")
            
            for card in product_cards[:limit]:
                try:
                    product_data = self._parse_product_card(card)
                    if product_data:
                        products.append(product_data)
                except Exception as e:
                    logger.debug(f"Ошибка парсинга карточки: {e}")
                    continue
            
            logger.info(f"Успешно распарсено {len(products)} товаров")
            return products
            
        except Exception as e:
            logger.error(f"Ошибка поиска товаров: {e}", exc_info=True)
            return []
    
    def _parse_product_card(self, card) -> Optional[Dict]:
        """Парсинг одной карточки товара"""
        try:
            # Название товара
            title_elem = card.find(['h3', 'a', 'span'], class_=lambda x: x and ('title' in x.lower() or 'name' in x.lower()))
            if not title_elem:
                title_elem = card.find('a', href=lambda x: x and '/product/' in x)
            
            title = title_elem.get_text(strip=True) if title_elem else "Не указано"
            
            # Цена
            price_elem = card.find(['span', 'div'], class_=lambda x: x and 'price' in x.lower())
            if not price_elem:
                price_elem = card.find(string=lambda x: x and '₽' in str(x))
            
            price_text = price_elem.get_text(strip=True) if price_elem else "0"
            price = self._extract_price(price_text)
            
            # URL
            url_elem = card.find('a', href=lambda x: x and '/product/' in x)
            url = url_elem['href'] if url_elem and url_elem.get('href') else None
            if url and not url.startswith('http'):
                url = self.base_url + url
            
            # Изображение
            img_elem = card.find('img')
            image = img_elem.get('src') or img_elem.get('data-src') if img_elem else None
            
            if not title or title == "Не указано" or price == 0:
                return None
            
            return {
                "title": title,
                "price": price,
                "url": url,
                "image": image,
                "shop_name": "Яндекс.Маркет"
            }
            
        except Exception as e:
            logger.debug(f"Ошибка парсинга карточки: {e}")
            return None
    
    def _extract_price(self, price_text: str) -> float:
        """Извлечение цены из текста"""
        try:
            # Убираем все кроме цифр и точки/запятой
            import re
            price_clean = re.sub(r'[^\d,.]', '', price_text.replace(' ', '').replace(',', '.'))
            if price_clean:
                return float(price_clean)
        except:
            pass
        return 0.0
    
    def get_popular_phones(self, limit: int = 3) -> List[Dict]:
        """Получение популярных смартфонов"""
        return self.search_products("смартфон популярные", limit=limit)


if __name__ == "__main__":
    # Тестирование
    logging.basicConfig(level=logging.INFO)
    
    parser = YandexMarketParser()
    
    print("Тест поиска товаров...")
    products = parser.search_products("смартфон", limit=5)
    
    print(f"\nНайдено товаров: {len(products)}")
    for i, product in enumerate(products, 1):
        print(f"\n{i}. {product['title']}")
        print(f"   Цена: {product['price']} руб.")
        print(f"   URL: {product.get('url', 'N/A')}")

