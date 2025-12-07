package com.example.test

import android.content.Context
import android.util.Log
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object RetrofitClient {

    private const val BASE_URL = "http://172.20.10.2:8000/" // TODO: Вынести в config

    // Определяем флаг отладки вручную
    private const val DEBUG = true // Меняйте на false для продакшена

    private var authManager: AuthManager? = null

    /**
     * Инициализация RetrofitClient с AuthManager для работы с токенами
     */
    fun initialize(context: Context) {
        authManager = AuthManager.getInstance(context)
    }

    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        // Используем наш флаг DEBUG
        level = if (DEBUG) {
            HttpLoggingInterceptor.Level.BODY
        } else {
            HttpLoggingInterceptor.Level.NONE
        }
    }

    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .connectTimeout(60, TimeUnit.SECONDS)  // Увеличено до 60 секунд
        .readTimeout(60, TimeUnit.SECONDS)     // Увеличено до 60 секунд
        .writeTimeout(60, TimeUnit.SECONDS)    // Увеличено до 60 секунд
        .addInterceptor { chain ->
            val originalRequest = chain.request()

            // Добавляем токен в заголовок, если он есть
            val token = authManager?.getToken()
            val requestBuilder = originalRequest.newBuilder()
                .addHeader("Content-Type", "application/json")
                .addHeader("Accept", "application/json")
            
            // Добавляем Authorization заголовок с токеном
            if (token != null) {
                requestBuilder.addHeader("Authorization", "Bearer $token")
            }

            val request = requestBuilder.build()
            chain.proceed(request)
        }
        .build()

    private val retrofit: Retrofit by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    val apiService: ApiService by lazy {
        retrofit.create(ApiService::class.java)
    }
}