"""
Клиент для работы с Яндекс.Маркет OAuth API (для разработчиков)
Документация: https://yandex.ru/dev/market/partner-api/doc/ru/
"""
import requests
import logging
from typing import List, Optional, Dict
from datetime import datetime

from data_providers import ProductData

logger = logging.getLogger(__name__)


class YandexMarketOAuthAPI:
    """Клиент для работы с Яндекс.Маркет OAuth API"""
    
    BASE_URL = "https://api.partner.market.yandex.ru"
    
    def __init__(self, oauth_token: str, campaign_id: Optional[str] = None):
        """
        Инициализация клиента
        
        Args:
            oauth_token: OAuth токен разработчика
            campaign_id: ID кампании (опционально, можно получить автоматически)
        """
        self.oauth_token = oauth_token
        self.campaign_id = campaign_id
        self.headers = {
            "Authorization": f"OAuth {oauth_token}",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, json_data: Optional[Dict] = None) -> Optional[Dict]:
        """Выполнение HTTP запроса к API"""
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=json_data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                logger.error("Ошибка авторизации: неверный OAuth токен")
                logger.error(f"Проверьте YANDEX_OAUTH_TOKEN в .env файле")
                return None
            elif response.status_code == 403:
                logger.error("Ошибка доступа: недостаточно прав")
                logger.error(f"Убедитесь, что у приложения есть право market:partner-api")
                return None
            elif response.status_code == 404:
                logger.warning(f"Endpoint не найден: {endpoint}. Пробую альтернативный метод.")
                return None
            else:
                logger.warning(f"Ошибка API: {response.status_code} - {response.text[:200]}")
                logger.debug(f"Полный ответ: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к Яндекс.Маркет API: {e}")
            return None
    
    def get_campaigns(self) -> List[Dict]:
        """Получение списка кампаний"""
        response = self._make_request("GET", "/campaigns")
        if response and "campaigns" in response:
            return response["campaigns"]
        return []
    
    def search_products(
        self,
        query: str,
        limit: int = 10,
        category_id: Optional[int] = None,
        campaign_id: Optional[str] = None
    ) -> List[ProductData]:
        """
        Поиск товаров в Яндекс.Маркет
        
        Args:
            query: Поисковый запрос (например, "смартфон", "телефон")
            limit: Количество товаров
            category_id: ID категории (опционально)
            campaign_id: ID кампании (если не указан, используется self.campaign_id)
        
        Returns:
            Список товаров ProductData
        """
        # Для поиска товаров используем endpoint каталога
        # Это позволяет искать товары без привязки к кампании
        # Используем endpoint для поиска в каталоге через Content API
        
        # Параметры запроса
        params = {
            "query": query,
            "count": min(limit, 30),  # API ограничивает до 30 за запрос
            "page": 1
        }
        
        if category_id:
            params["categoryId"] = category_id
        
        # Яндекс.Маркет Partner API не предоставляет публичный поиск по каталогу
        # Для получения товаров используем альтернативный подход:
        # 1. Пробуем получить офферы из кампании (если есть campaign_id)
        # 2. Если нет - используем публичный поиск через веб-интерфейс (парсинг)
        
        cid = campaign_id or self.campaign_id
        if not cid:
            campaigns = self.get_campaigns()
            if campaigns:
                cid = str(campaigns[0].get("id", ""))
                self.campaign_id = cid
                logger.info(f"Автоматически получен campaign_id: {cid}")
        
        response = None
        
        if cid:
            # Пробуем получить офферы из кампании
            endpoint = f"/campaigns/{cid}/offers"
            logger.info(f"Пробую получить офферы из кампании {cid}")
            response = self._make_request("GET", endpoint, params=params)
        
        if not response:
            logger.warning(f"Не удалось получить данные через Partner API по запросу '{query}'")
            logger.info("Примечание: Partner API предназначен для работы с собственными товарами продавца.")
            logger.info("Для поиска товаров в каталоге может потребоваться другой подход.")
            return []
        
        products = []
        
        # Обработка ответа - пробуем разные структуры
        items = []
        
        # Вариант 1: ответ от каталога
        if "searchResults" in response:
            search_results = response.get("searchResults", {})
            items = search_results.get("items", [])
        # Вариант 2: ответ от offers
        elif "offers" in response:
            items = response.get("offers", [])
        # Вариант 3: прямой список
        elif isinstance(response, list):
            items = response
        # Вариант 4: результат в поле result
        elif "result" in response:
            items = response.get("result", [])
        
        for item in items[:limit]:
            try:
                # Извлекаем данные в зависимости от структуры
                entity = item.get("entity", item) if isinstance(item, dict) else item
                
                # Название товара
                title = entity.get("name") or entity.get("title") or entity.get("offerName", "")
                
                # Цена
                price = 0
                price_data = entity.get("price", {})
                if isinstance(price_data, dict):
                    price = float(price_data.get("value", 0) or price_data.get("amount", 0))
                elif price_data:
                    price = float(price_data)
                
                # URL товара
                url = entity.get("url") or entity.get("link", "") or entity.get("offerUrl", "")
                if url and not url.startswith("http"):
                    url = f"https://market.yandex.ru{url}" if url.startswith("/") else f"https://market.yandex.ru/{url}"
                if not url:
                    url = f"https://market.yandex.ru/search?text={query}"
                
                # Бренд и модель
                brand = ""
                model = ""
                
                vendor = entity.get("vendor", {})
                if isinstance(vendor, dict):
                    brand = vendor.get("name", "")
                elif vendor:
                    brand = str(vendor)
                
                model_data = entity.get("model", {})
                if isinstance(model_data, dict):
                    model = model_data.get("name", "")
                elif model_data:
                    model = str(model_data)
                
                # Если бренд не указан, пытаемся извлечь из названия
                if not brand and title:
                    common_brands = ["Samsung", "Apple", "Xiaomi", "Huawei", "OnePlus", "Google", "Sony", "LG", "ASUS", "Lenovo", "Honor", "Realme", "Oppo", "Vivo", "Nokia", "Motorola"]
                    for b in common_brands:
                        if b.lower() in title.lower():
                            brand = b
                            break
                
                # Изображение
                image = ""
                pictures = entity.get("pictures", []) or entity.get("photos", [])
                if pictures:
                    if isinstance(pictures[0], dict):
                        image = pictures[0].get("url", "") or pictures[0].get("original", "") or pictures[0].get("thumbnail", "")
                    else:
                        image = pictures[0]
                
                if image and not image.startswith("http"):
                    image = f"https:{image}" if image.startswith("//") else image
                
                # Описание
                description = entity.get("description", "") or entity.get("shortDescription", "") or entity.get("offerDescription", "")
                
                # ID товара
                product_id = str(entity.get("id", "") or entity.get("offerId", "") or entity.get("entityId", ""))
                
                if title and price > 0:
                    products.append(ProductData(
                        title=title,
                        brand=brand or "Не указан",
                        model=model or "Не указана",
                        price=price,
                        shop_name="Яндекс.Маркет",
                        url=url,
                        image=image,
                        description=description,
                        product_id=product_id,
                        scraped_at=datetime.utcnow()
                    ))
            except Exception as e:
                logger.debug(f"Ошибка обработки товара: {e}, item: {item}")
                continue
        
        logger.info(f"Найдено {len(products)} товаров по запросу '{query}'")
        return products
    
    def get_popular_products(self, category: str = "электроника", limit: int = 10) -> List[ProductData]:
        """
        Получение популярных товаров
        
        Args:
            category: Категория товаров
            limit: Количество товаров
        
        Returns:
            Список популярных товаров
        """
        # Для популярных товаров используем поиск по категории
        # Можно использовать запросы типа "смартфон", "телефон" для электроники
        search_queries = {
            "электроника": ["смартфон", "телефон"],
            "компьютеры": ["ноутбук", "компьютер"],
            "аудио": ["наушники", "колонка"]
        }
        
        query = search_queries.get(category, ["смартфон"])[0]
        products = self.search_products(query=query, limit=limit)
        
        # Если Partner API не вернул товары, используем альтернативный метод
        if not products:
            logger.info(f"Partner API не вернул товары, пробую альтернативный метод для '{query}'")
            products = self._search_via_web(query=query, limit=limit)
        
        return products
    
    def _search_via_web(self, query: str, limit: int = 10) -> List[ProductData]:
        """
        Альтернативный метод поиска товаров через веб-интерфейс
        Используется, если Partner API недоступен
        """
        try:
            import requests
            from bs4 import BeautifulSoup
            
            # URL поиска Яндекс.Маркет
            search_url = f"https://market.yandex.ru/search?text={query}&how=aprice"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            logger.info(f"Парсинг товаров с {search_url}")
            response = requests.get(search_url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                logger.warning(f"Ошибка парсинга: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            products = []
            
            # Поиск товаров в HTML (структура может меняться)
            # Пробуем найти карточки товаров
            product_cards = soup.find_all(['div', 'article'], class_=lambda x: x and ('product' in x.lower() or 'offer' in x.lower() or 'card' in x.lower()))
            
            if not product_cards:
                # Альтернативный поиск по data-атрибутам
                product_cards = soup.find_all(attrs={"data-zone-name": lambda x: x and "product" in x.lower()})
            
            logger.info(f"Найдено {len(product_cards)} карточек товаров в HTML")
            
            for card in product_cards[:limit]:
                try:
                    # Извлекаем данные из карточки
                    title_elem = card.find(['h3', 'a', 'span'], class_=lambda x: x and ('title' in x.lower() or 'name' in x.lower()))
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    price_elem = card.find(['span', 'div'], class_=lambda x: x and 'price' in x.lower())
                    price_text = price_elem.get_text(strip=True) if price_elem else "0"
                    # Извлекаем число из цены
                    import re
                    price_match = re.search(r'[\d\s]+', price_text.replace(' ', ''))
                    price = float(price_match.group().replace(' ', '')) if price_match else 0
                    
                    link_elem = card.find('a', href=True)
                    url = link_elem['href'] if link_elem else ""
                    if url and not url.startswith("http"):
                        url = f"https://market.yandex.ru{url}"
                    
                    img_elem = card.find('img', src=True)
                    image = img_elem['src'] if img_elem else ""
                    
                    if title and price > 0:
                        # Извлекаем бренд из названия
                        brand = ""
                        common_brands = ["Samsung", "Apple", "Xiaomi", "Huawei", "OnePlus", "Google", "Sony", "LG", "ASUS", "Lenovo", "Honor", "Realme", "Oppo", "Vivo", "Nokia", "Motorola"]
                        for b in common_brands:
                            if b.lower() in title.lower():
                                brand = b
                                break
                        
                        products.append(ProductData(
                            title=title,
                            brand=brand or "Не указан",
                            model="Не указана",
                            price=price,
                            shop_name="Яндекс.Маркет",
                            url=url or search_url,
                            image=image,
                            description="",
                            product_id="",
                            scraped_at=datetime.utcnow()
                        ))
                except Exception as e:
                    logger.debug(f"Ошибка обработки карточки товара: {e}")
                    continue
            
            logger.info(f"Парсинг завершен, получено {len(products)} товаров")
            return products
            
        except Exception as e:
            logger.error(f"Ошибка парсинга веб-страницы: {e}", exc_info=True)
            return []

