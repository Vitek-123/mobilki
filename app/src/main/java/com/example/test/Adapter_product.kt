package com.example.test

import android.content.Context
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.ImageView
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.RecyclerView
import com.bumptech.glide.Glide
import com.bumptech.glide.load.DataSource
import com.bumptech.glide.load.engine.GlideException
import com.bumptech.glide.load.resource.drawable.DrawableTransitionOptions
import com.bumptech.glide.request.RequestListener
import com.bumptech.glide.request.target.Target
import android.graphics.drawable.Drawable
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
        val productPrice: TextView = itemView.findViewById(R.id.Product_TextView_price)
        val buyButton: Button = itemView.findViewById(R.id.Product_Button_product)

        init {
            // Делаем картинку кликабельной для открытия ссылки на магазин
            productImage.isClickable = true
            productImage.isFocusable = true
            
            // Обработчик клика на картинку - открываем ссылку на магазин
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
            
            // Обработчик клика на всю карточку - открываем магазин
            itemView.setOnClickListener { view ->
                try {
                    val position = bindingAdapterPosition
                    if (position != RecyclerView.NO_POSITION && position < productList.size) {
                        val product = productList[position]
                        if (product.id > 0 && onItemClickListener != null) {
                            // Открываем магазин вместо страницы деталей
                            onItemClickListener.onBuyButtonClick(product)
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
                    // Оптимизация: используем thumbnail для быстрой загрузки
                    // и уменьшаем размер изображения для RecyclerView
                    Glide.with(context)
                        .load(imageUrl)
                        .thumbnail(0.1f) // Показываем уменьшенную версию сначала
                        .transition(DrawableTransitionOptions.withCrossFade(200))
                        .placeholder(R.drawable.adapter_placeholder_image)
                        .error(R.drawable.adapter_error_image)
                        .fallback(R.drawable.adapter_placeholder_image)
                        .override(400, 300) // Уменьшен размер для ускорения загрузки
                        .centerCrop()
                        .skipMemoryCache(false) // Используем кэш памяти
                        .diskCacheStrategy(com.bumptech.glide.load.engine.DiskCacheStrategy.AUTOMATIC)
                        .listener(object : RequestListener<Drawable> {
                            override fun onLoadFailed(
                                e: GlideException?,
                                model: Any?,
                                target: Target<Drawable>,
                                isFirstResource: Boolean
                            ): Boolean {
                                // Игнорируем предупреждения о поврежденных JPEG - это не критично
                                val errorMessage = e?.message ?: "Unknown error"
                                if (!errorMessage.contains("Corrupt JPEG", ignoreCase = true) && 
                                    !errorMessage.contains("Inconsistent progression", ignoreCase = true)) {
                                    android.util.Log.w("ProductAdapter", "Ошибка загрузки изображения: $errorMessage, URL: $imageUrl")
                                }
                                return false // Позволяем Glide показать error drawable
                            }

                            override fun onResourceReady(
                                resource: Drawable,
                                model: Any,
                                target: Target<Drawable>,
                                dataSource: DataSource,
                                isFirstResource: Boolean
                            ): Boolean {
                                return false
                            }
                        })
                        .into(imageView)
                }
                else -> {
                    imageView.setImageResource(R.drawable.adapter_placeholder_image)
                }
            }
        } catch (e: Exception) {
            android.util.Log.e("ProductAdapter", "Критическая ошибка при загрузке изображения", e)
            imageView.setImageResource(R.drawable.adapter_error_image)
        }
    }

    private fun isValidUrl(url: String): Boolean {
        return url.startsWith("http://") || url.startsWith("https://")
    }

    private fun setProductTextData(holder: ProductViewHolder, product: Product, context: Context) {
        // Название товара
        holder.productTitle.text = product.getFullName()

        // Цена
        holder.productPrice.text = product.getFormattedPrice(context)

        // Улучшенные контент-дескрипшены для доступности
        val fullName = product.getFullName()
        val price = product.getFormattedPrice(context)
        val shopInfo = when {
            product.shopCount > 1 -> "Доступно в ${product.shopCount} магазинах"
            product.cheapestShop.isNotEmpty() && product.cheapestShop != "Не указан" -> 
                "Доступно в магазине ${product.cheapestShop}"
            else -> "Информация о магазинах недоступна"
        }
        
        holder.productTitle.contentDescription = "Товар: $fullName. $shopInfo"
        holder.productPrice.contentDescription = "Цена товара: $price"
        holder.productImage.contentDescription = "Изображение товара: $fullName"
        
        // Улучшенный contentDescription для кнопки
        val buttonText = holder.buyButton.text.toString()
        holder.buyButton.contentDescription = "Кнопка покупки. $buttonText. Нажмите для открытия магазина"
    }

    private fun setupBuyButton(button: Button, product: Product) {
        val context = button.context
        
        // Проверяем, является ли товар товаром из Яндекс.Маркета
        val isYandexMarketProduct = isYandexMarketProduct(product)
        
        val buttonText = when {
            isYandexMarketProduct -> context.getString(R.string.button_buy_in_yandex_market)
            product.shopCount > 1 -> context.getString(R.string.button_buy_in_shops, product.shopCount)
            product.cheapestShop.isNotEmpty() && product.cheapestShop != "Не указан" ->
                context.getString(R.string.button_buy_in_shop, product.cheapestShop)
            else -> context.getString(R.string.button_buy)
        }

        button.text = buttonText
        button.contentDescription = context.getString(R.string.button_buy) + ": $buttonText"

        // Визуальная обратная связь при наличии цены
        button.isEnabled = product.price != null && product.price > 0
        button.alpha = if (button.isEnabled) 1.0f else 0.6f
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
        if (shopName.contains("яндекс") || shopName.contains("yandex")) {
            return true
        }
        
        // Проверяем по наличию brand и model (товары из Яндекс.Маркета обычно имеют эти поля)
        // и URL указывает на Яндекс.Маркет
        val hasBrandAndModel = product.brand.isNotEmpty() && 
                              product.brand != "Не указан" &&
                              product.model.isNotEmpty() && 
                              product.model != "Не указана"
        
        if (hasBrandAndModel && !url.isNullOrEmpty()) {
            val urlLower = url.lowercase()
            if (urlLower.contains("yandex") || urlLower.contains("market")) {
                return true
            }
        }
        
        return false
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
        val diffCallback = ProductDiffCallback(productList, newProductList)
        val diffResult = DiffUtil.calculateDiff(diffCallback)
        
        productList = newProductList
        allProducts = ArrayList(newProductList) // Создаем копию
        
        diffResult.dispatchUpdatesTo(this)
    }


    // Очистка ресурсов при уничтожении адаптера
    fun cleanup() {
        // Очищаем ссылку на контекст
        contextRef.clear()
    }
}

/**
 * DiffUtil callback для эффективного обновления списка товаров
 */
class ProductDiffCallback(
    private val oldList: List<Product>,
    private val newList: List<Product>
) : DiffUtil.Callback() {

    override fun getOldListSize(): Int = oldList.size

    override fun getNewListSize(): Int = newList.size

    override fun areItemsTheSame(oldItemPosition: Int, newItemPosition: Int): Boolean {
        return oldList[oldItemPosition].id == newList[newItemPosition].id
    }

    override fun areContentsTheSame(oldItemPosition: Int, newItemPosition: Int): Boolean {
        val oldProduct = oldList[oldItemPosition]
        val newProduct = newList[newItemPosition]
        
        return oldProduct.id == newProduct.id &&
                oldProduct.title == newProduct.title &&
                oldProduct.brand == newProduct.brand &&
                oldProduct.model == newProduct.model &&
                oldProduct.price == newProduct.price &&
                oldProduct.image == newProduct.image &&
                oldProduct.shopCount == newProduct.shopCount &&
                oldProduct.cheapestShop == newProduct.cheapestShop &&
                oldProduct.url == newProduct.url
    }

    override fun getChangePayload(oldItemPosition: Int, newItemPosition: Int): Any? {
        // Можно вернуть конкретные изменения для частичного обновления
        // Пока возвращаем null для полного обновления элемента
        return null
    }
}