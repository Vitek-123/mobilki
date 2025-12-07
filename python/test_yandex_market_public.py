"""
Тест публичного API Яндекс.Маркет (без OAuth)
"""
import requests
import json

def test_yandex_market_public_api():
    """Тестирование публичного API Яндекс.Маркет"""
    
    print("=" * 60)
    print("Тест публичного API Яндекс.Маркет")
    print("=" * 60)
    print()
    
    # Публичный API - не требует токена
    url = "https://api.content.market.yandex.ru/v1/search.json"
    
    params = {
        "text": "смартфон",
        "geo_id": 213,  # Москва
        "page": 1,
        "count": 10
    }
    
    print(f"URL: {url}")
    print(f"Параметры: {params}")
    print()
    
    try:
        response = requests.get(url, params=params, timeout=15)
        
        print(f"Статус код: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Успешный ответ!")
            print()
            
            # Показываем структуру ответа
            print("Структура ответа:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])
            print()
            
            # Проверяем наличие товаров
            if "results" in data:
                results = data["results"]
                print(f"Найдено результатов: {len(results)}")
                
                if results:
                    print("\nПервый товар:")
                    first_item = results[0]
                    print(f"  Название: {first_item.get('name', 'N/A')}")
                    print(f"  Цена: {first_item.get('price', {}).get('value', 'N/A')} руб.")
                    print(f"  URL: {first_item.get('url', 'N/A')}")
            
        else:
            print(f"❌ Ошибка: статус {response.status_code}")
            print(f"Ответ: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    test_yandex_market_public_api()

