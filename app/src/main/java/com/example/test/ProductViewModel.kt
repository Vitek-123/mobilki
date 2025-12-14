package com.example.test

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class ProductViewModel : ViewModel() {

    companion object {
        const val PAGE_SIZE = 20
    }

    private val _products = MutableLiveData<Resource<List<Product>>>()
    val products: LiveData<Resource<List<Product>>> = _products

    private var allProducts = mutableListOf<Product>()
    var currentPage = 0
    private var isLastPage = false

    fun loadProducts(searchQuery: String = "") {
        currentPage = 0
        isLastPage = false
        viewModelScope.launch {
            // Проверяем кэш перед загрузкой с сервера
            val cacheKey = if (searchQuery.isEmpty()) "popular" else searchQuery
            val cachedProducts = ProductCache.getProducts(cacheKey, 0, PAGE_SIZE)
            
            if (cachedProducts != null) {
                allProducts.clear()
                allProducts.addAll(cachedProducts)
                _products.value = Resource.Success(allProducts.toList())
                isLastPage = searchQuery.isEmpty() || cachedProducts.size < PAGE_SIZE
                currentPage++
                return@launch
            }
            
            _products.value = Resource.Loading()
            try {
                val response = if (searchQuery.isEmpty()) {
                    RetrofitClient.apiService.getPopularProducts(limit = 10, useCache = true, category = "электроника")
                } else {
                    RetrofitClient.apiService.getProductsSuspend(
                        skip = currentPage * PAGE_SIZE,
                        limit = PAGE_SIZE,
                        search = searchQuery
                    )
                }

                if (response.isSuccessful) {
                    val productsResponse = response.body()
                    
                    if (productsResponse != null) {
                        // Конвертируем товары параллельно на фоновом потоке
                        val convertedProducts = withContext(Dispatchers.Default) {
                            convertApiProductsToAppProductsParallel(productsResponse.products)
                        }
                        
                        // Сохраняем в кэш и обновляем UI на главном потоке
                        withContext(Dispatchers.Main) {
                            ProductCache.putProducts(cacheKey, convertedProducts, 0, PAGE_SIZE)
                            
                            allProducts.clear()
                            allProducts.addAll(convertedProducts)
                            _products.value = Resource.Success(allProducts.toList())
                            // Для популярных товаров считаем, что это последняя страница
                            isLastPage = searchQuery.isEmpty() || convertedProducts.size < PAGE_SIZE
                            currentPage++
                        }
                    } else {
                        _products.value = Resource.Error("Пустой ответ от сервера")
                    }
                } else {
                    _products.value = Resource.Error("Ошибка загрузки: ${response.code()}")
                }
            } catch (t: Throwable) {
                android.util.Log.e("ProductViewModel", "Ошибка загрузки товаров: ${t.message}")
                _products.value = Resource.Error("Не удалось загрузить товары: ${t.message}")
            }
        }
    }

    fun loadMoreProducts(searchQuery: String = "") {
        if (isLastPage) return

        viewModelScope.launch(Dispatchers.IO) {
            try {
                val response = RetrofitClient.apiService.getProductsSuspend(
                    skip = currentPage * PAGE_SIZE,
                    limit = PAGE_SIZE,
                    search = if (searchQuery.isNotEmpty()) searchQuery else null
                )

                if (response.isSuccessful) {
                    val productsResponse = response.body()
                    if (productsResponse != null) {
                        // Конвертируем товары параллельно на фоновом потоке
                        val convertedProducts = withContext(Dispatchers.Default) {
                            convertApiProductsToAppProductsParallel(productsResponse.products)
                        }
                        
                        // Обновляем UI на главном потоке
                        withContext(Dispatchers.Main) {
                            allProducts.addAll(convertedProducts)
                            _products.value = Resource.Success(allProducts.toList())
                            isLastPage = convertedProducts.size < PAGE_SIZE
                            currentPage++
                        }
                    }
                }
            } catch (t: Throwable) {
                // Silent fail for pagination
            }
        }
    }
    
    /**
     * Предзагружает следующую страницу товаров в фоне
     */
    fun preloadNextPage(searchQuery: String = "") {
        if (isLastPage) return
        
        viewModelScope.launch(Dispatchers.IO) {
            try {
                // Загружаем следующую страницу в фоне
                val response = RetrofitClient.apiService.getProductsSuspend(
                    skip = (currentPage + 1) * PAGE_SIZE,
                    limit = PAGE_SIZE,
                    search = if (searchQuery.isNotEmpty()) searchQuery else null
                )
                
                if (response.isSuccessful) {
                    val productsResponse = response.body()
                    if (productsResponse != null) {
                        // Конвертируем и кэшируем товары
                        val convertedProducts = withContext(Dispatchers.Default) {
                            convertApiProductsToAppProductsParallel(productsResponse.products)
                        }
                        
                        // Сохраняем в кэш для быстрого доступа
                        val cacheKey = if (searchQuery.isEmpty()) "popular" else searchQuery
                        ProductCache.putProducts(cacheKey, convertedProducts, (currentPage + 1) * PAGE_SIZE, PAGE_SIZE)
                    }
                }
            } catch (t: Throwable) {
                // Silent fail for preload
            }
        }
    }

    fun searchProducts(query: String) {
        loadProducts(query)
    }

    fun refreshProducts(searchQuery: String = "") {
        // Очищаем кэш перед обновлением
        val cacheKey = if (searchQuery.isEmpty()) "popular" else searchQuery
        ProductCache.clearProductsCache(cacheKey)
        loadProducts(searchQuery)
    }

    fun resetPagination() {
        currentPage = 0
        isLastPage = false
        allProducts.clear()
    }
    
    /**
     * Конвертирует товары параллельно для ускорения обработки
     */
    private suspend fun convertApiProductsToAppProductsParallel(apiProducts: List<ProductWithPricesResponse>): List<Product> = withContext(Dispatchers.Default) {
        
        // Создаем задачи для параллельной конвертации
        val deferredProducts = apiProducts.map { apiProduct ->
            async {
                convertSingleProduct(apiProduct)
            }
        }
        
        // Ждем завершения всех задач и фильтруем null значения
        deferredProducts.awaitAll().filterNotNull()
    }
    
    /**
     * Конвертирует один товар из API формата в формат приложения
     */
    private fun convertSingleProduct(apiProduct: ProductWithPricesResponse): Product? {
        return try {
            val product = apiProduct.product
            val prices = apiProduct.prices

            val cheapestPriceInfo = if (prices.isNotEmpty()) {
                prices.minByOrNull { it.price }
            } else {
                null
            }
            
            val minPrice: Float = cheapestPriceInfo?.price ?: apiProduct.min_price ?: 0.0f
            val cheapestShop = cheapestPriceInfo?.shop_name ?: "Не указан"
            
            // Получаем URL: сначала пробуем взять из product.url (для товаров из Яндекс.Маркет),
            // затем у самого дешевого товара, если его нет - берем первый доступный URL из всех цен
            val productUrl = product.url
                ?: cheapestPriceInfo?.url 
                ?: prices.firstOrNull { !it.url.isNullOrEmpty() }?.url

            Product(
                id = product.id_product,
                title = product.title ?: "${product.brand} ${product.model}",
                brand = product.brand ?: "Не указан",
                model = product.model ?: "Не указана",
                description = product.description ?: "Описание не указано",
                image = product.image ?: "https://via.placeholder.com/600x400?text=No+Image",
                price = minPrice,
                shopCount = prices.size,
                cheapestShop = cheapestShop,
                url = productUrl
            )
        } catch (e: Exception) {
            android.util.Log.e("ProductViewModel", "Ошибка конвертации товара", e)
            null
        }
    }
}