"""
Парсер Яндекс.Маркет с использованием Selenium
Для загрузки JavaScript-контента
"""
import logging
import time
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException

try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

from data_providers import ProductData

logger = logging.getLogger(__name__)


def find_chrome_binary():
    """Автоматический поиск Chrome"""
    import os
    possible_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
    ]
    
    chrome_path = os.getenv("CHROME_BIN") or os.getenv("GOOGLE_CHROME_BIN")
    if chrome_path and os.path.exists(chrome_path):
        return chrome_path
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Chrome найден: {path}")
            return path
    
    return None


class YandexMarketSeleniumParser:
    """Парсер Яндекс.Маркет с использованием Selenium"""
    
    def __init__(self, headless: bool = True):
        self.base_url = "https://market.yandex.ru"
        self.provider_name = "Яндекс.Маркет"
        self.headless = headless
    
    def _create_driver(self):
        """Создание нового WebDriver (каждый раз новый)"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            chrome_binary = find_chrome_binary()
            if chrome_binary:
                chrome_options.binary_location = chrome_binary
                logger.info(f"Используется Chrome: {chrome_binary}")
            
            if WEBDRIVER_MANAGER_AVAILABLE:
                try:
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                except Exception as e:
                    logger.warning(f"Не удалось использовать webdriver_manager: {e}. Пробуем системный chromedriver...")
                    driver = webdriver.Chrome(options=chrome_options)
            else:
                driver = webdriver.Chrome(options=chrome_options)
            
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Selenium WebDriver создан успешно")
            return driver
        except Exception as e:
            logger.error(f"Ошибка создания WebDriver: {e}")
            raise
    
    def search_products(self, query: str, limit: int = 50) -> List[ProductData]:
        """Поиск товаров на Яндекс.Маркет"""
        driver = None
        try:
            # Создаем новый драйвер для каждого запроса
            driver = self._create_driver()
            url = f"{self.base_url}/search?text={query}"
            
            logger.info(f"Открываем страницу: {url}")
            driver.get(url)
            
            # Ждем загрузки контента
            wait = WebDriverWait(driver, 20)
            try:
                # Ждем появления карточек товаров
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-zone-name='productSnippet']")))
                logger.info("Карточки товаров загружены")
            except TimeoutException:
                logger.warning("Таймаут ожидания загрузки товаров")
            
            # Даем время на полную загрузку JavaScript
            time.sleep(3)
            
            products = []
            
            # Ищем карточки товаров
            product_cards = driver.find_elements(By.CSS_SELECTOR, "[data-zone-name='productSnippet']")
            
            if not product_cards:
                # Альтернативные селекторы
                product_cards = driver.find_elements(By.CSS_SELECTOR, "article, [class*='product'], [class*='snippet']")
            
            logger.info(f"Найдено {len(product_cards)} карточек товаров")
            
            for card in product_cards[:limit]:
                try:
                    product = self._parse_product_card(card)
                    if product:
                        products.append(product)
                except Exception as e:
                    logger.debug(f"Ошибка парсинга карточки: {e}")
                    continue
            
            logger.info(f"Успешно распарсено {len(products)} товаров")
            return products
            
        except WebDriverException as e:
            logger.error(f"Ошибка WebDriver: {e}")
            return []
        except Exception as e:
            logger.error(f"Ошибка парсинга: {e}", exc_info=True)
            return []
        finally:
            # Всегда закрываем драйвер после использования
            if driver:
                try:
                    driver.quit()
                    logger.debug("WebDriver закрыт")
                except Exception as e:
                    logger.debug(f"Ошибка при закрытии WebDriver: {e}")
    
    def _parse_product_card(self, card) -> Optional[ProductData]:
        """Парсинг одной карточки товара"""
        try:
            # Получаем весь текст карточки для анализа
            card_text = card.text
            
            # Название - ищем ссылку на товар
            title = ""
            url = None
            try:
                # Ищем ссылку на товар (обычно содержит название)
                link = card.find_element(By.CSS_SELECTOR, "a[href*='/product/']")
                url = link.get_attribute('href')
                title = link.get_attribute('title') or link.text.strip()
                
                # Если title пустой, пробуем найти в других элементах
                if not title or len(title) < 5:
                    try:
                        # Ищем в h3, h4 или элементах с классом title/name
                        title_elem = card.find_element(By.CSS_SELECTOR, "h3, h4, [class*='title'], [class*='name']")
                        title = title_elem.text.strip()
                    except:
                        # Берем первую строку текста, которая длиннее 10 символов
                        lines = card_text.split('\n')
                        for line in lines:
                            line = line.strip()
                            if len(line) > 10 and not any(x in line.lower() for x in ['₽', 'руб', 'купить', 'в корзину']):
                                title = line
                                break
            except:
                # Fallback - берем первую длинную строку
                lines = card_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if len(line) > 10 and not any(x in line.lower() for x in ['₽', 'руб', 'купить', 'в корзину', 'оригинал', 'ниже рынка']):
                        title = line
                        break
            
            # Цена - ищем числа с символом ₽
            price = 0.0
            try:
                import re
                # Ищем все элементы с ценами
                price_elements = card.find_elements(By.XPATH, ".//*[contains(text(), '₽') or contains(text(), 'руб')]")
                
                for price_elem in price_elements:
                    price_text = price_elem.text
                    # Ищем число в тексте
                    match = re.search(r'(\d[\d\s]*[\.,]?\d*)', price_text.replace(' ', '').replace(',', '.'))
                    if match:
                        try:
                            price_value = float(match.group(1))
                            # Цена должна быть разумной (больше 1000 для смартфонов)
                            if price_value > 1000:
                                price = price_value
                                break
                        except:
                            continue
                
                # Если не нашли, ищем в тексте карточки
                if price == 0:
                    price_match = re.search(r'(\d[\d\s]{3,}[\.,]?\d*)\s*₽', card_text.replace(' ', ''))
                    if price_match:
                        try:
                            price = float(price_match.group(1).replace(' ', '').replace(',', '.'))
                        except:
                            pass
            except Exception as e:
                logger.debug(f"Ошибка извлечения цены: {e}")
            
            # URL - ищем более тщательно
            if not url:
                try:
                    # Пробуем разные селекторы для ссылок
                    link_selectors = [
                        "a[href*='/product/']",
                        "a[href*='/catalog/']",
                        "a[href*='market.yandex.ru']",
                        "a[href*='yandex.ru']",
                        "a"
                    ]
                    for selector in link_selectors:
                        try:
                            links = card.find_elements(By.CSS_SELECTOR, selector)
                            for link in links:
                                href = link.get_attribute('href')
                                if href:
                                    # Проверяем, что это ссылка на товар
                                    if ('/product/' in href or '/catalog/' in href or 'market.yandex.ru' in href):
                                        # Убеждаемся, что это полный URL
                                        if href.startswith('http'):
                                            url = href
                                        elif href.startswith('/'):
                                            url = f"https://market.yandex.ru{href}"
                                        else:
                                            url = f"https://market.yandex.ru/{href}"
                                        break
                            if url:
                                break
                        except:
                            continue
                except:
                    pass
            
            # Изображение
            image = None
            try:
                img = card.find_element(By.CSS_SELECTOR, "img")
                image = img.get_attribute('src') or img.get_attribute('data-src') or img.get_attribute('data-lazy-src')
            except:
                pass
            
            # Фильтруем невалидные данные
            if not title or len(title) < 5:
                return None
            
            # Исключаем служебные тексты
            invalid_keywords = ['оригинал', 'ниже рынка', 'купить', 'в корзину', 'цена', 'от', 'до']
            if any(keyword in title.lower() for keyword in invalid_keywords):
                return None
            
            if price == 0 or price < 1000:  # Минимальная цена для смартфона
                return None
            
            brand, model = self._extract_brand_model(title)
            product_id = self._extract_product_id(url) if url else ""
            
            return ProductData(
                title=title,
                brand=brand,
                model=model,
                price=price,
                shop_name="Яндекс.Маркет",
                url=url or "",
                image=image or "",
                description="",
                product_id=product_id
            )
            
        except Exception as e:
            logger.debug(f"Ошибка парсинга карточки: {e}")
            return None
    
    def _extract_brand_model(self, title: str) -> tuple:
        """Извлечение бренда и модели"""
        if not title:
            return "", ""
        
        # Убираем слово "Смартфон" из начала
        title_clean = title.replace("Смартфон", "").strip()
        parts = title_clean.split()
        
        if len(parts) == 0:
            return "", ""
        
        # Известные бренды смартфонов
        known_brands = [
            "Apple", "iPhone", "Samsung", "Xiaomi", "Redmi", "Huawei", "Honor",
            "Realme", "Oppo", "Vivo", "OnePlus", "Google", "Pixel", "Nokia",
            "Motorola", "Sony", "Xperia", "TECNO", "iQOO", "POCO", "Nothing"
        ]
        
        # Ищем бренд
        brand = ""
        brand_index = -1
        
        for i, part in enumerate(parts):
            part_upper = part.upper()
            for known_brand in known_brands:
                if known_brand.upper() in part_upper or part_upper in known_brand.upper():
                    brand = known_brand
                    brand_index = i
                    break
            if brand:
                break
        
        # Если бренд не найден, берем первое слово
        if not brand:
            brand = parts[0]
            brand_index = 0
        
        # Модель - следующие 2-3 слова после бренда
        if brand_index >= 0 and len(parts) > brand_index + 1:
            model_parts = parts[brand_index + 1:brand_index + 4]
            model = " ".join(model_parts)
        else:
            model = ""
        
        return brand, model
    
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
    
    # Драйверы теперь создаются и закрываются для каждого запроса,
    # поэтому метод __del__ не нужен


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Тест парсера Яндекс.Маркет с Selenium...")
    print("(Это может занять некоторое время)")
    print()
    
    parser = YandexMarketSeleniumParser(headless=True)
    
    try:
        products = parser.search_products("смартфон", limit=5)
        
        print(f"\nНайдено товаров: {len(products)}")
        for i, product in enumerate(products, 1):
            print(f"\n{i}. {product.title}")
            print(f"   Бренд: {product.brand}, Модель: {product.model}")
            print(f"   Цена: {product.price} руб.")
            print(f"   URL: {product.url}")
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
