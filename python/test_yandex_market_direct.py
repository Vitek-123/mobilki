"""
Прямой тест парсинга Яндекс.Маркет
"""
import requests
from bs4 import BeautifulSoup

def test_yandex_market():
    """Тест парсинга страницы Яндекс.Маркет"""
    
    url = "https://market.yandex.ru/search?text=смартфон"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9"
    }
    
    print(f"Запрос к: {url}")
    print()
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Статус: {response.status_code}")
        print(f"Размер ответа: {len(response.text)} символов")
        print()
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Сохраняем HTML для анализа
            with open('yandex_market_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("✅ HTML сохранен в yandex_market_page.html")
            print()
            
            # Пробуем разные селекторы
            print("Поиск товаров...")
            print()
            
            # Вариант 1: data-zone-name
            cards1 = soup.find_all(attrs={"data-zone-name": "productSnippet"})
            print(f"1. data-zone-name='productSnippet': {len(cards1)} элементов")
            
            # Вариант 2: классы с product
            cards2 = soup.find_all(class_=lambda x: x and 'product' in str(x).lower())
            print(f"2. Классы с 'product': {len(cards2)} элементов")
            
            # Вариант 3: ссылки на /product/
            cards3 = soup.find_all('a', href=lambda x: x and '/product/' in str(x))
            print(f"3. Ссылки на '/product/': {len(cards3)} элементов")
            
            # Вариант 4: article теги
            cards4 = soup.find_all('article')
            print(f"4. Теги <article>: {len(cards4)} элементов")
            
            # Вариант 5: div с data-атрибутами
            cards5 = soup.find_all('div', attrs={"data-id": True})
            print(f"5. div с data-id: {len(cards5)} элементов")
            
            print()
            print("Анализ структуры...")
            
            # Ищем любые элементы с ценами
            price_elements = soup.find_all(string=lambda x: x and '₽' in str(x))
            print(f"Элементов с символом ₽: {len(price_elements)}")
            
            if price_elements:
                print("\nПримеры цен:")
                for i, price in enumerate(price_elements[:5], 1):
                    print(f"  {i}. {price.strip()[:50]}")
            
            # Ищем заголовки
            titles = soup.find_all(['h1', 'h2', 'h3', 'h4'])
            print(f"\nЗаголовков (h1-h4): {len(titles)}")
            if titles:
                print("\nПримеры заголовков:")
                for i, title in enumerate(titles[:5], 1):
                    text = title.get_text(strip=True)
                    if text:
                        print(f"  {i}. {text[:80]}")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_yandex_market()

