package com.example.test

import android.util.Log
import java.util.concurrent.ConcurrentHashMap

/**
 * Утилита для кэширования товаров
 * Использует in-memory кэш с TTL (time to live)
 */
object ProductCache {
    private const val TAG = "ProductCache"
    
    // TTL для кэша в миллисекундах (5 минут)
    private const val CACHE_TTL_MS = 5 * 60 * 1000L
    
    // Максимальный размер кэша списков товаров
    private const val MAX_CACHE_SIZE = 50
    
    // Кэш списков товаров: ключ - поисковый запрос, значение - кэшированные данные
    private val productsCache = ConcurrentHashMap<String, CachedProducts>()
    
    // Кэш детальной информации о товаре: ключ - ID товара, значение - кэшированные данные
    private val productDetailCache = ConcurrentHashMap<Int, CachedProductDetail>()
    
    /**
     * Данные кэша для списка товаров
     */
    private data class CachedProducts(
        val products: List<Product>,
        val timestamp: Long = System.currentTimeMillis()
    ) {
        fun isExpired(): Boolean {
            return System.currentTimeMillis() - timestamp > CACHE_TTL_MS
        }
    }
    
    /**
     * Данные кэша для детальной информации о товаре
     */
    private data class CachedProductDetail(
        val productData: ProductWithPricesResponse,
        val timestamp: Long = System.currentTimeMillis()
    ) {
        fun isExpired(): Boolean {
            return System.currentTimeMillis() - timestamp > CACHE_TTL_MS
        }
    }
    
    /**
     * Получает ключ для кэша на основе поискового запроса
     */
    private fun getCacheKey(searchQuery: String, skip: Int = 0, limit: Int = 20): String {
        return "products_${searchQuery}_${skip}_${limit}"
    }
    
    /**
     * Получает список товаров из кэша
     * @param searchQuery Поисковый запрос
     * @param skip Смещение для пагинации
     * @param limit Лимит товаров
     * @return Список товаров или null, если данных нет в кэше или они устарели
     */
    fun getProducts(searchQuery: String, skip: Int = 0, limit: Int = 20): List<Product>? {
        val key = getCacheKey(searchQuery, skip, limit)
        val cached = productsCache[key]
        
        return if (cached != null && !cached.isExpired()) {
            Log.d(TAG, "Товары найдены в кэше для запроса: '$searchQuery'")
            cached.products
        } else {
            if (cached != null) {
                Log.d(TAG, "Кэш устарел для запроса: '$searchQuery'")
                productsCache.remove(key)
            }
            null
        }
    }
    
    /**
     * Сохраняет список товаров в кэш
     * @param searchQuery Поисковый запрос
     * @param products Список товаров для кэширования
     * @param skip Смещение для пагинации
     * @param limit Лимит товаров
     */
    fun putProducts(searchQuery: String, products: List<Product>, skip: Int = 0, limit: Int = 20) {
        val key = getCacheKey(searchQuery, skip, limit)
        
        // Очищаем устаревшие записи перед добавлением новой
        cleanupExpired()
        
        // Если кэш переполнен, удаляем самую старую запись
        if (productsCache.size >= MAX_CACHE_SIZE) {
            val oldestKey = productsCache.entries.minByOrNull { it.value.timestamp }?.key
            oldestKey?.let { productsCache.remove(it) }
            Log.d(TAG, "Кэш переполнен, удалена старая запись: $oldestKey")
        }
        
        productsCache[key] = CachedProducts(products)
        Log.d(TAG, "Товары сохранены в кэш для запроса: '$searchQuery' (${products.size} товаров)")
    }
    
    /**
     * Получает детальную информацию о товаре из кэша
     * @param productId ID товара
     * @return Данные товара или null, если данных нет в кэше или они устарели
     */
    fun getProductDetail(productId: Int): ProductWithPricesResponse? {
        val cached = productDetailCache[productId]
        
        return if (cached != null && !cached.isExpired()) {
            Log.d(TAG, "Детальная информация о товаре $productId найдена в кэше")
            cached.productData
        } else {
            if (cached != null) {
                Log.d(TAG, "Кэш детальной информации о товаре $productId устарел")
                productDetailCache.remove(productId)
            }
            null
        }
    }
    
    /**
     * Сохраняет детальную информацию о товаре в кэш
     * @param productId ID товара
     * @param productData Данные товара для кэширования
     */
    fun putProductDetail(productId: Int, productData: ProductWithPricesResponse) {
        // Очищаем устаревшие записи перед добавлением новой
        cleanupExpired()
        
        productDetailCache[productId] = CachedProductDetail(productData)
        Log.d(TAG, "Детальная информация о товаре $productId сохранена в кэш")
    }
    
    /**
     * Очищает устаревшие записи из кэша
     */
    private fun cleanupExpired() {
        val now = System.currentTimeMillis()
        
        // Очищаем устаревшие списки товаров
        val expiredProducts = productsCache.entries.filter { it.value.isExpired() }
        expiredProducts.forEach { productsCache.remove(it.key) }
        if (expiredProducts.isNotEmpty()) {
            Log.d(TAG, "Очищено ${expiredProducts.size} устаревших записей списков товаров")
        }
        
        // Очищаем устаревшие детальные данные
        val expiredDetails = productDetailCache.entries.filter { it.value.isExpired() }
        expiredDetails.forEach { productDetailCache.remove(it.key) }
        if (expiredDetails.isNotEmpty()) {
            Log.d(TAG, "Очищено ${expiredDetails.size} устаревших записей детальной информации")
        }
    }
    
    /**
     * Очищает весь кэш
     */
    fun clearAll() {
        productsCache.clear()
        productDetailCache.clear()
        Log.d(TAG, "Весь кэш очищен")
    }
    
    /**
     * Очищает кэш для конкретного поискового запроса
     */
    fun clearProductsCache(searchQuery: String) {
        val keysToRemove = productsCache.keys.filter { it.startsWith("products_${searchQuery}_") }
        keysToRemove.forEach { productsCache.remove(it) }
        Log.d(TAG, "Кэш очищен для запроса: '$searchQuery' (${keysToRemove.size} записей)")
    }
    
    /**
     * Очищает кэш детальной информации о конкретном товаре
     */
    fun clearProductDetailCache(productId: Int) {
        productDetailCache.remove(productId)
        Log.d(TAG, "Кэш детальной информации о товаре $productId очищен")
    }
    
    /**
     * Получает статистику кэша
     */
    fun getCacheStats(): String {
        cleanupExpired()
        return "Списки товаров: ${productsCache.size}, Детальная информация: ${productDetailCache.size}"
    }
}

