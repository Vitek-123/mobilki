package com.example.test

data class ApiProduct(
    val id_product: Int,
    val title: String?,
    val brand: String?,
    val model: String?,
    val prices: List<PriceResponse>,
    val min_price: Float?,
    val max_price: Float?
)

data class Product(
    val id: Int,
    val title: String,
    val brand: String,
    val model: String,
    val description: String,
    val image: String, 
    val price: Float?,
    val shopCount: Int,
    val cheapestShop: String
)
{
    // Вспомогательный метод для форматирования цены
    fun getFormattedPrice(): String {
        return if (price != null && price > 0) {
            String.format("%,.0f ₽", price)
        } else {
            "Цена не указана"
        }
    }

    // Метод для получения полного названия
    fun getFullName(): String {
        return if (brand.isNotEmpty() && model.isNotEmpty() && brand != "Не указан" && model != "Не указана") {
            "$brand $model"
        } else {
            title.ifEmpty { "Без названия" }
        }
    }
}