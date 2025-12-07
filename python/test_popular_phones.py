"""
Тестовый скрипт для проверки эндпоинта популярных телефонов
"""
import requests
import json

def test_popular_phones():
    """Тестирование эндпоинта /products/popular-phones"""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("Тестирование эндпоинта /products/popular-phones")
    print("=" * 60)
    
    try:
        # Тест 1: Получение популярных телефонов
        print("\n1. Запрос популярных телефонов (limit=3)...")
        response = requests.get(
            f"{base_url}/products/popular-phones",
            params={"limit": 3, "use_cache": False}
        )
        
        print(f"   Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Найдено товаров: {data.get('total', 0)}")
            
            if data.get('products'):
                print("\n   Товары:")
                for i, product in enumerate(data['products'], 1):
                    prod = product['product']
                    print(f"   {i}. {prod.get('brand', 'N/A')} {prod.get('model', 'N/A')}")
                    print(f"      Название: {prod.get('title', 'N/A')[:50]}")
                    print(f"      Цена: {product.get('min_price', 'N/A')} руб.")
                    print(f"      Изображение: {prod.get('image', 'N/A')[:50]}...")
                    print()
            else:
                print("   ⚠️ Товары не найдены!")
        else:
            print(f"   ❌ Ошибка: {response.text}")
        
        # Тест 2: Проверка с кэшем
        print("\n2. Запрос с кэшем (use_cache=True)...")
        response2 = requests.get(
            f"{base_url}/products/popular-phones",
            params={"limit": 3, "use_cache": True}
        )
        print(f"   Статус: {response2.status_code}")
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"   Найдено товаров: {data2.get('total', 0)}")
        
        # Тест 3: Проверка обычного поиска
        print("\n3. Проверка обычного поиска (search='смартфон')...")
        response3 = requests.get(
            f"{base_url}/products",
            params={"search": "смартфон", "limit": 3}
        )
        print(f"   Статус: {response3.status_code}")
        if response3.status_code == 200:
            data3 = response3.json()
            print(f"   Найдено товаров: {data3.get('total', 0)}")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Ошибка: Не удалось подключиться к серверу.")
        print("   Убедитесь, что сервер запущен: uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")

if __name__ == "__main__":
    test_popular_phones()
