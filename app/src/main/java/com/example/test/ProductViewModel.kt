package com.example.test

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.launch

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
            _products.value = Resource.Loading()
            try {
                android.util.Log.d("ProductViewModel", "Загрузка товаров. Поисковый запрос: '${searchQuery}'")
                
                val response = if (searchQuery.isEmpty()) {
                    // Если поисковый запрос пустой, загружаем популярные телефоны
                    android.util.Log.d("ProductViewModel", "Запрос популярных телефонов...")
                    RetrofitClient.apiService.getPopularPhones(limit = 3, useCache = true)
                } else {
                    // Иначе используем обычный поиск
                    android.util.Log.d("ProductViewModel", "Обычный поиск: '$searchQuery'")
                    RetrofitClient.apiService.getProductsSuspend(
                        skip = currentPage * PAGE_SIZE,
                        limit = PAGE_SIZE,
                        search = searchQuery
                    )
                }

                android.util.Log.d("ProductViewModel", "Ответ получен. Статус: ${response.code()}, Успешно: ${response.isSuccessful}")

                if (response.isSuccessful) {
                    val productsResponse = response.body()
                    android.util.Log.d("ProductViewModel", "Тело ответа: $productsResponse")
                    
                    if (productsResponse != null) {
                        android.util.Log.d("ProductViewModel", "Количество товаров в ответе: ${productsResponse.products.size}")
                        android.util.Log.d("ProductViewModel", "Total: ${productsResponse.total}")
                        
                        val convertedProducts = convertApiProductsToAppProducts(productsResponse.products)
                        android.util.Log.d("ProductViewModel", "Конвертировано товаров: ${convertedProducts.size}")
                        
                        allProducts.clear()
                        allProducts.addAll(convertedProducts)
                        _products.value = Resource.Success(allProducts.toList())
                        // Для популярных телефонов считаем, что это последняя страница
                        isLastPage = searchQuery.isEmpty() || convertedProducts.size < PAGE_SIZE
                        currentPage++
                    } else {
                        android.util.Log.e("ProductViewModel", "Пустой ответ от сервера")
                        _products.value = Resource.Error("Пустой ответ от сервера")
                    }
                } else {
                    val errorBody = response.errorBody()?.string()
                    android.util.Log.e("ProductViewModel", "Ошибка загрузки: ${response.code()}, Тело: $errorBody")
                    _products.value = Resource.Error("Ошибка загрузки: ${response.code()}")
                }
            } catch (t: Throwable) {
                android.util.Log.e("ProductViewModel", "Исключение при загрузке товаров", t)
                _products.value = Resource.Error("Не удалось загрузить товары: ${t.message}")
            }
        }
    }

    fun loadMoreProducts(searchQuery: String = "") {
        if (isLastPage) return

        viewModelScope.launch {
            try {
                val response = RetrofitClient.apiService.getProductsSuspend(
                    skip = currentPage * PAGE_SIZE,
                    limit = PAGE_SIZE,
                    search = if (searchQuery.isNotEmpty()) searchQuery else null
                )

                if (response.isSuccessful) {
                    val productsResponse = response.body()
                    if (productsResponse != null) {
                        val convertedProducts = convertApiProductsToAppProducts(productsResponse.products)
                        allProducts.addAll(convertedProducts)
                        _products.value = Resource.Success(allProducts.toList())
                        isLastPage = convertedProducts.size < PAGE_SIZE
                        currentPage++
                    }
                }
            } catch (t: Throwable) {
                // Silent fail for pagination
            }
        }
    }

    fun searchProducts(query: String) {
        loadProducts(query)
    }

    fun refreshProducts(searchQuery: String = "") {
        loadProducts(searchQuery)
    }

    fun resetPagination() {
        currentPage = 0
        isLastPage = false
        allProducts.clear()
    }

    private fun convertApiProductsToAppProducts(apiProducts: List<ProductWithPricesResponse>): List<Product> {
        android.util.Log.d("ProductViewModel", "Конвертация ${apiProducts.size} товаров")
        
        return apiProducts.mapNotNull { apiProduct ->
            try {
                val product = apiProduct.product
                val prices = apiProduct.prices

                android.util.Log.d("ProductViewModel", "Товар: ${product.title}, Цен: ${prices.size}")

                val cheapestPriceInfo = if (prices.isNotEmpty()) {
                    prices.minByOrNull { it.price }
                } else {
                    null
                }
                
                val minPrice: Float = cheapestPriceInfo?.price ?: apiProduct.min_price ?: 0.0f
                val cheapestShop = cheapestPriceInfo?.shop_name ?: "Не указан"
                // Получаем URL самого дешевого товара
                val productUrl = cheapestPriceInfo?.url

                val convertedProduct = Product(
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
                
                android.util.Log.d("ProductViewModel", "Конвертирован товар: ${convertedProduct.title}, цена: ${convertedProduct.price}")
                convertedProduct
            } catch (e: Exception) {
                android.util.Log.e("ProductViewModel", "Ошибка конвертации товара", e)
                e.printStackTrace()
                null
            }
        }
    }
}