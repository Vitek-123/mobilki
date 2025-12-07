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
    private lateinit var buyYandexButton: Button
    private lateinit var progressBar: ProgressBar
    private lateinit var errorTextView: TextView

    private var productId: Int = -1
    private var yandexMarketUrl: String? = null

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
        if (productId <= 0) {
            Log.w("ProductDetail", "Invalid product ID, skipping view history")
            return
        }
        
        val authManager = AuthManager.getInstance(this)
        if (!authManager.isLoggedIn()) {
            Log.d("ProductDetail", "User not logged in, skipping view history")
            return
        }
        
        // Используем CoroutineScope вместо lifecycleScope для совместимости с AppCompatActivity
        // Запускаем в фоне, не блокируя UI
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val response = RetrofitClient.apiService.addViewHistory(productId)
                if (!response.isSuccessful) {
                    // Логируем ошибку, но не крашим приложение
                    val errorBody = response.errorBody()?.string()
                    Log.e("ProductDetail", "Error adding to view history: ${response.code()}, message: ${response.message()}, body: $errorBody")
                } else {
                    Log.d("ProductDetail", "Product $productId added to view history successfully")
                }
            } catch (e: Exception) {
                // Логируем ошибку, но не крашим приложение
                Log.e("ProductDetail", "Error adding to view history", e)
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
        buyYandexButton = findViewById(R.id.ProductDetail_button_buy_yandex)
        progressBar = findViewById(R.id.ProductDetail_progressBar)
        errorTextView = findViewById(R.id.ProductDetail_textView_error)
    }

    private fun setupListeners() {
        compareButton.setOnClickListener {
            val intent = Intent(this, ShopComparisonActivity::class.java)
            intent.putExtra("product_id", productId)
            startActivity(intent)
        }
        
        buyYandexButton.setOnClickListener {
            yandexMarketUrl?.let { url ->
                try {
                    val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                    startActivity(intent)
                } catch (e: Exception) {
                    Log.e("ProductDetail", "Ошибка открытия URL Яндекс.Маркет", e)
                    Toast.makeText(this, getString(R.string.error_opening_url), Toast.LENGTH_SHORT).show()
                }
            } ?: run {
                Toast.makeText(this, "Ссылка на Яндекс.Маркет недоступна", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun loadProductDetails() {
        showLoading(true)
        hideError()

        CoroutineScope(Dispatchers.IO).launch {
            try {
                val response: Response<ProductWithPricesResponse> = 
                    RetrofitClient.apiService.getProductByIdSuspend(productId)

                withContext(Dispatchers.Main) {
                    showLoading(false)

                    if (response.isSuccessful) {
                        val productData = response.body()
                        if (productData != null) {
                            displayProduct(productData)
                            // Добавляем в историю просмотров только после успешной загрузки товара
                            addToViewHistory()
                        } else {
                            showError("Пустой ответ от сервера")
                        }
                    } else {
                        val errorBody = try {
                            response.errorBody()?.string()
                        } catch (e: Exception) {
                            null
                        }
                        Log.e("ProductDetail", "Error loading product: ${response.code()}, body: $errorBody")
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
            String.format("%,.0f ₽", minPrice)
        } else {
            "Не указана"
        }

        maxPriceTextView.text = if (maxPrice != null) {
            String.format("%,.0f ₽", maxPrice)
        } else {
            "Не указана"
        }

        // Поиск URL Яндекс.Маркет
        yandexMarketUrl = prices
            .firstOrNull { price ->
                price.shop_name.contains("Яндекс", ignoreCase = true) ||
                price.shop_name.contains("Yandex", ignoreCase = true) ||
                price.shop_name.contains("Маркет", ignoreCase = true) ||
                price.shop_name.contains("Market", ignoreCase = true) ||
                (price.url?.contains("market.yandex.ru", ignoreCase = true) == true)
            }?.url

        // Показываем кнопку "Купить в Яндекс.Маркет" только если есть URL
        if (!yandexMarketUrl.isNullOrEmpty()) {
            buyYandexButton.visibility = View.VISIBLE
            buyYandexButton.isEnabled = true
        } else {
            buyYandexButton.visibility = View.GONE
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
}

