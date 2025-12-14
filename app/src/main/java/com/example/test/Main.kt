package com.example.test

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.widget.ProgressBar
import android.widget.SearchView
import android.widget.TextView
import android.widget.Toast
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView

class Main : BaseActivity() {
    
    private val viewModel: ProductViewModel by viewModels()
    private lateinit var recyclerView: RecyclerView
    private lateinit var adapter: ProductAdapter
    private lateinit var progressBar: ProgressBar
    private lateinit var emptyTextView: TextView
    private lateinit var errorTextView: TextView
    private lateinit var searchView: SearchView
    
    private var currentSearchQuery = ""
    private var isLoadingMore = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.main)
        
        // Инициализация RetrofitClient
        RetrofitClient.initialize(this)
        
        // Инициализация курсов валют (загружает актуальные курсы в фоне)
        CurrencyUtils.initializeRates(this)
        
        // Обработка system bars для CoordinatorLayout (без padding снизу, чтобы bottom navigation был виден)
        findViewById<View>(R.id.main)?.let { mainView ->
            ViewCompat.setOnApplyWindowInsetsListener(mainView) { v, insets ->
                val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
                v.setPadding(systemBars.left, systemBars.top, systemBars.right, 0)
                insets
            }
        }
        
        // Обработка system bars для контента (учитываем bottom navigation)
        findViewById<View>(R.id.content_container)?.let { contentView ->
            ViewCompat.setOnApplyWindowInsetsListener(contentView) { v, insets ->
                val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
                // Padding снизу уже установлен в layout (72dp для bottom navigation)
                v.setPadding(systemBars.left, systemBars.top, systemBars.right, v.paddingBottom + systemBars.bottom)
                insets
            }
        }

        setupBottomNavigation(R.id.navigation_home)
        initViews()
        setupRecyclerView()
        setupSearchView()
        observeViewModel()
        
        // Загружаем товары при первом запуске
        if (savedInstanceState == null) {
            viewModel.loadProducts()
        }
    }

    private fun initViews() {
        recyclerView = findViewById(R.id.Main_RecyclerView_product)
        progressBar = findViewById(R.id.Main_progressBar)
        emptyTextView = findViewById(R.id.Main_textview_empty)
        errorTextView = findViewById(R.id.Main_textview_error)
        searchView = findViewById(R.id.Main_SearchView)
    }

    private fun setupRecyclerView() {
        // Оптимизация RecyclerView для лучшей производительности
        recyclerView.setHasFixedSize(true) // Если размер элементов фиксированный
        recyclerView.setItemViewCacheSize(20) // Увеличиваем кэш представлений для плавной прокрутки
        
        adapter = ProductAdapter(
            productList = emptyList(),
            context = this,
            object : ProductAdapter.OnItemClickListener {
                override fun onProductClick(product: Product) {
                    // Открываем детальную страницу товара
                    if (product.id <= 0) {
                        Toast.makeText(this@Main, getString(R.string.error_invalid_product_id), Toast.LENGTH_SHORT).show()
                        return
                    }
                    try {
                        val intent = Intent(this@Main, ProductDetailActivity::class.java)
                        intent.putExtra("product_id", product.id)
                        startActivity(intent)
                    } catch (e: Exception) {
                        android.util.Log.e("Main", "Error opening product detail", e)
                        Toast.makeText(this@Main, getString(R.string.error_opening_product, e.message ?: ""), Toast.LENGTH_SHORT).show()
                    }
                }

                override fun onBuyButtonClick(product: Product) {
                    // Определяем, является ли товар товаром из Яндекс.Маркета
                    val isYandexMarketProduct = isYandexMarketProduct(product)
                    
                    if (isYandexMarketProduct) {
                        // Товар из Яндекс.Маркет - открываем URL из product
                        // URL уже извлечен из prices при конвертации в ProductViewModel
                        val productUrl = product.url
                        
                        if (!productUrl.isNullOrEmpty()) {
                            val url = productUrl.trim()
                            
                            // Проверяем, что это валидный URL Яндекс.Маркет
                            val urlLower = url.lowercase()
                            val isYandexMarketUrl = urlLower.contains("market.yandex.ru") || 
                                                   urlLower.contains("yandex.ru/product") ||
                                                   urlLower.contains("yandex.ru/catalog") ||
                                                   url.startsWith("https://market.yandex.ru") ||
                                                   url.startsWith("http://market.yandex.ru")
                            
                            if (isYandexMarketUrl) {
                                try {
                                    // Нормализуем URL
                                    val finalUrl = when {
                                        url.startsWith("http://") || url.startsWith("https://") -> url
                                        url.startsWith("/") -> "https://market.yandex.ru$url"
                                        else -> "https://market.yandex.ru/$url"
                                    }
                                    
                                    val intent = Intent(Intent.ACTION_VIEW, Uri.parse(finalUrl))
                                    startActivity(intent)
                                    return
                                } catch (e: Exception) {
                                    android.util.Log.e("Main", "Ошибка открытия URL Яндекс.Маркет", e)
                                    Toast.makeText(this@Main, "Не удалось открыть Яндекс.Маркет", Toast.LENGTH_SHORT).show()
                                }
                            }
                        }
                        
                        // Fallback: открываем поиск в Яндекс.Маркет
                        val searchQuery = if (product.brand != null && product.model != null &&
                                            product.brand != "Не указан" && product.model != "Не указана") {
                            "${product.brand} ${product.model}".trim()
                        } else {
                            product.title ?: ""
                        }
                        
                        if (searchQuery.isNotEmpty()) {
                            // Формируем поисковый URL Яндекс.Маркет
                            val searchParams = mutableListOf<String>()
                            searchParams.add("text=${android.net.Uri.encode(searchQuery)}")
                            
                            // Добавляем фильтр по бренду если есть
                            if (product.brand != null && product.brand != "Не указан" && 
                                !searchQuery.contains(product.brand, ignoreCase = true)) {
                                searchParams.add("vendor=${android.net.Uri.encode(product.brand)}")
                            }
                            
                            // Сортировка по цене
                            searchParams.add("how=aprice")
                            
                            val searchUrl = "https://market.yandex.ru/search?${searchParams.joinToString("&")}"
                            
                            try {
                                val intent = Intent(Intent.ACTION_VIEW, Uri.parse(searchUrl))
                                startActivity(intent)
                                return
                            } catch (e: Exception) {
                                Toast.makeText(this@Main, "Не удалось открыть Яндекс.Маркет", Toast.LENGTH_SHORT).show()
                                return
                            }
                        } else {
                            // Если нет поискового запроса, открываем главную страницу Яндекс.Маркет
                            try {
                                val intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://market.yandex.ru"))
                                startActivity(intent)
                                return
                            } catch (e: Exception) {
                                Toast.makeText(this@Main, "Не удалось открыть Яндекс.Маркет", Toast.LENGTH_SHORT).show()
                                return
                            }
                        }
                    } else {
                        // Товар из БД - открываем URL из listings (таблица listings, атрибут url)
                        if (!product.url.isNullOrEmpty()) {
                            val url = product.url.trim()
                            try {
                                // Нормализуем URL для БД
                                val finalUrl = when {
                                    url.startsWith("http://") || url.startsWith("https://") -> url
                                    url.startsWith("/") -> {
                                        // Относительный URL - определяем домен по магазину или используем базовый
                                        if (product.cheapestShop.contains("biggeek", ignoreCase = true)) {
                                            "https://biggeek.ru$url"
                                        } else {
                                            "https://$url"
                                        }
                                    }
                                    else -> "https://$url"
                                }
                                
                                val intent = Intent(Intent.ACTION_VIEW, Uri.parse(finalUrl))
                                startActivity(intent)
                                return
                            } catch (e: Exception) {
                                Toast.makeText(this@Main, "Не удалось открыть ссылку", Toast.LENGTH_SHORT).show()
                                return
                            }
                        }
                        
                        // Если URL из listings отсутствует, открываем детальную страницу товара
                        if (product.id > 0) {
                            try {
                                val intent = Intent(this@Main, ProductDetailActivity::class.java)
                                intent.putExtra("product_id", product.id)
                                startActivity(intent)
                            } catch (e: Exception) {
                                android.util.Log.e("Main", "Ошибка открытия детальной страницы", e)
                                Toast.makeText(this@Main, getString(R.string.error_opening_product, e.message ?: ""), Toast.LENGTH_SHORT).show()
                            }
                        } else {
                            Toast.makeText(this@Main, "Ссылка на товар недоступна", Toast.LENGTH_SHORT).show()
                        }
                    }
                }
            }
        )

        recyclerView.layoutManager = LinearLayoutManager(this)
        recyclerView.adapter = adapter

        // Пагинация при прокрутке
        recyclerView.addOnScrollListener(object : RecyclerView.OnScrollListener() {
            override fun onScrolled(recyclerView: RecyclerView, dx: Int, dy: Int) {
                super.onScrolled(recyclerView, dx, dy)
                val layoutManager = recyclerView.layoutManager as? LinearLayoutManager
                val visibleItemCount = layoutManager?.childCount ?: 0
                val totalItemCount = layoutManager?.itemCount ?: 0
                val firstVisibleItemPosition = layoutManager?.findFirstVisibleItemPosition() ?: 0

                // Загружаем следующую страницу, когда осталось 5 элементов до конца
                if (!isLoadingMore && visibleItemCount + firstVisibleItemPosition >= totalItemCount - 5) {
                    isLoadingMore = true
                    viewModel.loadMoreProducts(currentSearchQuery)
                    // Предзагружаем следующую страницу для еще большей скорости
                    viewModel.preloadNextPage(currentSearchQuery)
                    
                    // Таймаут для сброса флага загрузки (на случай ошибки)
                    android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
                        if (isLoadingMore) {
                            isLoadingMore = false
                        }
                    }, 10000) // 10 секунд таймаут
                }
            }
        })
    }

    private fun setupSearchView() {
        // Делаем всю область поиска кликабельной
        val searchContainer = findViewById<android.widget.LinearLayout>(R.id.Main_SearchContainer)
        searchContainer?.setOnClickListener {
            searchView.isIconified = false
            searchView.requestFocus()
            // Показываем клавиатуру
            val imm = getSystemService(android.content.Context.INPUT_METHOD_SERVICE) as android.view.inputmethod.InputMethodManager
            imm.showSoftInput(searchView, android.view.inputmethod.InputMethodManager.SHOW_IMPLICIT)
        }
        
        searchView.setOnQueryTextListener(object : SearchView.OnQueryTextListener {
            override fun onQueryTextSubmit(query: String?): Boolean {
                currentSearchQuery = query ?: ""
                viewModel.searchProducts(currentSearchQuery)
                searchView.clearFocus()
                return true
            }

            override fun onQueryTextChange(newText: String?): Boolean {
                // Можно добавить debounce для поиска в реальном времени
                return false
            }
        })

        // Очистка поиска
        searchView.setOnCloseListener {
            currentSearchQuery = ""
            viewModel.loadProducts()
            false
        }
    }

    private fun observeViewModel() {
        viewModel.products.observe(this) { resource ->
            when (resource) {
                is Resource.Loading -> {
                    // Показываем основной прогресс только при первой загрузке
                    if (!isLoadingMore) {
                        showLoading(true)
                    }
                    hideError()
                    hideEmpty()
                }
                is Resource.Success -> {
                    showLoading(false)
                    isLoadingMore = false
                    hideError()
                    val products = resource.data ?: emptyList()
                    
                    if (products.isEmpty()) {
                        showEmpty()
                    } else {
                        hideEmpty()
                        adapter.updateData(products)
                    }
                }
                is Resource.Error -> {
                    showLoading(false)
                    isLoadingMore = false
                    showError(resource.message ?: "Неизвестная ошибка")
                    hideEmpty()
                }
            }
        }
    }

    private fun showLoading(show: Boolean) {
        progressBar.visibility = if (show) View.VISIBLE else View.GONE
        recyclerView.visibility = if (show) View.GONE else View.VISIBLE
    }

    private fun showError(message: String) {
        errorTextView.text = "Ошибка: $message"
        errorTextView.visibility = View.VISIBLE
        recyclerView.visibility = View.GONE
    }

    private fun hideError() {
        errorTextView.visibility = View.GONE
    }

    private fun showEmpty() {
        emptyTextView.visibility = View.VISIBLE
        recyclerView.visibility = View.GONE
    }

    private fun hideEmpty() {
        emptyTextView.visibility = View.GONE
    }
    
    /**
     * Проверяет, является ли товар товаром из Яндекс.Маркета
     */
    private fun isYandexMarketProduct(product: Product): Boolean {
        // Проверяем URL товара
        val url = product.url
        if (!url.isNullOrEmpty()) {
            val urlLower = url.lowercase()
            if (urlLower.contains("market.yandex.ru") || 
                urlLower.contains("yandex.ru/product") ||
                urlLower.contains("yandex.ru/catalog")) {
                return true
            }
        }
        
        // Проверяем по магазину
        val shopName = product.cheapestShop.lowercase()
        if (shopName.contains("яндекс") || shopName.contains("yandex") || 
            shopName.contains("маркет") || shopName.contains("market")) {
            return true
        }
        
        // Проверяем по наличию brand и model (товары из Яндекс.Маркета обычно имеют эти поля)
        // и URL указывает на Яндекс.Маркет
        val hasBrandAndModel = product.brand.isNotEmpty() && 
                              product.brand != "Не указан" &&
                              product.model.isNotEmpty() && 
                              product.model != "Не указана"
        
        if (hasBrandAndModel) {
            // Если есть brand и model, и URL содержит yandex или market, это товар из Яндекс.Маркета
            if (!url.isNullOrEmpty()) {
                val urlLower = url.lowercase()
                if (urlLower.contains("yandex") || urlLower.contains("market")) {
                    return true
                }
            }
            // Если нет URL, но есть brand и model, и магазин не указан или содержит яндекс/маркет
            if (shopName.isEmpty() || shopName == "не указан" || 
                shopName.contains("яндекс") || shopName.contains("yandex") ||
                shopName.contains("маркет") || shopName.contains("market")) {
                return true
            }
        }
        
        return false
    }

}

