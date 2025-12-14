"""
Тестовый скрипт для проверки работы Яндекс.Маркет API
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_yandex_api():
    """Тестирование Яндекс.Маркет API"""
    print("=" * 80)
    print("Тест Яндекс.Маркет OAuth API")
    print("=" * 80)
    
    oauth_token = os.getenv("YANDEX_OAUTH_TOKEN")
    
    if not oauth_token:
        print("\n❌ YANDEX_OAUTH_TOKEN не найден в .env файле")
        print("Для получения токена запустите: python get_oauth_token.py")
        return False
    
    print(f"\n✅ OAuth токен найден: {oauth_token[:30]}...")
    
    try:
        from yandex_market_oauth_api import YandexMarketOAuthAPI
        
        # Инициализация API
        print("\n1. Инициализация API...")
        api = YandexMarketOAuthAPI(oauth_token=oauth_token)
        print("✅ API инициализирован")
        
        # Проверка кампаний
        print("\n2. Проверка кампаний...")
        campaigns = api.get_campaigns()
        if campaigns:
            print(f"✅ Найдено кампаний: {len(campaigns)}")
            for i, campaign in enumerate(campaigns[:3], 1):
                print(f"   {i}. ID: {campaign.get('id')}, Название: {campaign.get('domain', 'N/A')}")
        else:
            print("⚠️ Кампании не найдены (это нормально для разработчиков)")
        
        # Тест поиска товаров
        print("\n3. Тест поиска товаров...")
        print("   Запрос: 'смартфон', лимит: 5")
        products = api.search_products(query="смартфон", limit=5)
        
        if products:
            print(f"✅ Найдено товаров: {len(products)}")
            for i, product in enumerate(products[:3], 1):
                print(f"\n   Товар {i}:")
                print(f"   - Название: {product.title[:50]}")
                print(f"   - Бренд: {product.brand}")
                print(f"   - Модель: {product.model}")
                print(f"   - Цена: {product.price} ₽")
                print(f"   - URL: {product.url[:60]}...")
        else:
            print("⚠️ Товары не найдены")
            print("\nВозможные причины:")
            print("1. Partner API не предоставляет публичный поиск по каталогу")
            print("2. API предназначен для работы с собственными товарами продавца")
            print("3. Может потребоваться другой endpoint или метод")
        
        # Тест популярных товаров
        print("\n4. Тест популярных товаров...")
        popular = api.get_popular_products(category="электроника", limit=5)
        
        if popular:
            print(f"✅ Найдено популярных товаров: {len(popular)}")
        else:
            print("⚠️ Популярные товары не найдены")
        
        print("\n" + "=" * 80)
        print("Тест завершен")
        print("=" * 80)
        
        return len(products) > 0 or len(popular) > 0
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_yandex_api()
    sys.exit(0 if success else 1)

