package com.example.test

import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.GET
import java.util.concurrent.TimeUnit

/**
 * Модели данных для API курсов валют ЦБ РФ
 */
data class ExchangeRatesResponse(
    val Date: String,
    val PreviousDate: String,
    val PreviousURL: String,
    val Timestamp: String,
    val Valute: Map<String, CurrencyRate>
)

data class CurrencyRate(
    val ID: String,
    val NumCode: String,
    val CharCode: String,
    val Nominal: Int,
    val Name: String,
    val Value: Double,
    val Previous: Double
)

/**
 * Интерфейс для API курсов валют
 */
interface ExchangeRateApi {
    @GET("daily_json.js")
    suspend fun getExchangeRates(): ExchangeRatesResponse
}

/**
 * Сервис для получения курсов валют
 */
object ExchangeRateService {
    private const val TAG = "ExchangeRateService"
    private const val BASE_URL = "https://www.cbr-xml-daily.ru/"
    
    // TTL для кэша курсов валют (1 час)
    private const val CACHE_TTL_MS = 60 * 60 * 1000L
    
    private var cachedRates: Map<String, Double>? = null
    private var cacheTimestamp: Long = 0
    
    private val api: ExchangeRateApi by lazy {
        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }
        
        val okHttpClient = OkHttpClient.Builder()
            .addInterceptor(loggingInterceptor)
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(10, TimeUnit.SECONDS)
            .writeTimeout(10, TimeUnit.SECONDS)
            .build()
        
        val retrofit = Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
        
        retrofit.create(ExchangeRateApi::class.java)
    }
    
    /**
     * Получает актуальные курсы валют
     * @param forceRefresh Принудительное обновление (игнорирует кэш)
     * @return Map с курсами валют (ключ - код валюты, значение - курс относительно рубля)
     */
    suspend fun getExchangeRates(forceRefresh: Boolean = false): Map<String, Double> = withContext(Dispatchers.IO) {
        try {
            // Проверяем кэш
            if (!forceRefresh && cachedRates != null) {
                val cacheAge = System.currentTimeMillis() - cacheTimestamp
                if (cacheAge < CACHE_TTL_MS) {
                    Log.d(TAG, "Используются кэшированные курсы валют (возраст: ${cacheAge / 1000} сек)")
                    return@withContext cachedRates!!
                }
            }
            
            Log.d(TAG, "Загрузка актуальных курсов валют с API ЦБ РФ...")
            val response = api.getExchangeRates()
            
            // Конвертируем курсы в формат: код валюты -> курс относительно рубля
            val rates = mutableMapOf<String, Double>()
            
            // Рубль всегда 1.0
            rates["RUB"] = 1.0
            
            // Обрабатываем валюты из ответа
            response.Valute.forEach { (code, rate) ->
                // Курс в API указан за Nominal единиц валюты
                // Например, если Nominal = 1, то Value = 90.5 означает 1 USD = 90.5 RUB
                // Нам нужно: 1 RUB = 1 / Value USD
                val ratePerUnit = rate.Value / rate.Nominal
                rates[code] = 1.0 / ratePerUnit // Конвертируем в курс относительно рубля
            }
            
            // Сохраняем в кэш
            cachedRates = rates
            cacheTimestamp = System.currentTimeMillis()
            
            Log.d(TAG, "Курсы валют успешно загружены. USD: ${rates["USD"]}, EUR: ${rates["EUR"]}")
            rates
            
        } catch (e: Exception) {
            Log.e(TAG, "Ошибка загрузки курсов валют", e)
            
            // Если есть кэшированные данные, используем их даже если они устарели
            if (cachedRates != null) {
                Log.w(TAG, "Используются устаревшие курсы валют из кэша")
                return@withContext cachedRates!!
            }
            
            // Если кэша нет, возвращаем дефолтные значения
            Log.w(TAG, "Используются дефолтные курсы валют")
            getDefaultRates()
        }
    }
    
    /**
     * Получает курс конкретной валюты
     */
    suspend fun getRate(currencyCode: String, forceRefresh: Boolean = false): Double {
        val rates = getExchangeRates(forceRefresh)
        return rates[currencyCode] ?: when (currencyCode) {
            "USD" -> 0.011 // Примерно 90 RUB за 1 USD
            "EUR" -> 0.010 // Примерно 100 RUB за 1 EUR
            "RUB" -> 1.0
            else -> 1.0
        }
    }
    
    /**
     * Возвращает дефолтные курсы валют (fallback)
     */
    private fun getDefaultRates(): Map<String, Double> {
        return mapOf(
            "RUB" to 1.0,
            "USD" to 0.011,  // 1 RUB = 0.011 USD (примерно 90 RUB за 1 USD)
            "EUR" to 0.010   // 1 RUB = 0.010 EUR (примерно 100 RUB за 1 EUR)
        )
    }
    
    /**
     * Очищает кэш курсов валют
     */
    fun clearCache() {
        cachedRates = null
        cacheTimestamp = 0
        Log.d(TAG, "Кэш курсов валют очищен")
    }
}

