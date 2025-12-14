"""
Парсер для получения товаров с Яндекс.Маркет через веб-интерфейс
Используется как альтернатива API, когда Partner API недоступен
"""
import requests
import logging
import re
from typing import List, Optional
from datetime import datetime
from bs4 import BeautifulSoup

from data_providers import ProductData

logger = logging.getLogger(__name__)


class YandexMarketParser:
    """Парсер для получения товаров с Яндекс.Маркет"""
    
    BASE_URL = "https://market.yandex.ru"
    
    def __init__(self, use_selenium: bool = False):
        """
        Инициализация парсера
        
        Args:
            use_selenium: Использовать Selenium для рендеринга JavaScript (требует установки)
        """
        self.use_selenium = use_selenium
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        self.selenium_driver = None
        if use_selenium:
            try:
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                from selenium.webdriver.chrome.service import Service
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                chrome_options = Options()
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_argument(f'user-agent={self.headers["User-Agent"]}')
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                # Пробуем использовать webdriver-manager для автоматической установки драйвера
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    service = Service(ChromeDriverManager().install())
                    self.selenium_driver = webdriver.Chrome(service=service, options=chrome_options)
                    logger.info("✅ Selenium WebDriver инициализирован (с автоматической установкой драйвера)")
                except ImportError:
                    # Если webdriver-manager не установлен, пробуем использовать системный ChromeDriver
                    logger.info("webdriver-manager не найден, пробую использовать системный ChromeDriver")
                    self.selenium_driver = webdriver.Chrome(options=chrome_options)
                    logger.info("✅ Selenium WebDriver инициализирован (используется системный драйвер)")
            except Exception as e:
                logger.warning(f"Selenium недоступен: {e}. Использую обычный парсинг.")
                logger.warning("Для установки Selenium выполните: pip install selenium webdriver-manager")
                logger.warning("Также убедитесь, что установлен Google Chrome")
                self.use_selenium = False
    
    def search_products(self, query: str, limit: int = 10) -> List[ProductData]:
        """
        Поиск товаров на Яндекс.Маркет
        
        Args:
            query: Поисковый запрос
            limit: Количество товаров
        
        Returns:
            Список товаров ProductData
        """
        try:
            # Формируем URL поиска
            search_url = f"{self.BASE_URL}/search"
            params = {
                "text": query,
                "how": "aprice",  # Сортировка по цене (от дешевых к дорогим)
                "local-offers-first": "0",  # Не приоритизировать локальные предложения
                "onstock": "1"  # Только товары в наличии
            }
            
            logger.info(f"🔍 Парсинг товаров с Яндекс.Маркет: запрос '{query}'")
            logger.info(f"   Параметры: сортировка по цене, только в наличии")
            
            html_content = None
            
            # Используем Selenium если доступен
            if self.use_selenium and self.selenium_driver:
                try:
                    logger.info("🌐 Использую Selenium для рендеринга JavaScript...")
                    # Кодируем запрос для URL
                    import urllib.parse
                    encoded_query = urllib.parse.quote(query)
                    full_url = f"{search_url}?text={encoded_query}&how=aprice&local-offers-first=0"
                    logger.info(f"   Открываю URL: {full_url}")
                    
                    self.selenium_driver.get(full_url)
                    
                    # Ждем загрузки контента
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    from selenium.webdriver.common.by import By
                    
                    try:
                        logger.info("   Ожидание загрузки товаров...")
                        WebDriverWait(self.selenium_driver, 15).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-zone-name*='product'], [data-zone-name*='snippet'], [data-zone-name*='offer']"))
                        )
                        logger.info("   Товары загружены")
                    except Exception as e:
                        logger.warning(f"   Таймаут ожидания элементов: {e}, продолжаю...")
                        # Даем еще немного времени на загрузку
                        import time
                        time.sleep(2)
                    
                    html_content = self.selenium_driver.page_source
                    logger.info(f"✅ Страница загружена через Selenium, размер HTML: {len(html_content)} символов")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка Selenium: {e}, пробую обычный запрос", exc_info=True)
            
            # Если Selenium не использовался или не сработал, используем requests
            if not html_content:
                try:
                    import urllib.parse
                    encoded_query = urllib.parse.quote(query)
                    full_url = f"{search_url}?text={encoded_query}&how=aprice&local-offers-first=0"
                    logger.info(f"📡 Отправка HTTP запроса к Яндекс.Маркет...")
                    logger.info(f"   URL: {full_url}")
                    
                    response = requests.get(full_url, headers=self.headers, timeout=20, allow_redirects=True)
                    
                    if response.status_code != 200:
                        logger.error(f"❌ Ошибка при запросе: HTTP {response.status_code}")
                        logger.error(f"   Ответ сервера (первые 500 символов): {response.text[:500]}")
                        return []
                    
                    html_content = response.text
                    logger.info(f"✅ Получен HTML контент, размер: {len(html_content)} символов")
                    
                    # Проверяем, не вернулась ли капча или блокировка
                    if 'captcha' in html_content.lower() or 'робот' in html_content.lower():
                        logger.warning("⚠️ Возможно, Яндекс.Маркет требует капчу. Рекомендуется использовать Selenium.")
                    if len(html_content) < 1000:
                        logger.warning(f"⚠️ Получен очень короткий HTML ({len(html_content)} символов), возможно, страница не загрузилась")
                except requests.exceptions.Timeout:
                    logger.error("Таймаут при запросе к Яндекс.Маркет")
                    return []
                except requests.exceptions.ConnectionError as e:
                    logger.error(f"Ошибка подключения к Яндекс.Маркет: {e}")
                    return []
                except requests.exceptions.RequestException as e:
                    logger.error(f"Ошибка запроса к Яндекс.Маркет: {e}")
                    return []
            
            # Парсим HTML
            if not html_content or len(html_content) < 100:
                logger.warning("Получен пустой или слишком короткий HTML контент")
                return []
            
            soup = BeautifulSoup(html_content, 'html.parser')
            products = []
            
            logger.info(f"HTML распарсен, ищем товары...")
            
            # Метод 1: Поиск данных в JSON (часто Яндекс.Маркет встраивает данные в script теги)
            json_products = self._extract_from_json(soup)
            if json_products:
                logger.info(f"Найдено {len(json_products)} товаров в JSON данных")
                products.extend(json_products[:limit])
            
            # Метод 2: Поиск в HTML структуре
            product_elements = []
            if len(products) < limit:
                product_elements = self._find_product_elements(soup)
                logger.info(f"Найдено {len(product_elements)} элементов товаров в HTML")
            
            # Парсим элементы товаров из HTML
            parsed_count = 0
            failed_count = 0
            for element in product_elements[:limit * 2]:  # Пробуем больше элементов, т.к. не все могут распарситься
                try:
                    product = self._parse_product_element(element, query)
                    if product:
                        if product not in products:  # Избегаем дубликатов
                            products.append(product)
                            parsed_count += 1
                            logger.debug(f"Успешно распарсен товар: {product.title[:50]}")
                        if len(products) >= limit:
                            break
                    else:
                        failed_count += 1
                except Exception as e:
                    failed_count += 1
                    logger.debug(f"Ошибка парсинга элемента товара: {e}")
                    continue
            
            if parsed_count == 0 and failed_count > 0:
                logger.warning(f"Найдено {len(product_elements)} элементов, но не удалось распарсить ни одного")
                logger.warning("Возможные причины:")
                logger.warning("  1. Изменилась структура HTML Яндекс.Маркет")
                logger.warning("  2. Элементы не содержат необходимых данных (название, цена)")
                logger.warning("  3. Требуется JavaScript для загрузки данных (нужен Selenium)")
            
            # Удаляем дубликаты по названию
            seen_titles = set()
            unique_products = []
            for product in products:
                if product.title not in seen_titles:
                    seen_titles.add(product.title)
                    unique_products.append(product)
            products = unique_products
            
            if products:
                logger.info(f"✅ Успешно распарсено {len(products)} товаров")
            else:
                logger.warning("=" * 80)
                logger.warning("⚠️ Не удалось найти товары на странице. Возможные причины:")
                logger.warning("   1. Изменилась структура HTML Яндекс.Маркет")
                logger.warning("   2. Страница требует JavaScript (нужен Selenium)")
                logger.warning("   3. Блокировка запросов со стороны Яндекс.Маркет")
                logger.warning("   4. Страница возвращает капчу или требует авторизацию")
                logger.warning("=" * 80)
                
                # Логируем информацию для отладки
                logger.debug(f"Размер HTML: {len(html_content)} символов")
                logger.debug(f"Найдено элементов для парсинга: {len(product_elements)}")
                
                # Сохраняем HTML для отладки (первые 5000 символов)
                if len(html_content) > 0:
                    logger.debug(f"HTML контент (первые 5000 символов):\n{html_content[:5000]}")
                    
                    # Пробуем найти ключевые слова в HTML
                    if 'product' in html_content.lower():
                        logger.debug("✅ В HTML найдено слово 'product'")
                    if 'offer' in html_content.lower():
                        logger.debug("✅ В HTML найдено слово 'offer'")
                    if 'snippet' in html_content.lower():
                        logger.debug("✅ В HTML найдено слово 'snippet'")
                    if 'data-zone-name' in html_content:
                        logger.debug("✅ В HTML найдены data-zone-name атрибуты")
                    else:
                        logger.warning("⚠️ В HTML НЕ найдены data-zone-name атрибуты - возможно, структура изменилась")
            
            return products
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к Яндекс.Маркет: {e}")
            return []
        except Exception as e:
            logger.error(f"Ошибка парсинга: {e}", exc_info=True)
            return []
        finally:
            # Закрываем Selenium если использовали
            if self.use_selenium and self.selenium_driver:
                try:
                    self.selenium_driver.quit()
                except:
                    pass
    
    def _extract_from_json(self, soup: BeautifulSoup) -> List[ProductData]:
        """Извлечение товаров из JSON данных, встроенных в HTML"""
        products = []
        try:
            import json
            
            # Ищем script теги с JSON данными
            scripts = soup.find_all('script', type='application/json')
            scripts.extend(soup.find_all('script', string=re.compile(r'window\.__INITIAL_STATE__|__APP_DATA__|products|offers', re.I)))
            
            for script in scripts:
                try:
                    # Пробуем извлечь JSON
                    if script.string:
                        # Ищем JSON объекты в тексте
                        json_matches = re.findall(r'\{[^{}]*"products"[^{}]*\}', script.string, re.DOTALL)
                        for match in json_matches:
                            try:
                                data = json.loads(match)
                                # Пробуем найти товары в структуре
                                if 'products' in data:
                                    for item in data['products']:
                                        product = self._parse_json_product(item)
                                        if product:
                                            products.append(product)
                            except:
                                continue
                except:
                    continue
            
            # Также пробуем найти данные в data-атрибутах
            data_attrs = soup.find_all(attrs={"data-state": True})
            for elem in data_attrs:
                try:
                    state = json.loads(elem.get('data-state', '{}'))
                    if 'products' in state or 'offers' in state:
                        items = state.get('products', state.get('offers', []))
                        for item in items:
                            product = self._parse_json_product(item)
                            if product:
                                products.append(product)
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Ошибка извлечения из JSON: {e}")
        
        return products
    
    def _parse_json_product(self, item: dict) -> Optional[ProductData]:
        """Парсинг товара из JSON структуры"""
        try:
            title = item.get('name') or item.get('title') or item.get('offerName', '')
            if not title:
                return None
            
            # Цена
            price = 0
            price_data = item.get('price', {})
            if isinstance(price_data, dict):
                price = float(price_data.get('value', 0) or price_data.get('amount', 0))
            elif price_data:
                price = float(price_data)
            
            if price <= 0:
                return None
            
            # URL
            url = item.get('url') or item.get('link') or item.get('offerUrl', '')
            if url and not url.startswith('http'):
                url = f"{self.BASE_URL}{url}" if url.startswith('/') else f"{self.BASE_URL}/{url}"
            
            # Изображение
            image = ""
            if 'pictures' in item and item['pictures']:
                image = item['pictures'][0].get('url', '') or item['pictures'][0].get('original', '')
            elif 'image' in item:
                image = item['image']
            
            # Бренд и модель
            brand = item.get('vendor', {}).get('name', '') if isinstance(item.get('vendor'), dict) else (item.get('vendor') or '')
            model = item.get('model', {}).get('name', '') if isinstance(item.get('model'), dict) else (item.get('model') or '')
            
            # Если нет бренда, извлекаем из названия
            if not brand:
                common_brands = ["Samsung", "Apple", "Xiaomi", "Huawei", "OnePlus", "Google", "Sony", "LG", "ASUS", "Lenovo"]
                for b in common_brands:
                    if b.lower() in title.lower():
                        brand = b
                        break
            
            return ProductData(
                title=title,
                brand=brand or "Не указан",
                model=model or "Не указана",
                price=price,
                shop_name="Яндекс.Маркет",
                url=url or f"{self.BASE_URL}/search",
                image=image,
                description=item.get('description', ''),
                product_id=str(item.get('id', '')),
                scraped_at=datetime.utcnow()
            )
        except Exception as e:
            logger.debug(f"Ошибка парсинга JSON товара: {e}")
            return None
    
    def _find_product_elements(self, soup: BeautifulSoup) -> List:
        """Поиск элементов товаров в HTML"""
        elements = []
        
        # Метод 1: Поиск по data-атрибутам (современная структура Яндекс.Маркет)
        # Используем тот же подход, что и yandex_market_oauth_api
        data_zone_elements = soup.find_all(attrs={"data-zone-name": lambda x: x and "product" in x.lower()})
        if data_zone_elements:
            logger.info(f"Найдено {len(data_zone_elements)} элементов по data-zone-name")
            elements.extend(data_zone_elements)
        
        # Метод 2: Поиск по классам (div и article с классами product/offer/card)
        class_elements = soup.find_all(['div', 'article'], class_=lambda x: x and (
            'product' in x.lower() or 'offer' in x.lower() or 'card' in x.lower() or 
            'snippet' in x.lower() or 'item' in x.lower()
        ))
        if class_elements:
            logger.info(f"Найдено {len(class_elements)} элементов по классам")
            elements.extend(class_elements)
        
        # Метод 3: Поиск по data-атрибутам с более широким паттерном
        data_elements = soup.find_all(attrs={"data-zone-name": re.compile(r"product|offer|snippet", re.I)})
        if data_elements:
            logger.info(f"Найдено {len(data_elements)} элементов по data-zone-name (расширенный поиск)")
            elements.extend(data_elements)
        
        # Метод 4: Поиск по структуре (div с ссылкой и ценой внутри)
        # Ищем div, которые содержат ссылку и элемент с ценой
        structural_elements = []
        for div in soup.find_all('div'):
            has_link = div.find('a', href=True)
            has_price = div.find(string=re.compile(r'[\d\s]+₽|[\d\s]+руб', re.I))
            if has_link and has_price:
                structural_elements.append(div)
        if structural_elements:
            logger.info(f"Найдено {len(structural_elements)} элементов по структуре (ссылка + цена)")
            elements.extend(structural_elements)
        
        # Удаляем дубликаты
        seen = set()
        unique_elements = []
        for elem in elements:
            elem_id = id(elem)
            if elem_id not in seen:
                seen.add(elem_id)
                unique_elements.append(elem)
        
        logger.info(f"Итого найдено {len(unique_elements)} уникальных элементов товаров")
        return unique_elements
    
    def _parse_product_element(self, element, query: str) -> Optional[ProductData]:
        """Парсинг одного элемента товара"""
        try:
            # Название товара - пробуем разные способы
            title = ""
            
            # Способ 1: Поиск в data-zone-name="title"
            title_elem = element.find(attrs={"data-zone-name": re.compile(r"title|name", re.I)})
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            # Способ 2: Поиск ссылки с текстом
            if not title:
                link_elem = element.find('a', href=True)
                if link_elem:
                    title = link_elem.get_text(strip=True)
                    # Если в ссылке нет текста, пробуем найти текст в дочерних элементах
                    if not title or len(title) < 3:
                        title_elem_in_link = link_elem.find(['span', 'div', 'h3', 'h4'], class_=re.compile(r'title|name', re.I))
                        if title_elem_in_link:
                            title = title_elem_in_link.get_text(strip=True)
            
            # Способ 3: Поиск заголовков
            if not title or len(title) < 3:
                for tag in ['h3', 'h4', 'h2']:
                    title_elem = element.find(tag)
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        if title and len(title) >= 3:
                            break
            
            # Способ 4: Поиск по классам
            if not title or len(title) < 3:
                title_elem = (
                    element.find('span', class_=re.compile(r'title|name', re.I)) or
                    element.find('div', class_=re.compile(r'title|name', re.I))
                )
                if title_elem:
                    title = title_elem.get_text(strip=True)
            
            # Способ 5: Из атрибутов
            if not title or len(title) < 3:
                title = element.get('aria-label', '') or element.get('title', '') or element.get('data-title', '')
            
            if not title or len(title) < 3:
                logger.debug(f"Не удалось найти название товара в элементе")
                return None
            
            # Цена - пробуем разные способы
            price = 0
            
            # Способ 1: Поиск в data-zone-name="price"
            price_elem = element.find(attrs={"data-zone-name": re.compile(r"price", re.I)})
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'[\d\s]+', price_text.replace(' ', '').replace('\u2009', '').replace(',', ''))
                if price_match:
                    try:
                        price = float(price_match.group().replace(' ', '').replace('\u2009', '').replace(',', ''))
                    except ValueError:
                        pass
            
            # Способ 2: Поиск по классам
            if price <= 0:
                price_elem = (
                    element.find('span', class_=re.compile(r'price', re.I)) or
                    element.find('div', class_=re.compile(r'price', re.I)) or
                    element.find('span', class_=re.compile(r'value|amount', re.I))
                )
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    # Извлекаем число из цены (поддерживаем разные форматы)
                    price_match = re.search(r'[\d\s,]+', price_text.replace(' ', '').replace('\u2009', '').replace(',', ''))
                    if price_match:
                        try:
                            price = float(price_match.group().replace(' ', '').replace('\u2009', '').replace(',', ''))
                        except ValueError:
                            pass
            
            # Способ 3: Поиск текста с рублями/₽ в элементе
            if price <= 0:
                price_text_elem = element.find(string=re.compile(r'[\d\s]+₽|[\d\s]+руб', re.I))
                if price_text_elem:
                    price_text = price_text_elem.strip()
                    price_match = re.search(r'[\d\s]+', price_text.replace(' ', '').replace('\u2009', '').replace(',', ''))
                    if price_match:
                        try:
                            price = float(price_match.group().replace(' ', '').replace('\u2009', '').replace(',', ''))
                        except ValueError:
                            pass
            
            if price <= 0:
                logger.debug(f"Не удалось найти цену для товара: {title[:50]}")
                return None
            
            # URL товара
            url = ""
            link_elem = element.find('a', href=True)
            if link_elem:
                url = link_elem.get('href', '')
                if url and not url.startswith('http'):
                    url = f"{self.BASE_URL}{url}" if url.startswith('/') else f"{self.BASE_URL}/{url}"
            
            if not url:
                # Формируем URL поиска как fallback
                url = f"{self.BASE_URL}/search?text={query}"
            
            # Изображение
            image = ""
            img_elem = (
                element.find('img', src=True) or
                element.find('img', data_src=True) or
                element.find('img', data_lazy_src=True)
            )
            if img_elem:
                image = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy-src', '')
                if image and not image.startswith('http'):
                    image = f"https:{image}" if image.startswith('//') else image
            
            # Бренд и модель из названия
            brand = ""
            model = ""
            
            # Список популярных брендов
            common_brands = [
                "Samsung", "Apple", "Xiaomi", "Huawei", "OnePlus", "Google", "Sony", "LG", 
                "ASUS", "Lenovo", "Honor", "Realme", "Oppo", "Vivo", "Nokia", "Motorola",
                "JBL", "Sennheiser", "Bose", "AirPods", "Beats", "HyperX", "Razer"
            ]
            
            title_lower = title.lower()
            for b in common_brands:
                if b.lower() in title_lower:
                    brand = b
                    # Пытаемся извлечь модель после бренда
                    brand_pos = title_lower.find(b.lower())
                    if brand_pos >= 0:
                        model_part = title[brand_pos + len(b):].strip()
                        # Берем первые слова как модель
                        model_words = model_part.split()[:3]
                        model = ' '.join(model_words).strip()
                    break
            
            # Если бренд не найден, пробуем извлечь из начала названия
            words = title.split()  # Определяем words заранее
            if not brand and words:
                first_word = words[0]
                # Проверяем, может это бренд
                if any(b.lower() == first_word.lower() for b in common_brands):
                    brand = first_word
                    model = ' '.join(words[1:4]) if len(words) > 1 else ""
            
            # Если все еще нет бренда, используем первое слово как бренд
            if not brand and words:
                brand = words[0]
                model = ' '.join(words[1:4]) if len(words) > 1 else ""
            
            return ProductData(
                title=title,
                brand=brand or "Не указан",
                model=model or "Не указана",
                price=price,
                shop_name="Яндекс.Маркет",
                url=url,
                image=image,
                description="",
                product_id="",
                scraped_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.debug(f"Ошибка парсинга элемента: {e}")
            return None
    
    def get_popular_products(self, category: str = "электроника", limit: int = 10) -> List[ProductData]:
        """
        Получение популярных товаров
        
        Args:
            category: Категория товаров
            limit: Количество товаров
        
        Returns:
            Список популярных товаров
        """
        search_queries = {
            "электроника": ["смартфон", "телефон"],
            "компьютеры": ["ноутбук", "компьютер"],
            "аудио": ["наушники", "колонка"]
        }
        
        query = search_queries.get(category, ["смартфон"])[0]
        return self.search_products(query=query, limit=limit)

