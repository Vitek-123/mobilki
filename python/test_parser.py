"""
Тестовый скрипт для проверки работы парсера Яндекс.Маркет
"""
import sys
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_parser():
    """Тестирование парсера"""
    print("=" * 80)
    print("Тест парсера Яндекс.Маркет")
    print("=" * 80)
    
    try:
        from yandex_market_parser import YandexMarketParser
        
        print("\n1. Инициализация парсера...")
        parser = YandexMarketParser()
        print("✅ Парсер инициализирован")
        
        print("\n2. Тест поиска товаров...")
        print("   Запрос: 'смартфон', лимит: 5")
        products = parser.search_products(query="смартфон", limit=5)
        
        if products:
            print(f"\n✅ Найдено товаров: {len(products)}")
            for i, product in enumerate(products, 1):
                print(f"\n   Товар {i}:")
                print(f"   - Название: {product.title[:60]}")
                print(f"   - Бренд: {product.brand}")
                print(f"   - Модель: {product.model}")
                print(f"   - Цена: {product.price:,.0f} ₽")
                print(f"   - URL: {product.url[:70]}...")
                if product.image:
                    print(f"   - Изображение: {product.image[:50]}...")
        else:
            print("⚠️ Товары не найдены")
            print("\nВозможные причины:")
            print("1. Изменилась структура HTML на Яндекс.Маркет")
            print("2. Блокировка запросов (нужно добавить больше заголовков)")
            print("3. Требуется JavaScript для загрузки контента")
        
        print("\n3. Тест популярных товаров...")
        popular = parser.get_popular_products(category="электроника", limit=5)
        
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
    success = test_parser()
    sys.exit(0 if success else 1)

