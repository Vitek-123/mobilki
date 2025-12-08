package com.example.test

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.util.Log
import kotlinx.coroutines.delay

object NetworkUtils {
    private const val TAG = "NetworkUtils"
    
    /**
     * Проверка доступности интернета
     */
    fun isNetworkAvailable(context: Context): Boolean {
        val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val network = connectivityManager.activeNetwork ?: return false
        val capabilities = connectivityManager.getNetworkCapabilities(network) ?: return false
        
        return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) &&
               capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
    }
    
    /**
     * Retry логика с экспоненциальной задержкой
     * @param maxRetries максимальное количество попыток
     * @param initialDelay начальная задержка в миллисекундах
     * @param block блок кода для выполнения
     */
    suspend fun <T> retryWithBackoff(
        maxRetries: Int = 3,
        initialDelay: Long = 1000,
        block: suspend () -> T
    ): Result<T> {
        var lastException: Throwable? = null
        
        repeat(maxRetries) { attempt ->
            try {
                val result = block()
                return Result.success(result)
            } catch (e: Exception) {
                lastException = e
                Log.w(TAG, "Попытка ${attempt + 1}/$maxRetries не удалась: ${e.message}")
                
                if (attempt < maxRetries - 1) {
                    val delay = initialDelay * (1L shl attempt) // Экспоненциальная задержка
                    Log.d(TAG, "Повтор через ${delay}ms...")
                    delay(delay)
                }
            }
        }
        
        return Result.failure(lastException ?: Exception("Неизвестная ошибка"))
    }
    
    /**
     * Получить понятное сообщение об ошибке сети
     */
    fun getNetworkErrorMessage(throwable: Throwable?): String {
        return when {
            throwable == null -> "Неизвестная ошибка сети"
            throwable.message?.contains("timeout", ignoreCase = true) == true -> 
                "Превышено время ожидания. Проверьте подключение к интернету"
            throwable.message?.contains("Unable to resolve host", ignoreCase = true) == true -> 
                "Не удалось подключиться к серверу. Проверьте подключение к интернету"
            throwable.message?.contains("Connection refused", ignoreCase = true) == true -> 
                "Сервер недоступен. Попробуйте позже"
            throwable.message?.contains("No address associated with hostname", ignoreCase = true) == true -> 
                "Неверный адрес сервера"
            else -> "Ошибка сети: ${throwable.message ?: "Неизвестная ошибка"}"
        }
    }
}

