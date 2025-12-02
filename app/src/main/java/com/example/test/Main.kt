package com.example.test

import android.content.Intent
import android.os.Bundle
import android.view.Menu
import android.view.MenuItem
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
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import kotlinx.coroutines.launch
import kotlinx.coroutines.delay

class Main : BaseActivity() {
    
    private val viewModel: ProductViewModel by viewModels()
    private lateinit var recyclerView: RecyclerView
    private lateinit var adapter: ProductAdapter
    private lateinit var progressBar: ProgressBar
    private lateinit var emptyTextView: TextView
    private lateinit var errorTextView: TextView
    private lateinit var searchView: SearchView
    
    private var currentSearchQuery = ""

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.main)
        
        // Инициализация RetrofitClient
        RetrofitClient.initialize(this)
        
        // Обработка system bars для CoordinatorLayout (без padding снизу, чтобы bottom navigation был виден)
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, 0)
            insets
        }
        
        // Обработка system bars для контента (учитываем bottom navigation)
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.content_container)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            // Padding снизу уже установлен в layout (72dp для bottom navigation)
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, v.paddingBottom + systemBars.bottom)
            insets
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
        adapter = ProductAdapter(
            productList = emptyList(),
            context = this,
            object : ProductAdapter.OnItemClickListener {
                override fun onProductClick(product: Product) {
                    // Открываем детальную страницу товара
                    if (product.id <= 0) {
                        Toast.makeText(this@Main, "Ошибка: неверный ID товара", Toast.LENGTH_SHORT).show()
                        return
                    }
                    try {
                        val intent = Intent(this@Main, ProductDetailActivity::class.java)
                        intent.putExtra("product_id", product.id)
                        startActivity(intent)
                    } catch (e: Exception) {
                        android.util.Log.e("Main", "Error opening product detail", e)
                        Toast.makeText(this@Main, "Ошибка при открытии товара: ${e.message}", Toast.LENGTH_SHORT).show()
                    }
                }

                override fun onBuyButtonClick(product: Product) {
                    // Открываем страницу сравнения магазинов
                    android.util.Log.d("Main", "Buy button clicked for product: ${product.title}, ID: ${product.id}")
                    if (product.id <= 0) {
                        Toast.makeText(this@Main, "Ошибка: неверный ID товара", Toast.LENGTH_SHORT).show()
                        return
                    }
                    val intent = Intent(this@Main, ShopComparisonActivity::class.java)
                    intent.putExtra("product_id", product.id)
                    startActivity(intent)
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
                if (visibleItemCount + firstVisibleItemPosition >= totalItemCount - 5) {
                    viewModel.loadMoreProducts(currentSearchQuery)
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
                    showLoading(true)
                    hideError()
                    hideEmpty()
                }
                is Resource.Success -> {
                    showLoading(false)
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

    override fun onCreateOptionsMenu(menu: Menu?): Boolean {
        // Можно добавить меню, если нужно
        return super.onCreateOptionsMenu(menu)
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return super.onOptionsItemSelected(item)
    }
}

