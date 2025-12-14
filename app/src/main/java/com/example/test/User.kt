package com.example.test

import java.util.Date

data class CreateUserRequest(
    val login: String,
    val email: String,
    val password: String
)

data class UserResponse(
    val id_user: Int,
    val login: String,
    val email: String
)

data class LoginRequest(
    val login: String,
    val password: String
)

data class LoginResponse(
    val access_token: String,
    val token_type: String,
    val user: UserResponse
)


//Продукты

data class ProductResponse(
    val id_product: Int,
    val title: String?,
    val description: String?,
    val brand: String?,
    val model: String?,
    val image: String?,
    val url: String? = null  // URL товара (для товаров из Яндекс.Маркет)
)

data class PriceResponse(
    val price: Float,
    val scraped_at: String,
    val shop_name: String,
    val shop_id: Int,
    val url: String?
)

data class ProductWithPricesResponse(
    val product: ProductResponse,
    val prices: List<PriceResponse>,
    val min_price: Float?,
    val max_price: Float?
)

data class ProductsResponse(
    val products: List<ProductWithPricesResponse>,
    val total: Int
)

// История просмотров
data class ViewHistoryResponse(
    val id_view: Int,
    val product: ProductWithPricesResponse,
    val viewed_at: String
)

data class ViewHistoryListResponse(
    val views: List<ViewHistoryResponse>,
    val total: Int
)

// Избранное
data class FavoriteResponse(
    val id_favorite: Int,
    val product: ProductWithPricesResponse,
    val added_at: String
)

data class FavoritesListResponse(
    val favorites: List<FavoriteResponse>,
    val total: Int
)

// Отслеживание цен
data class PriceAlertCreate(
    val product_id: Int,
    val target_price: Float
)

data class PriceAlertResponse(
    val id_alert: Int,
    val product: ProductWithPricesResponse,
    val target_price: Float,
    val is_active: Boolean,
    val created_at: String
)

data class PriceAlertsListResponse(
    val alerts: List<PriceAlertResponse>,
    val total: Int
)

// Статистика
data class UserStatsResponse(
    val viewed_count: Int,
    val favorites_count: Int,
    val alerts_count: Int,
    val shopping_lists_count: Int,
    val comparisons_count: Int,
    val reviews_count: Int
)
