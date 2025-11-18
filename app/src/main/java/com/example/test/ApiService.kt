package com.example.test

import retrofit2.Call
import retrofit2.http.*

interface ApiService {

    @POST("/add_user")
    fun registerUser(@Body user: CreateUserRequest): Call<UserResponse>

    @POST("login")
    fun loginUser(@Body loginData: LoginRequest): Call<LoginResponse>

    @GET("users/{user_id}")
    fun getUserById(@Path("user_id") userId: Int): Call<UserResponse>

    @GET("users")
    fun getAllUsers(): Call<List<UserResponse>>

    @GET("health")
    fun healthCheck(): Call<Map<String, String>>
}