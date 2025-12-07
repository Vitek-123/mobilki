"""
Улучшенный парсер для Яндекс.Маркет
Парсит JSON данные из HTML или использует Selenium
"""
import requests
from bs4 import BeautifulSoup
import json
import re
import logging
from typing import List, Dict, Optional
from datetime import datetime

from data_providers import ProductData

logger = logging.getLogger(__name__)


class YandexMarketProvider:
    """Провайдер для получения данных с Яндекс.Маркет"""
    
    def __init__(self):
        self.base_url = "https://market.yandex.ru"
        self.provider_name = "Яндекс.Маркет"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        self.last_request_time = 0
        self.min_request_interval = 2.0
    
    def _wait_if_needed(self):
        """Задержка между запросами"""
        import time
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def search_products(self, query: str, limit: int = 50) -> List[ProductData]:
        """
        Поиск товаров на Яндекс.Маркет
        
        Args:
            query: Поисковый запрос
            limit: Количество товаров
        
        Returns:
            Список товаров
        """
        try:
            self._wait_if_needed()
            
            # URL для поиска
            search_url = f"{self.base_url}/search"
            params = {
                "text": query,
                "local-offers-first": "0"
            }
            
            logger.info(f"Поиск товаров на Яндекс.Маркет: '{query}'")
            
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
            products = []
            
            # Метод 1: Ищем JSON данные в скриптах
            json_data = self._extract_json_from_scripts(soup)
            if json_data:
                products = self._parse_json_data(json_data, limit)
                if products:
                    logger.info(f"Найдено {len(products)} товаров из JSON данных")
                    return products
            
            # Метод 2: Парсим HTML элементы
            products = self._parse_html_elements(soup, limit)
            
            logger.info(f"Успешно распарсено {len(products)} товаров")
            return products
            
        except Exception as e:
            logger.error(f"Ошибка поиска товаров: {e}", exc_info=True)
            return []
    
    def _extract_json_from_scripts(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Извлечение JSON данных из script тегов"""
        try:
            scripts = soup.find_all('script')
            for script in scripts:
                script_text = script.string
                if not script_text:
                    continue
                
                # Ищем JSON данные
                # Вариант 1: window.__INITIAL_STATE__
                if '__INITIAL_STATE__' in script_text or 'window.__' in script_text:
                    # Пробуем извлечь JSON
                    json_match = re.search(r'\{.*\}', script_text, re.DOTALL)
                    if json_match:
                        try:
                            data = json.loads(json_match.group(0))
                            return data
                        except:
                            pass
                
                # Вариант 2: Ищем любые большие JSON объекты
                if len(script_text) > 1000 and '{' in script_text:
                    # Пробуем найти JSON
                    try:
                        # Ищем объекты с products или offers
                        if 'product' in script_text.lower() or 'offer' in script_text.lower():
                            json_match = re.search(r'\{[^{}]*"product[s]?":\s*\[.*?\][^{}]*\}', script_text, re.DOTALL)
                            if json_match:
                                data = json.loads(json_match.group(0))
                                return data
                    except:
                        pass
            
            return None
        except Exception as e:
            logger.debug(f"Ошибка извлечения JSON: {e}")
            return None
    
    def _parse_json_data(self, data: Dict, limit: int) -> List[ProductData]:
        """Парсинг JSON данных"""
        products = []
        try:
            # Пробуем разные структуры JSON
            # Это зависит от структуры данных Яндекс.Маркет
            # Нужно адаптировать под реальную структуру
            
            # Примерная структура (нужно проверить реальную)
            if 'products' in data:
                items = data['products']
            elif 'offers' in data:
                items = data['offers']
            elif 'results' in data:
                items = data['results']
            else:
                return []
            
            for item in items[:limit]:
                try:
                    product = self._parse_json_item(item)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.debug(f"Ошибка парсинга JSON элемента: {e}")
                    continue
            
        except Exception as e:
            logger.debug(f"Ошибка парсинга JSON: {e}")
        
        return products
    
    def _parse_json_item(self, item: Dict) -> Optional[ProductData]:
        """Парсинг одного элемента из JSON"""
        try:
            title = item.get('name') or item.get('title') or item.get('productName', '')
            price = item.get('price') or item.get('salePrice') or item.get('priceU', 0)
            
            # Если цена в копейках
            if isinstance(price, int) and price > 10000:
                price = price / 100
            
            if not title or price == 0:
                return None
            
            brand = item.get('brand') or item.get('vendor', '')
            model = item.get('model') or ''
            url = item.get('url') or item.get('link', '')
            image = item.get('image') or item.get('picture', '')
            product_id = str(item.get('id') or item.get('productId') or '')
            
            if url and not url.startswith('http'):
                url = self.base_url + url
            
            return ProductData(
                title=title,
                brand=brand,
                model=model,
                price=float(price),
                shop_name="Яндекс.Маркет",
                url=url,
                image=image,
                description=item.get('description', ''),
                product_id=product_id
            )
        except Exception as e:
            logger.debug(f"Ошибка парсинга JSON элемента: {e}")
            return None
    
    def _parse_html_elements(self, soup: BeautifulSoup, limit: int) -> List[ProductData]:
        """Парсинг HTML элементов (fallback)"""
        products = []
        
        # Ищем элементы с data-zone-name="productSnippet"
        product_cards = soup.find_all(attrs={"data-zone-name": "productSnippet"})
        
        if not product_cards:
            # Альтернативный поиск
            product_cards = soup.find_all('article')
        
        logger.info(f"Найдено {len(product_cards)} HTML элементов товаров")
        
        for card in product_cards[:limit]:
            try:
                product = self._parse_html_card(card)
                if product:
                    products.append(product)
            except Exception as e:
                logger.debug(f"Ошибка парсинга HTML карточки: {e}")
                continue
        
        return products
    
    def _parse_html_card(self, card) -> Optional[ProductData]:
        """Парсинг HTML карточки товара"""
        try:
            # Название
            title_elem = card.find(['h3', 'a', 'span'], class_=lambda x: x and ('title' in str(x).lower() or 'name' in str(x).lower()))
            if not title_elem:
                title_elem = card.find('a', href=lambda x: x and '/product/' in str(x))
            
            title = title_elem.get_text(strip=True) if title_elem else None
            
            # Цена
            price_elem = card.find(['span', 'div'], class_=lambda x: x and 'price' in str(x).lower())
            if not price_elem:
                price_text = card.find(string=lambda x: x and '₽' in str(x))
                if price_text:
                    price_elem = price_text.parent
            
            price_text = price_elem.get_text(strip=True) if price_elem else "0"
            price = self._extract_price(price_text)
            
            # URL
            url_elem = card.find('a', href=lambda x: x and '/product/' in str(x))
            url = url_elem['href'] if url_elem and url_elem.get('href') else None
            if url and not url.startswith('http'):
                url = self.base_url + url
            
            # Изображение
            img_elem = card.find('img')
            image = None
            if img_elem:
                image = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy-src')
            
            if not title or price == 0:
                return None
            
            brand, model = self._extract_brand_model(title)
            
            return ProductData(
                title=title,
                brand=brand,
                model=model,
                price=price,
                shop_name="Яндекс.Маркет",
                url=url or "",
                image=image or "",
                description="",
                product_id=self._extract_product_id(url) if url else ""
            )
            
        except Exception as e:
            logger.debug(f"Ошибка парсинга HTML карточки: {e}")
            return None
    
    def _extract_price(self, price_text: str) -> float:
        """Извлечение цены из текста"""
        try:
            import re
            price_clean = re.sub(r'[^\d,.]', '', price_text.replace(' ', '').replace(',', '.'))
            if price_clean:
                return float(price_clean)
        except:
            pass
        return 0.0
    
    def _extract_brand_model(self, title: str) -> tuple:
        """Извлечение бренда и модели"""
        if not title:
            return "", ""
        parts = title.split()
        if len(parts) > 0:
            brand = parts[0]
            model = " ".join(parts[1:3]) if len(parts) > 1 else ""
            return brand, model
        return "", ""
    
    def _extract_product_id(self, url: str) -> str:
        """Извлечение ID товара из URL"""
        if not url:
            return ""
        try:
            import re
            match = re.search(r'/product/(\d+)', url)
            if match:
                return match.group(1)
        except:
            pass
        return ""
    
    def get_popular_phones(self, limit: int = 3) -> List[ProductData]:
        """Получение популярных смартфонов"""
        return self.search_products("смартфон", limit=limit)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    parser = YandexMarketProvider()
    
    print("Тест поиска товаров на Яндекс.Маркет...")
    products = parser.search_products("смартфон", limit=5)
    
    print(f"\nНайдено товаров: {len(products)}")
    for i, product in enumerate(products, 1):
        print(f"\n{i}. {product.title}")
        print(f"   Бренд: {product.brand}, Модель: {product.model}")
        print(f"   Цена: {product.price} руб.")
        print(f"   URL: {product.url}")

