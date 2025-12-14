"""
Модуль для объединения товаров из разных источников с чередованием
"""
from typing import List, Dict


def merge_products_alternating(
    external_products: List[Dict],
    db_products: List[Dict],
    static_products: List[Dict] = None
) -> List[Dict]:
    """
    Объединение товаров из разных источников с чередованием
    
    Алгоритм чередования:
    1. Берем товар из внешнего источника
    2. Берем товар из БД
    3. Берем товар из статических (если есть)
    4. Повторяем цикл
    
    Args:
        external_products: Товары из внешнего источника
        db_products: Товары из базы данных
        static_products: Статические товары (опционально)
    
    Returns:
        Объединенный список товаров с чередованием
    """
    if static_products is None:
        static_products = []
    
    merged = []
    
    # Индексы для каждого источника
    external_idx = 0
    db_idx = 0
    static_idx = 0
    
    # Чередуем товары: внешний источник -> БД -> Статические -> повтор
    while external_idx < len(external_products) or db_idx < len(db_products) or static_idx < len(static_products):
        if external_idx < len(external_products):
            merged.append(external_products[external_idx])
            external_idx += 1
        
        if db_idx < len(db_products):
            merged.append(db_products[db_idx])
            db_idx += 1
        
        if static_idx < len(static_products):
            merged.append(static_products[static_idx])
            static_idx += 1
    
    return merged

