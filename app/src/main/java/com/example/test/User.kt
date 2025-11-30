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
    val image: String?
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
