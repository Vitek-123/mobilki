package com.example.test

import retrofit2.Call
import retrofit2.Response
import retrofit2.http.*

interface ApiService {
    @POST("/add_user")
    fun registerUser(@Body user: CreateUserRequest): Call<UserResponse>

    @POST("/login")
    fun loginUser(@Body loginData: LoginRequest): Call<LoginResponse>

    @GET("/products")
    fun getProducts(
        @Query("skip") skip: Int = 0,
        @Query("limit") limit: Int = 50,
        @Query("search") search: String? = null
    ): Call<ProductsResponse>

    @GET("/products/{id}")
    fun getProductById(@Path("id") productId: Int): Call<ProductWithPricesResponse>
    
    // Suspend функции для работы с корутинами
    @GET("/products")
    suspend fun getProductsSuspend(
        @Query("skip") skip: Int = 0,
        @Query("limit") limit: Int = 50,
        @Query("search") search: String? = null
    ): Response<ProductsResponse>
    
    @GET("/products/popular")
    suspend fun getPopularProducts(
        @Query("limit") limit: Int = 10,
        @Query("use_cache") useCache: Boolean = true,
        @Query("category") category: String = "электроника"
    ): Response<ProductsResponse>
    
    @GET("/products/{id}")
    suspend fun getProductByIdSuspend(@Path("id") productId: Int): Response<ProductWithPricesResponse>
    
    // История просмотров
    @POST("/user/view-history")
    suspend fun addViewHistory(@Query("product_id") productId: Int): Response<ViewHistoryResponse>
    
    @GET("/user/view-history")
    suspend fun getViewHistory(
        @Query("skip") skip: Int = 0,
        @Query("limit") limit: Int = 50
    ): Response<ViewHistoryListResponse>
    
    @DELETE("/user/view-history")
    suspend fun clearViewHistory(): Response<Map<String, String>>
    
    // Избранное
    @POST("/favorites/{product_id}")
    suspend fun addToFavorites(@Path("product_id") productId: Int): Response<FavoriteResponse>
    
    @GET("/favorites")
    suspend fun getFavorites(
        @Query("skip") skip: Int = 0,
        @Query("limit") limit: Int = 50
    ): Response<FavoritesListResponse>
    
    @DELETE("/favorites/{product_id}")
    suspend fun removeFromFavorites(@Path("product_id") productId: Int): Response<Map<String, String>>
    
    // Отслеживание цен
    @POST("/user/price-alerts")
    suspend fun createPriceAlert(@Body alert: PriceAlertCreate): Response<PriceAlertResponse>
    
    @GET("/user/price-alerts")
    suspend fun getPriceAlerts(
        @Query("skip") skip: Int = 0,
        @Query("limit") limit: Int = 50
    ): Response<PriceAlertsListResponse>
    
    @DELETE("/user/price-alerts/{alert_id}")
    suspend fun deletePriceAlert(@Path("alert_id") alertId: Int): Response<Map<String, String>>
    
    // Статистика
    @GET("/user/stats")
    suspend fun getUserStats(): Response<UserStatsResponse>
    
    // Очистка кэша
    @DELETE("/cache/clear-all")
    suspend fun clearAllCache(): Response<Map<String, String>>
}