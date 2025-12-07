"""
Тест API Яндекс.Маркет с OAuth токеном
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Загружаем токен из .env
OAUTH_TOKEN = os.getenv("YANDEX_MARKET_OAUTH_TOKEN")
CLIENT_ID = "5c11d50c52304b16b6c07fbb6b5382d8"

def test_market_api():
    """Тестирование API Яндекс.Маркет"""
    
    print("=" * 60)
    print("Тест API Яндекс.Маркет")
    print("=" * 60)
    print()
    
    if not OAUTH_TOKEN:
        print("❌ OAuth токен не найден в .env файле")
        print("Запустите сначала: python get_yandex_market_token.py")
        return
    
    print(f"Client ID: {CLIENT_ID}")
    print(f"OAuth Token: {OAUTH_TOKEN[:20]}...")
    print()
    
    # Заголовки для запроса
    headers = {
        "Authorization": f"OAuth {OAUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Попробуем разные эндпоинты API
    
    # Вариант 1: Content API
    print("Тест 1: Content API (поиск товаров)")
    print("-" * 60)
    try:
        url = "https://api.content.market.yandex.ru/v1/search.json"
        params = {
            "text": "смартфон",
            "geo_id": 213,  # Москва
            "page": 1,
            "count": 5
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Успешно!")
            print(f"Данные: {str(data)[:500]}...")
        else:
            print(f"❌ Ошибка: {response.text[:500]}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print()
    
    # Вариант 2: Partner API (может потребоваться campaign ID)
    print("Тест 2: Partner API")
    print("-" * 60)
    print("Для Partner API нужен campaign ID из личного кабинета")
    print("Пропускаем этот тест")
    
    print()
    print("=" * 60)
    print("Если Content API не работает, попробуйте:")
    print("1. Проверить, что токен действителен")
    print("2. Использовать парсинг HTML страниц")
    print("3. Зарегистрироваться в партнерской программе для API-Key")
    print("=" * 60)

if __name__ == "__main__":
    test_market_api()

