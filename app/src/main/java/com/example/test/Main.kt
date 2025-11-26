package com.example.test

import android.net.ConnectivityManager
import android.os.Bundle
import android.view.View
import android.widget.ProgressBar
import android.widget.SearchView
import android.widget.Toast
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class Main : AppCompatActivity(), ProductAdapter.OnItemClickListener {

    private lateinit var recyclerView: RecyclerView
    private lateinit var productAdapter: ProductAdapter
    private lateinit var searchView: SearchView
    private lateinit var progressBar: ProgressBar
    private val productList = mutableListOf<Product>()
    private var allProducts = listOf<Product>()


    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.main)
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom)
            insets
        }

        initViews()
        initRecyclerView()
        setupSearchView()

        if (!isNetworkAvailable()) {
            showAlertDialog("Ошибка сети", "Отсутствует подключение к интернету")
        } else {
            loadProductsFromApi()
        }
    }

    private fun initViews() {
        recyclerView = findViewById(R.id.Main_RecyclerView_product)
        searchView = findViewById(R.id.Main_SearchView)
        progressBar = findViewById(R.id.Main_progressBar)
    }

    private fun initRecyclerView() {
        recyclerView.layoutManager = LinearLayoutManager(this)
        productAdapter = ProductAdapter(productList, this, this)
        recyclerView.adapter = productAdapter
    }

    private fun setupSearchView() {
        searchView.setOnQueryTextListener(object : SearchView.OnQueryTextListener {
            override fun onQueryTextSubmit(query: String): Boolean {
                productAdapter.filterProducts(query)
                return true
            }

            override fun onQueryTextChange(newText: String): Boolean {
                productAdapter.filterProducts(newText)
                return true
            }
        })

        searchView.setOnCloseListener {
            productAdapter.resetFilter()
            false
        }
    }


    private fun loadProductsFromApi() {
        showLoading(true)

        RetrofitClient.apiService.getProducts().enqueue(object : Callback<ProductsResponse> {
            override fun onResponse(call: Call<ProductsResponse>, response: Response<ProductsResponse>) {
                showLoading(false)

                if (response.isSuccessful) {
                    val productsResponse = response.body()
                    productsResponse?.let {
                        val convertedProducts = convertApiProductsToAppProducts(it.products)
                        productList.clear()
                        productList.addAll(convertedProducts)
                        allProducts = convertedProducts
                        productAdapter.updateData(productList)

                        if (productList.isEmpty()) {
                            Toast.makeText(this@Main, "Товары не найдены", Toast.LENGTH_SHORT).show()
                        } else {
                            false
                        }
                    }
                } else {
                    showAlertDialog("Ошибка", "Ошибка загрузки товаров: ${response.code()}")
                }
            }

            override fun onFailure(call: Call<ProductsResponse>, t: Throwable) {
                showLoading(false)
                showAlertDialog("Ошибка сети", "Не удалось загрузить товары: ${t.message}")
            }
        })
    }


    private fun convertApiProductsToAppProducts(apiProducts: List<ProductWithPricesResponse>): List<Product> {
        return apiProducts.mapNotNull { apiProduct ->
            try {
                val product = apiProduct.product
                val prices = apiProduct.prices

                val cheapestPriceInfo = prices.minByOrNull { it.price }
                val minPrice = apiProduct.min_price ?: cheapestPriceInfo?.price
                val cheapestShop = cheapestPriceInfo?.shop_name ?: "Не указан"


                Product(
                    id = product.id_product,
                    title = product.title ?: "${product.brand} ${product.model}",
                    brand = product.brand ?: "Не указан",
                    model = product.model ?: "Не указана",
                    description = product.description ?: "Описание не указано",
                    image = product.image ?: "https://yandex.ru/images/search?pos=0&from=tabbar&img_url=https%3A%2F%2Fi.ytimg.com%2Fvi%2F3we_qAN-BzI%2Fmaxresdefault.jpg&text=загрузка&rpt=simage&lr=213",
                    price = minPrice,
                    shopCount = apiProduct.prices.size,
                    cheapestShop = cheapestShop
                )
            } catch (e: Exception) {
                null
            }
        }
    }


    private fun isNetworkAvailable(): Boolean {
        val connectivityManager = getSystemService(ConnectivityManager::class.java)
        val networkInfo = connectivityManager.activeNetworkInfo
        return networkInfo != null && networkInfo.isConnected
    }

    private fun showAlertDialog(title: String, message: String) {
        runOnUiThread {
            AlertDialog.Builder(this@Main)
                .setTitle(title)
                .setMessage(message)
                .setPositiveButton("OK", null)
                .create()
                .show()
        }
    }

    private fun showLoading(show: Boolean) {
        if (show) {
            progressBar.visibility = View.VISIBLE
            recyclerView.visibility = View.GONE
        } else {
            progressBar.visibility = View.GONE
            recyclerView.visibility = View.VISIBLE
        }
    }

    override fun onProductClick(product: Product) {
        Toast.makeText(this, "Выбран: ${product.title}", Toast.LENGTH_SHORT).show()
        // TODO: Переход на экран деталей товара
    }

    override fun onBuyButtonClick(product: Product) {
        Toast.makeText(this, "Переход в магазин: ${product.cheapestShop}", Toast.LENGTH_SHORT).show()
        // TODO: Открытие ссылки на товар в магазине
    }
}