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
                val response = RetrofitClient.apiService.getProductsSuspend(
                    skip = currentPage * PAGE_SIZE,
                    limit = PAGE_SIZE,
                    search = if (searchQuery.isNotEmpty()) searchQuery else null
                )

                if (response.isSuccessful) {
                    val productsResponse = response.body()
                    if (productsResponse != null) {
                        val convertedProducts = convertApiProductsToAppProducts(productsResponse.products)
                        allProducts.clear()
                        allProducts.addAll(convertedProducts)
                        _products.value = Resource.Success(allProducts.toList())
                        isLastPage = convertedProducts.size < PAGE_SIZE
                        currentPage++
                    } else {
                        _products.value = Resource.Error("Пустой ответ от сервера")
                    }
                } else {
                    _products.value = Resource.Error("Ошибка загрузки: ${response.code()}")
                }
            } catch (t: Throwable) {
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
        return apiProducts.mapNotNull { apiProduct ->
            try {
                val product = apiProduct.product
                val prices = apiProduct.prices

                val cheapestPriceInfo = prices.minByOrNull { it.price }
                val minPrice = cheapestPriceInfo?.price ?: apiProduct.min_price
                val cheapestShop = cheapestPriceInfo?.shop_name ?: "Не указан"

                Product(
                    id = product.id_product,
                    title = product.title ?: "${product.brand} ${product.model}",
                    brand = product.brand ?: "Не указан",
                    model = product.model ?: "Не указана",
                    description = product.description ?: "Описание не указано",
                    image = product.image ?: "https://via.placeholder.com/600x400?text=No+Image",
                    price = minPrice,
                    shopCount = prices.size,
                    cheapestShop = cheapestShop
                )
            } catch (e: Exception) {
                e.printStackTrace()
                null
            }
        }
    }
}