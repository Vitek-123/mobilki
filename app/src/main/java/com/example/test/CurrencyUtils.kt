package com.example.test

import android.content.Context
import android.content.SharedPreferences
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import java.text.NumberFormat
import java.util.Locale
import java.util.concurrent.ConcurrentHashMap

object CurrencyUtils {
    private const val TAG = "CurrencyUtils"
    private const val PREFS_NAME = "app_settings"
    private const val KEY_CURRENCY = "currency"
    private const val DEFAULT_CURRENCY = "rub"
    
    // Кэш курсов валют (обновляется динамически)
    private val exchangeRatesCache = ConcurrentHashMap<String, Double>()
    private var ratesInitialized = false
    
    // Scope для асинхронных операций
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    
    /**
     * Инициализирует курсы валют (загружает с API в фоне)
     */
    fun initializeRates(context: Context) {
        if (ratesInitialized) return
        
        scope.launch {
            try {
                val rates = ExchangeRateService.getExchangeRates()
                exchangeRatesCache.clear()
                exchangeRatesCache.putAll(rates)
                ratesInitialized = true
                Log.d(TAG, "Курсы валют инициализированы")
            } catch (e: Exception) {
                Log.e(TAG, "Ошибка инициализации курсов валют", e)
                // Используем дефолтные значения
                loadDefaultRates()
            }
        }
    }
    
    /**
     * Загружает дефолтные курсы валют
     */
    private fun loadDefaultRates() {
        exchangeRatesCache["RUB"] = 1.0
        exchangeRatesCache["USD"] = 0.011
        exchangeRatesCache["EUR"] = 0.010
        ratesInitialized = true
    }
    
    /**
     * Получает курс валюты (синхронно, использует кэш)
     */
    private fun getRateSync(currency: String): Double {
        // Если курсы еще не загружены, используем дефолтные
        if (!ratesInitialized) {
            loadDefaultRates()
            // Запускаем загрузку актуальных курсов в фоне
            scope.launch {
                try {
                    val rates = ExchangeRateService.getExchangeRates()
                    exchangeRatesCache.clear()
                    exchangeRatesCache.putAll(rates)
                    Log.d(TAG, "Курсы валют обновлены в фоне")
                } catch (e: Exception) {
                    Log.e(TAG, "Ошибка обновления курсов валют", e)
                }
            }
        }
        
        val currencyUpper = currency.uppercase()
        return when (currencyUpper) {
            "RUB" -> exchangeRatesCache["RUB"] ?: 1.0
            "USD" -> exchangeRatesCache["USD"] ?: 0.011
            "EUR" -> exchangeRatesCache["EUR"] ?: 0.010
            else -> exchangeRatesCache[currencyUpper] ?: 1.0
        }
    }
    
    /**
     * Обновляет курсы валют (асинхронно)
     */
    fun refreshRates() {
        scope.launch {
            try {
                val rates = ExchangeRateService.getExchangeRates(forceRefresh = true)
                exchangeRatesCache.clear()
                exchangeRatesCache.putAll(rates)
                Log.d(TAG, "Курсы валют обновлены")
            } catch (e: Exception) {
                Log.e(TAG, "Ошибка обновления курсов валют", e)
            }
        }
    }
    
    /**
     * Получает выбранную валюту из настроек
     */
    fun getSelectedCurrency(context: Context): String {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getString(KEY_CURRENCY, DEFAULT_CURRENCY) ?: DEFAULT_CURRENCY
    }
    
    /**
     * Сохраняет выбранную валюту
     */
    fun saveCurrency(context: Context, currency: String) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString(KEY_CURRENCY, currency).apply()
    }
    
    /**
     * Конвертирует цену из рублей в выбранную валюту
     */
    fun convertPrice(context: Context, priceInRubles: Double?): Double? {
        if (priceInRubles == null || priceInRubles <= 0) return null
        
        val currency = getSelectedCurrency(context)
        val rate = getRateSync(currency)
        return priceInRubles * rate
    }
    
    /**
     * Конвертирует цену из рублей в выбранную валюту (Float версия)
     */
    fun convertPrice(context: Context, priceInRubles: Float?): Float? {
        if (priceInRubles == null || priceInRubles <= 0) return null
        
        val currency = getSelectedCurrency(context)
        val rate = getRateSync(currency)
        return (priceInRubles * rate).toFloat()
    }
    
    /**
     * Получает символ валюты
     */
    fun getCurrencySymbol(currency: String): String {
        return when (currency) {
            "rub" -> "₽"
            "usd" -> "$"
            "eur" -> "€"
            else -> "₽"
        }
    }
    
    /**
     * Получает символ валюты из контекста
     */
    fun getCurrencySymbol(context: Context): String {
        return getCurrencySymbol(getSelectedCurrency(context))
    }
    
    /**
     * Форматирует цену с учетом выбранной валюты
     */
    fun formatPrice(context: Context, priceInRubles: Double?): String {
        if (priceInRubles == null || priceInRubles <= 0) {
            return "Цена не указана"
        }
        
        val currency = getSelectedCurrency(context)
        val convertedPrice = convertPrice(context, priceInRubles) ?: return "Цена не указана"
        val symbol = getCurrencySymbol(currency)
        
        return when (currency) {
            "rub" -> String.format("%,.0f %s", convertedPrice, symbol)
            "usd" -> String.format(Locale.US, "%,.2f %s", convertedPrice, symbol)
            "eur" -> String.format(Locale.US, "%,.2f %s", convertedPrice, symbol)
            else -> String.format("%,.0f %s", convertedPrice, symbol)
        }
    }
    
    /**
     * Форматирует цену с учетом выбранной валюты (Float версия)
     */
    fun formatPrice(context: Context, priceInRubles: Float?): String {
        if (priceInRubles == null || priceInRubles <= 0) {
            return "Цена не указана"
        }
        
        return formatPrice(context, priceInRubles.toDouble())
    }
    
    /**
     * Форматирует цену без символа валюты (только число)
     */
    fun formatPriceNumber(context: Context, priceInRubles: Double?): String {
        if (priceInRubles == null || priceInRubles <= 0) {
            return "0"
        }
        
        val currency = getSelectedCurrency(context)
        val convertedPrice = convertPrice(context, priceInRubles) ?: return "0"
        
        return when (currency) {
            "rub" -> String.format("%,.0f", convertedPrice)
            "usd" -> String.format(Locale.US, "%,.2f", convertedPrice)
            "eur" -> String.format(Locale.US, "%,.2f", convertedPrice)
            else -> String.format("%,.0f", convertedPrice)
        }
    }
    
    /**
     * Форматирует цену без символа валюты (Float версия)
     */
    fun formatPriceNumber(context: Context, priceInRubles: Float?): String {
        if (priceInRubles == null || priceInRubles <= 0) {
            return "0"
        }
        
        return formatPriceNumber(context, priceInRubles.toDouble())
    }
}

