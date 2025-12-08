package com.example.test

import android.content.Context
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.ImageView
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.bumptech.glide.Glide
import com.bumptech.glide.load.resource.drawable.DrawableTransitionOptions
import java.lang.ref.WeakReference

class ProductAdapter(
    private var productList: List<Product>,
    context: Context,
    private val onItemClickListener: OnItemClickListener? = null
) : RecyclerView.Adapter<ProductAdapter.ProductViewHolder>() {

    interface OnItemClickListener {
        fun onProductClick(product: Product)
        fun onBuyButtonClick(product: Product)
    }

    // Используем WeakReference для предотвращения утечек памяти
    private val contextRef = WeakReference(context)
    private var allProducts: List<Product> = productList

    inner class ProductViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        val productImage: ImageView = itemView.findViewById(R.id.Product_imageView_product)
        val productTitle: TextView = itemView.findViewById(R.id.Product_TextView_title)
        val productDescription: TextView = itemView.findViewById(R.id.Product_TextView_desc)
        val productPrice: TextView = itemView.findViewById(R.id.Product_TextView_price)
        val buyButton: Button = itemView.findViewById(R.id.Product_Button_product)

        init {
            // Делаем картинку кликабельной для открытия ссылки на Яндекс.Маркет
            productImage.isClickable = true
            productImage.isFocusable = true
            
            // Обработчик клика на картинку - открываем ссылку на Яндекс.Маркет
            productImage.setOnClickListener { view ->
                try {
                    // Предотвращаем всплытие события на itemView
                    view?.let {
                        val position = bindingAdapterPosition
                        if (position != RecyclerView.NO_POSITION && position < productList.size) {
                            val product = productList[position]
                            if (product.id > 0 && onItemClickListener != null) {
                                onItemClickListener.onBuyButtonClick(product)
                            }
                        }
                    }
                } catch (e: Exception) {
                    android.util.Log.e("ProductAdapter", "Error handling image click", e)
                }
            }
            
            // Обработчик клика на всю карточку (кроме картинки и кнопки)
            itemView.setOnClickListener { view ->
                try {
                    val position = bindingAdapterPosition
                    if (position != RecyclerView.NO_POSITION && position < productList.size) {
                        val product = productList[position]
                        if (product.id > 0 && onItemClickListener != null) {
                            onItemClickListener.onProductClick(product)
                        }
                    }
                } catch (e: Exception) {
                    android.util.Log.e("ProductAdapter", "Error handling item click", e)
                }
            }

            // Обработчик клика на кнопку покупки
            buyButton.setOnClickListener { view ->
                try {
                    // Предотвращаем всплытие события на itemView
                    view?.let {
                        val position = bindingAdapterPosition
                        if (position != RecyclerView.NO_POSITION && position < productList.size) {
                            val product = productList[position]
                            if (product.id > 0 && onItemClickListener != null) {
                                onItemClickListener.onBuyButtonClick(product)
                            }
                        }
                    }
                } catch (e: Exception) {
                    android.util.Log.e("ProductAdapter", "Error handling buy button click", e)
                }
            }
        }

        // Метод для очистки ресурсов при переиспользовании ViewHolder
        fun clearResources() {
            // Отменяем загрузку изображения для предотвращения утечек памяти
            Glide.with(itemView).clear(productImage)
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ProductViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.product_item, parent, false)
        return ProductViewHolder(view)
    }

    override fun onBindViewHolder(holder: ProductViewHolder, position: Int) {
        val context = contextRef.get() ?: return // Проверяем, что контекст еще доступен
        val product = productList[position]

        bindProductData(holder, product, context)
    }

    private fun bindProductData(holder: ProductViewHolder, product: Product, context: Context) {
        // Загрузка изображения с улучшенной обработкой ошибок
        loadProductImage(holder.productImage, product.image, context)

        // Установка текстовых данных
        setProductTextData(holder, product, context)

        // Настройка кнопки покупки
        setupBuyButton(holder.buyButton, product)
    }

    private fun loadProductImage(imageView: ImageView, imageUrl: String?, context: Context) {
        try {
            imageView.visibility = View.VISIBLE

            when {
                !imageUrl.isNullOrEmpty() && imageUrl != "default" && isValidUrl(imageUrl) -> {
                    Glide.with(context)
                        .load(imageUrl)
                        .transition(DrawableTransitionOptions.withCrossFade(300))
                        .placeholder(R.drawable.adapter_placeholder_image)
                        .error(R.drawable.adapter_error_image)
                        .fallback(R.drawable.adapter_placeholder_image)
                        .override(600, 400) // Оптимальный размер для уменьшения использования памяти
                        .centerCrop()
                        .into(imageView)
                }
                else -> {
                    imageView.setImageResource(R.drawable.adapter_placeholder_image)
                }
            }
        } catch (e: Exception) {
            imageView.setImageResource(R.drawable.adapter_error_image)
        }
    }

    private fun isValidUrl(url: String): Boolean {
        return url.startsWith("http://") || url.startsWith("https://")
    }

    private fun setProductTextData(holder: ProductViewHolder, product: Product, context: Context) {
        // Название товара
        holder.productTitle.text = product.getFullName()

        // Описание товара
        val description = product.description ?: "Описание не указано"
        holder.productDescription.text = if (description.length > 150) {
            "${description.substring(0, 147)}..."
        } else {
            description
        }

        // Цена
        holder.productPrice.text = product.getFormattedPrice(context)

        // Установка контент-дескрипшена для доступности
        holder.productTitle.contentDescription = "Название товара: ${product.getFullName()}"
        holder.productDescription.contentDescription = "Описание товара: $description"
        holder.productPrice.contentDescription = "Цена: ${product.getFormattedPrice(context)}"
    }

    private fun setupBuyButton(button: Button, product: Product) {
        val buttonText = when {
            product.shopCount > 1 -> "Купить в ${product.shopCount} магазинах"
            product.cheapestShop.isNotEmpty() && product.cheapestShop != "Не указан" ->
                "Купить в ${product.cheapestShop}"
            else -> "Купить"
        }

        button.text = buttonText
        button.contentDescription = "Кнопка покупки: $buttonText"

        // Визуальная обратная связь при наличии цены
        button.isEnabled = product.price != null && product.price > 0
        button.alpha = if (button.isEnabled) 1.0f else 0.6f
    }

    override fun getItemCount(): Int = productList.size

    override fun getItemId(position: Int): Long {
        return productList[position].id.toLong()
    }

    override fun onViewRecycled(holder: ProductViewHolder) {
        super.onViewRecycled(holder)
        // Очищаем ресурсы при переиспользовании ViewHolder
        holder.clearResources()
    }

    fun updateData(newProductList: List<Product>) {
        productList = newProductList
        allProducts = ArrayList(newProductList) // Создаем копию
        notifyDataSetChanged()
    }

    fun filterProducts(query: String) {
        val filteredList = if (query.isEmpty()) {
            allProducts
        } else {
            val searchQuery = query.toLowerCase().trim()
            allProducts.filter { product ->
                product.title.contains(searchQuery, true) ||
                        product.brand.contains(searchQuery, true) ||
                        product.model.contains(searchQuery, true) ||
                        (product.description?.contains(searchQuery, true) == true) ||
                        product.getFullName().contains(searchQuery, true)
            }
        }
        productList = filteredList
        notifyDataSetChanged()
    }

    fun resetFilter() {
        productList = allProducts
        notifyDataSetChanged()
    }

    // Метод для получения продукта по позиции
    fun getProductAt(position: Int): Product? {
        return if (position in 0 until itemCount) {
            productList[position]
        } else {
            null
        }
    }

    // Метод для обновления отдельного элемента
    fun updateItem(position: Int, product: Product) {
        if (position in 0 until itemCount) {
            // Обновляем в основном списке
            val mutableList = productList.toMutableList()
            mutableList[position] = product
            productList = mutableList

            // Обновляем в полном списке
            val mutableAllList = allProducts.toMutableList()
            val indexInAll = allProducts.indexOfFirst { it.id == product.id }
            if (indexInAll != -1) {
                mutableAllList[indexInAll] = product
                allProducts = mutableAllList
            }

            notifyItemChanged(position)
        }
    }

    // Очистка ресурсов при уничтожении адаптера
    fun cleanup() {
        // Очищаем ссылку на контекст
        contextRef.clear()
    }
}