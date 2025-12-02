package com.example.test

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import retrofit2.Response
import java.text.SimpleDateFormat
import java.util.*

class ShopComparisonActivity : AppCompatActivity() {

    private lateinit var recyclerView: RecyclerView
    private lateinit var progressBar: ProgressBar
    private lateinit var errorTextView: TextView
    private lateinit var productNameTextView: TextView
    private lateinit var productInfoTextView: TextView
    private lateinit var adapter: ShopPriceAdapter

    private var productId: Int = -1

    override fun onCreate(savedInstanceState: Bundle?) {
        // Применяем тему перед setContentView
        ThemeUtils.applyTheme(this)
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_shop_comparison)
        
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom)
            insets
        }

        // Инициализация RetrofitClient
        RetrofitClient.initialize(this)

        // Получаем ID товара из Intent
        productId = intent.getIntExtra("product_id", -1)
        if (productId == -1) {
            android.util.Log.e("ShopComparison", "Product ID not found in Intent")
            Toast.makeText(this, "Ошибка: товар не найден. ID: $productId", Toast.LENGTH_LONG).show()
            finish()
            return
        }
        android.util.Log.d("ShopComparison", "Received product ID: $productId")

        initViews()
        setupRecyclerView()
        loadProductPrices()
    }

    private fun initViews() {
        recyclerView = findViewById(R.id.ShopComparison_recyclerView)
        progressBar = findViewById(R.id.ShopComparison_progressBar)
        errorTextView = findViewById(R.id.ShopComparison_textView_error)
        productNameTextView = findViewById(R.id.ShopComparison_textView_productName)
        productInfoTextView = findViewById(R.id.ShopComparison_textView_productInfo)
    }

    private fun setupRecyclerView() {
        adapter = ShopPriceAdapter(emptyList()) { priceResponse ->
            // Открываем URL магазина
            priceResponse.url?.let { url ->
                try {
                    val intent = Intent(Intent.ACTION_VIEW, Uri.parse(url))
                    startActivity(intent)
                } catch (e: Exception) {
                    Toast.makeText(this, "Не удалось открыть ссылку", Toast.LENGTH_SHORT).show()
                }
            } ?: run {
                Toast.makeText(this, "Ссылка недоступна", Toast.LENGTH_SHORT).show()
            }
        }

        recyclerView.layoutManager = LinearLayoutManager(this)
        recyclerView.adapter = adapter
    }

    private fun loadProductPrices() {
        showLoading(true)
        hideError()

        CoroutineScope(Dispatchers.IO).launch {
            try {
                android.util.Log.d("ShopComparison", "Loading product prices for ID: $productId")
                val response: Response<ProductWithPricesResponse> = 
                    RetrofitClient.apiService.getProductByIdSuspend(productId)

                withContext(Dispatchers.Main) {
                    showLoading(false)

                    if (response.isSuccessful) {
                        val productData = response.body()
                        if (productData != null) {
                            // Отображаем информацию о товаре
                            displayProductInfo(productData)
                            
                            if (productData.prices.isEmpty()) {
                                showError("Нет доступных цен для этого товара")
                                productNameTextView.visibility = View.VISIBLE
                                productInfoTextView.visibility = View.VISIBLE
                            } else {
                                // Показываем информацию о товаре
                                productNameTextView.visibility = View.VISIBLE
                                productInfoTextView.visibility = View.VISIBLE
                                
                                // Сортируем цены по возрастанию
                                val sortedPrices = productData.prices.sortedBy { it.price }
                                val cheapestPrice = sortedPrices.firstOrNull()?.price
                                adapter.updatePrices(sortedPrices, cheapestPrice)
                                
                                // Показываем RecyclerView
                                recyclerView.visibility = View.VISIBLE
                            }
                        } else {
                            showError("Пустой ответ от сервера")
                        }
                    } else {
                        val errorBody = response.errorBody()?.string()
                        android.util.Log.e("ShopComparison", "Error ${response.code()}: $errorBody")
                        val errorMessage = when (response.code()) {
                            404 -> "Товар не найден"
                            500 -> "Ошибка сервера. Проверьте подключение к БД"
                            else -> "Ошибка загрузки: ${response.code()}"
                        }
                        showError(errorMessage)
                        Toast.makeText(this@ShopComparisonActivity, errorMessage, Toast.LENGTH_LONG).show()
                    }
                }
            } catch (e: Exception) {
                android.util.Log.e("ShopComparison", "Exception loading prices", e)
                withContext(Dispatchers.Main) {
                    showLoading(false)
                    val errorMsg = "Не удалось загрузить цены: ${e.message ?: "Неизвестная ошибка"}"
                    showError(errorMsg)
                    Toast.makeText(this@ShopComparisonActivity, errorMsg, Toast.LENGTH_LONG).show()
                }
            }
        }
    }

    private fun showLoading(show: Boolean) {
        progressBar.visibility = if (show) View.VISIBLE else View.GONE
        recyclerView.visibility = if (show) View.GONE else View.VISIBLE
    }

    private fun showError(message: String) {
        errorTextView.text = message
        errorTextView.visibility = View.VISIBLE
        recyclerView.visibility = View.GONE
        productNameTextView.visibility = View.GONE
        productInfoTextView.visibility = View.GONE
    }

    private fun hideError() {
        errorTextView.visibility = View.GONE
    }
    
    private fun displayProductInfo(productData: ProductWithPricesResponse) {
        val product = productData.product
        
        // Название товара
        val productTitle = product.title ?: "${product.brand} ${product.model}".trim()
        productNameTextView.text = productTitle
        
        // Информация о товаре (бренд/модель)
        val brandModel = buildString {
            if (!product.brand.isNullOrEmpty()) append(product.brand)
            if (!product.brand.isNullOrEmpty() && !product.model.isNullOrEmpty()) append(" / ")
            if (!product.model.isNullOrEmpty()) append(product.model)
        }
        productInfoTextView.text = brandModel.ifEmpty { "Информация не указана" }
    }

    // Адаптер для списка цен
    private class ShopPriceAdapter(
        private var prices: List<PriceResponse>,
        private val onShopClick: (PriceResponse) -> Unit
    ) : RecyclerView.Adapter<ShopPriceAdapter.ShopPriceViewHolder>() {
        
        private var cheapestPrice: Float? = null

        inner class ShopPriceViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
            val cardView: androidx.cardview.widget.CardView = itemView as androidx.cardview.widget.CardView
            val bestPriceBadge: TextView = itemView.findViewById(R.id.ShopPrice_textView_bestPrice)
            val shopNameTextView: TextView = itemView.findViewById(R.id.ShopPrice_textView_shopName)
            val priceTextView: TextView = itemView.findViewById(R.id.ShopPrice_textView_price)
            val dateTextView: TextView = itemView.findViewById(R.id.ShopPrice_textView_date)
            val openButton: Button = itemView.findViewById(R.id.ShopPrice_button_open)
        }

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ShopPriceViewHolder {
            val cardView = LayoutInflater.from(parent.context)
                .inflate(R.layout.item_shop_price, parent, false) as androidx.cardview.widget.CardView
            return ShopPriceViewHolder(cardView)
        }

        override fun onBindViewHolder(holder: ShopPriceViewHolder, position: Int) {
            if (position >= prices.size) {
                android.util.Log.e("ShopPriceAdapter", "Position $position out of bounds, size: ${prices.size}")
                return
            }
            
            val price = prices[position]
            val isCheapest = cheapestPrice != null && price.price == cheapestPrice

            try {
                holder.shopNameTextView.text = price.shop_name ?: "Неизвестный магазин"
                holder.priceTextView.text = String.format("%,.0f ₽", price.price)
                
                // Выделяем самую дешевую цену
                if (isCheapest) {
                    // Показываем бейдж "Самая дешевая"
                    holder.bestPriceBadge.visibility = View.VISIBLE
                    
                    // Выделяем цену цветом
                    holder.priceTextView.setTextColor(0xFF4CAF50.toInt()) // Зеленый
                    holder.priceTextView.textSize = 30f // Немного больше
                    
                    // Выделяем карточку цветом
                    holder.cardView.setCardBackgroundColor(0xFFE8F5E9.toInt()) // Светло-зеленый
                } else {
                    // Обычное отображение
                    holder.bestPriceBadge.visibility = View.GONE
                    holder.priceTextView.setTextColor(0xFF000000.toInt()) // Черный
                    holder.priceTextView.textSize = 28f
                    
                    // Обычный фон карточки
                    holder.cardView.setCardBackgroundColor(0xFFFFFFFF.toInt()) // Белый
                }
            } catch (e: Exception) {
                android.util.Log.e("ShopPriceAdapter", "Error binding price: ${e.message}")
                holder.shopNameTextView.text = "Ошибка"
                holder.priceTextView.text = "Ошибка"
            }

            // Форматируем дату
            try {
                val scrapedAt = price.scraped_at
                if (!scrapedAt.isNullOrEmpty()) {
                    // Пробуем разные форматы даты
                    val formats = listOf(
                        "yyyy-MM-dd'T'HH:mm:ss",
                        "yyyy-MM-dd'T'HH:mm:ss.SSS",
                        "yyyy-MM-dd HH:mm:ss",
                        "yyyy-MM-dd"
                    )
                    
                    var parsed = false
                    for (format in formats) {
                        try {
                            val dateFormat = SimpleDateFormat(format, Locale.getDefault())
                            val date = dateFormat.parse(scrapedAt)
                            if (date != null) {
                                val displayFormat = SimpleDateFormat("dd.MM.yyyy HH:mm", Locale.getDefault())
                                holder.dateTextView.text = "Обновлено: ${displayFormat.format(date)}"
                                parsed = true
                                break
                            }
                        } catch (e: Exception) {
                            // Пробуем следующий формат
                        }
                    }
                    
                    if (!parsed) {
                        holder.dateTextView.text = "Обновлено: $scrapedAt"
                    }
                } else {
                    holder.dateTextView.text = "Дата не указана"
                }
            } catch (e: Exception) {
                android.util.Log.e("ShopPriceAdapter", "Error parsing date: ${e.message}")
                holder.dateTextView.text = "Дата: ${price.scraped_at ?: "не указана"}"
            }

            holder.openButton.setOnClickListener {
                onShopClick(price)
            }
        }

        override fun getItemCount(): Int = prices.size

        fun updatePrices(newPrices: List<PriceResponse>, cheapest: Float?) {
            prices = newPrices
            cheapestPrice = cheapest
            notifyDataSetChanged()
        }
    }
}

