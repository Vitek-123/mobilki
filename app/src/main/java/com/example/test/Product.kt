package com.example.test

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
) {
    fun getFormattedPrice(): String {
        return try {
            if (price != null && price > 0) {
                String.format("%,.0f ₽", price)
            } else {
                "Цена не указана"
            }
        } catch (e: Exception) {
            "Цена не указана"
        }
    }

    fun getFullName(): String {
        return try {
            val brandPart = if (brand.isNotEmpty() && brand != "Не указан") brand else ""
            val modelPart = if (model.isNotEmpty() && model != "Не указана") model else ""

            val fullName = "$brandPart $modelPart".trim()
            if (fullName.isNotEmpty()) fullName else title
        } catch (e: Exception) {
            title.ifEmpty { "Без названия" }
        }
    }

    fun hasValidPrice(): Boolean {
        return price != null && price > 0
    }

    fun getShopCountText(): String {
        return when (shopCount) {
            0 -> "Нет в продаже"
            1 -> "1 магазин"
            else -> "$shopCount магазинов"
        }
    }

    fun getCheapestShopText(): String {
        return when {
            cheapestShop.isNotEmpty() && cheapestShop != "Не указан" -> cheapestShop
            else -> "Неизвестный магазин"
        }
    }
}

