package com.example.test

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.ImageView
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import com.bumptech.glide.Glide
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import retrofit2.Response
import android.util.Log

class ProductDetailActivity : AppCompatActivity() {

    private lateinit var imageView: ImageView
    private lateinit var titleTextView: TextView
    private lateinit var brandTextView: TextView
    private lateinit var descriptionTextView: TextView
    private lateinit var minPriceTextView: TextView
    private lateinit var maxPriceTextView: TextView
    private lateinit var compareButton: Button
    private lateinit var buyButton: Button
    private lateinit var progressBar: ProgressBar
    private lateinit var errorTextView: TextView

    private var productId: Int = -1
    private var shopUrl: String? = null
    private var shopName: String? = null
    private var productData: ProductWithPricesResponse? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        // Применяем тему перед setContentView
        ThemeUtils.applyTheme(this)
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_product_detail)
        
        // Обработка system bars
        try {
            val mainLayout = findViewById<androidx.coordinatorlayout.widget.CoordinatorLayout>(R.id.main)
            if (mainLayout != null) {
                ViewCompat.setOnApplyWindowInsetsListener(mainLayout) { v, insets ->
                    val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
                    v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom)
                    insets
                }
            }
        } catch (e: Exception) {
            Log.e("ProductDetail", "Error setting up window insets", e)
        }

        // Инициализация RetrofitClient
        RetrofitClient.initialize(this)

        // Получаем ID товара из Intent
        productId = intent.getIntExtra("product_id", -1)
        if (productId == -1) {
            Toast.makeText(this, getString(R.string.error_product_not_found), Toast.LENGTH_SHORT).show()
            finish()
            return
        }

        initViews()
        setupListeners()
        loadProductDetails()
    }
    
    private fun addToViewHistory() {
        if (productId <= 0) return
        
        val authManager = AuthManager.getInstance(this)
        if (!authManager.isLoggedIn()) return
        
        // Используем CoroutineScope вместо lifecycleScope для совместимости с AppCompatActivity
        // Запускаем в фоне, не блокируя UI
        CoroutineScope(Dispatchers.IO).launch {
            try {
                RetrofitClient.apiService.addViewHistory(productId)
            } catch (e: Exception) {
                // Silent fail
            }
        }
    }

    private fun initViews() {
        imageView = findViewById(R.id.ProductDetail_imageView)
        titleTextView = findViewById(R.id.ProductDetail_textView_title)
        brandTextView = findViewById(R.id.ProductDetail_textView_brand)
        descriptionTextView = findViewById(R.id.ProductDetail_textView_description)
        minPriceTextView = findViewById(R.id.ProductDetail_textView_minPrice)
        maxPriceTextView = findViewById(R.id.ProductDetail_textView_maxPrice)
        compareButton = findViewById(R.id.ProductDetail_button_compare)
        buyButton = findViewById(R.id.ProductDetail_button_buy)
        progressBar = findViewById(R.id.ProductDetail_progressBar)
        errorTextView = findViewById(R.id.ProductDetail_textView_error)
    }

    private fun setupListeners() {
        compareButton.setOnClickListener {
            val intent = Intent(this, ShopComparisonActivity::class.java)
            intent.putExtra("product_id", productId)
            startActivity(intent)
        }
        
        // Функция для открытия поиска (fallback) - должна быть определена первой
        val openSearchFallback = {
            val currentProductData = productData
            
            if (currentProductData != null) {
                val product = currentProductData.product
                val searchQuery = product.title ?: "${product.brand} ${product.model}".trim()
                
                // Открываем поиск
                Toast.makeText(this, "Поиск товара: $searchQuery", Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(this, "Товар не найден", Toast.LENGTH_SHORT).show()
            }
        }
        
        // Функция для открытия ссылки на магазин
        val openShopUrl = {
            val currentShopUrl = shopUrl
            val currentShopName = shopName
            if (!currentShopUrl.isNullOrEmpty()) {
                val normalizedUrl = normalizeUrl(currentShopUrl)
                if (normalizedUrl != null && isValidProductUrl(normalizedUrl, currentShopName)) {
                    try {
                        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(normalizedUrl))
                        startActivity(intent)
                    } catch (e: Exception) {
                        Toast.makeText(this, getString(R.string.error_opening_url), Toast.LENGTH_SHORT).show()
                        openSearchFallback()
                    }
                } else {
                    openSearchFallback()
                }
            } else {
                openSearchFallback()
            }
        }
        
        // Обработчик клика на кнопку
        buyButton.setOnClickListener {
            openShopUrl()
        }
        
        // Обработчик клика на картинку
        imageView.setOnClickListener {
            openShopUrl()
        }
    }

    private fun loadProductDetails() {
        // Проверяем кэш перед загрузкой с сервера
        val cachedProductData = ProductCache.getProductDetail(productId)
        if (cachedProductData != null) {
            displayProduct(cachedProductData)
            addToViewHistory()
            return
        }
        
        showLoading(true)
        hideError()

        CoroutineScope(Dispatchers.IO).launch {
            try {
                // Загружаем данные товара
                val response: Response<ProductWithPricesResponse> = 
                    RetrofitClient.apiService.getProductByIdSuspend(productId)

                withContext(Dispatchers.Main) {
                    showLoading(false)

                    if (response.isSuccessful) {
                        val productData = response.body()
                        if (productData != null) {
                            // Сохраняем в кэш и отображаем товар
                            ProductCache.putProductDetail(productId, productData)
                            displayProduct(productData)
                            
                            // Добавляем в историю просмотров асинхронно (не блокируем UI)
                            CoroutineScope(Dispatchers.IO).launch {
                                addToViewHistory()
                            }
                        } else {
                            showError("Пустой ответ от сервера")
                        }
                    } else {
                        showError("Ошибка загрузки: ${response.code()}")
                    }
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    showLoading(false)
                    showError("Не удалось загрузить товар: ${e.message}")
                }
            }
        }
    }

    private fun displayProduct(productData: ProductWithPricesResponse) {
        // Сохраняем данные товара для использования в обработчиках
        this.productData = productData
        
        val product = productData.product
        val prices = productData.prices

        // Загрузка изображения
        if (!product.image.isNullOrEmpty()) {
            Glide.with(this)
                .load(product.image)
                .placeholder(R.drawable.adapter_placeholder_image)
                .error(R.drawable.adapter_error_image)
                .into(imageView)
        } else {
            imageView.setImageResource(R.drawable.adapter_placeholder_image)
        }

        // Название
        titleTextView.text = product.title ?: "${product.brand} ${product.model}"

        // Бренд и модель
        val brandModel = buildString {
            if (!product.brand.isNullOrEmpty()) append(product.brand)
            if (!product.brand.isNullOrEmpty() && !product.model.isNullOrEmpty()) append(" / ")
            if (!product.model.isNullOrEmpty()) append(product.model)
        }
        brandTextView.text = brandModel.ifEmpty { "Не указано" }

        // Описание
        descriptionTextView.text = product.description ?: "Описание не указано"

        // Цены
        val minPrice = productData.min_price
        val maxPrice = productData.max_price

        minPriceTextView.text = if (minPrice != null) {
            CurrencyUtils.formatPrice(this, minPrice.toDouble())
        } else {
            "Не указана"
        }

        maxPriceTextView.text = if (maxPrice != null) {
            CurrencyUtils.formatPrice(this, maxPrice.toDouble())
        } else {
            "Не указана"
        }

        // Поиск URL магазина (приоритет: самая дешевая цена)
        
        // Находим самую дешевую цену и берем её URL
        val cheapestPrice = prices.minByOrNull { it.price }
        shopUrl = cheapestPrice?.url
        shopName = cheapestPrice?.shop_name
        
        // Если URL нет у самой дешевой, берем первый доступный
        if (shopUrl.isNullOrEmpty()) {
            val firstAvailable = prices.firstOrNull { !it.url.isNullOrEmpty() }
            shopUrl = firstAvailable?.url
            shopName = firstAvailable?.shop_name
        }

        // Показываем кнопку "Купить в магазине" только если есть URL
        if (!shopUrl.isNullOrEmpty() && !shopName.isNullOrEmpty()) {
            buyButton.visibility = View.VISIBLE
            buyButton.isEnabled = true
            val buttonShopName = shopName ?: "магазине"
            buyButton.text = getString(R.string.button_buy_in_shop, buttonShopName)
            imageView.isClickable = true
            imageView.isFocusable = true
        } else {
            buyButton.visibility = View.VISIBLE
            buyButton.isEnabled = true
            buyButton.text = getString(R.string.find_in_shop, "магазине")
            imageView.isClickable = true
            imageView.isFocusable = true
        }

        // Кнопка сравнения
        compareButton.isEnabled = prices.isNotEmpty()
        compareButton.text = if (prices.isNotEmpty()) {
            "Сравнить цены в ${prices.size} магазинах"
        } else {
            "Нет доступных магазинов"
        }
    }

    private fun showLoading(show: Boolean) {
        progressBar.visibility = if (show) View.VISIBLE else View.GONE
    }

    private fun showError(message: String) {
        errorTextView.text = message
        errorTextView.visibility = View.VISIBLE
    }

    private fun hideError() {
        errorTextView.visibility = View.GONE
    }
    
    private fun normalizeUrl(url: String): String? {
        if (url.isBlank()) return null
        
        val trimmedUrl = url.trim()
        
        val suspiciousPaths = listOf("/Common/", "/Error", "/404", "/NotFound", "/common/", "/error")
        if (suspiciousPaths.any { trimmedUrl.contains(it, ignoreCase = true) }) {
            return null
        }
        
        if (trimmedUrl.startsWith("http://", ignoreCase = true) || 
            trimmedUrl.startsWith("https://", ignoreCase = true)) {
            if (suspiciousPaths.any { trimmedUrl.contains(it, ignoreCase = true) }) {
                return null
            }
            return trimmedUrl
        }
        
        if (trimmedUrl.startsWith("/")) {
            val validPatterns = listOf("/p/", "/product/", "/products/", "/item/", "/goods/", "/catalog/", "/search")
            if (validPatterns.any { trimmedUrl.contains(it, ignoreCase = true) } || 
                trimmedUrl.matches(Regex("^/\\d+/?$"))) {
                    return trimmedUrl
            } else {
                return null
            }
        }
        
        if (trimmedUrl.startsWith("http://") || trimmedUrl.startsWith("https://")) {
                        if (suspiciousPaths.any { trimmedUrl.contains(it, ignoreCase = true) }) {
                            return null
                        }
            return trimmedUrl
                    }
        
        // В остальных случаях считаем невалидным
        return null
    }
    
       private fun isValidProductUrl(url: String, shopName: String? = null): Boolean {
           if (url.isBlank()) return false

               // Проверяем формат URL
               if (!url.startsWith("http://") && !url.startsWith("https://")) {
                   return false
           }
        
        val suspiciousPaths = listOf("/Common/", "/Error", "/404", "/NotFound", "/common/", "/error")
        if (suspiciousPaths.any { url.contains(it, ignoreCase = true) }) {
            return false
        }
        
        val validPatterns = listOf("/p/", "/product/", "/item/", "/goods/", "/catalog/", "/search")
        val hasValidPattern = validPatterns.any { url.contains(it, ignoreCase = true) }
        val isNumericPath = url.matches(Regex(".*/\\d+/?.*"))
        val isRootOrSearch = url.endsWith("/") || url.contains("/search")
        
        if (!hasValidPattern && !isNumericPath && !isRootOrSearch) {
            return false
        }
        
        return true
    }
}

