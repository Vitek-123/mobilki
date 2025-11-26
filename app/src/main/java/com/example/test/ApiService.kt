package com.example.test

import retrofit2.Call
import retrofit2.http.*

interface ApiService {

    @POST("/add_user")
    fun registerUser(@Body user: CreateUserRequest): Call<UserResponse>

    @POST("/login")
    fun loginUser(@Body loginData: LoginRequest): Call<LoginResponse>

    // Новые методы для продуктов
    @GET("/products")
    fun getProducts(
        @Query("skip") skip: Int = 0,
        @Query("limit") limit: Int = 50,
        @Query("search") search: String? = null
    ): Call<ProductsResponse>

    @GET("/products/{id}")
    fun getProductById(@Path("id") productId: Int): Call<ProductWithPricesResponse>
}