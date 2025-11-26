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

class ProductAdapter(
    private var productList: List<Product>,
    private val context: Context,
    private val onItemClickListener: OnItemClickListener? = null
) : RecyclerView.Adapter<ProductAdapter.ProductViewHolder>() {

    interface OnItemClickListener {
        fun onProductClick(product: Product)
        fun onBuyButtonClick(product: Product)
    }

    private var allProducts: List<Product> = productList

    inner class ProductViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        val productImage: ImageView = itemView.findViewById(R.id.Product_imageView_product)
        val productTitle: TextView = itemView.findViewById(R.id.Product_TextView_title)
        val productDescription: TextView = itemView.findViewById(R.id.Product_TextView_desc)
        val productPrice: TextView = itemView.findViewById(R.id.Product_TextView_price)
        val buyButton: Button = itemView.findViewById(R.id.Product_Button_product)

        init {
            itemView.setOnClickListener {
                val position = adapterPosition
                if (position != RecyclerView.NO_POSITION) {
                    onItemClickListener?.onProductClick(productList[position])
                }
            }

            buyButton.setOnClickListener {
                val position = adapterPosition
                if (position != RecyclerView.NO_POSITION) {
                    onItemClickListener?.onBuyButtonClick(productList[position])
                }
            }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ProductViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.product_item, parent, false)
        return ProductViewHolder(view)
    }

    override fun onBindViewHolder(holder: ProductViewHolder, position: Int) {
        val product = productList[position]

        // Загрузка изображения
        if (product.image.isNotEmpty()) {
            Glide.with(context)
                .load(product.image)
                .into(holder.productImage)
        } else {
            holder.productImage.visibility = View.GONE
        }

        // Установка данных
        holder.productTitle.text = product.getFullName()
        holder.productDescription.text = product.description
        holder.productPrice.text = product.getFormattedPrice()

        // Установка текста кнопки
        if (product.shopCount > 1) {
            holder.buyButton.text = "Купить в ${product.shopCount} магазинах"
        } else {
            holder.buyButton.text = if (product.cheapestShop.isNotEmpty() && product.cheapestShop != "Не указан") {
                "Купить в ${product.cheapestShop}"
            } else {
                "Купить"
            }
        }
    }

    override fun getItemCount(): Int = productList.size

    fun updateData(newProductList: List<Product>) {
        productList = newProductList
        allProducts = newProductList
        notifyDataSetChanged()
    }

    fun filterProducts(query: String) {
        val filteredList = if (query.isEmpty()) {
            allProducts // При пустом запросе показываем ВЕСЬ список
        } else {
            allProducts.filter { product ->
                product.title.contains(query, true) ||
                        product.brand.contains(query, true) ||
                        product.model.contains(query, true) ||
                        product.description.contains(query, true)
            }
        }
        productList = filteredList
        notifyDataSetChanged()
    }

    fun resetFilter() {
        productList = allProducts
        notifyDataSetChanged()
    }
}