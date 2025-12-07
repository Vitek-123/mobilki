package com.example.test

import android.content.Context
import android.content.SharedPreferences
import android.content.res.Configuration
import android.content.res.Resources
import android.os.Build
import java.util.Locale

/**
 * Утилита для управления языком приложения
 */
object LocaleHelper {
    
    private const val PREFS_NAME = "app_settings"
    private const val KEY_LANGUAGE = "language"
    
    /**
     * Применяет сохраненный язык к контексту
     */
    fun setLocale(context: Context): Context {
        val language = getSavedLanguage(context)
        return updateLocale(context, language)
    }
    
    /**
     * Обновляет локаль для контекста
     */
    fun updateLocale(context: Context, language: String): Context {
        val locale = Locale(language)
        Locale.setDefault(locale)
        
        val resources: Resources = context.resources
        val configuration: Configuration = resources.configuration
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            configuration.setLocale(locale)
            return context.createConfigurationContext(configuration)
        } else {
            @Suppress("DEPRECATION")
            configuration.locale = locale
            @Suppress("DEPRECATION")
            resources.updateConfiguration(configuration, resources.displayMetrics)
            return context
        }
    }
    
    /**
     * Сохраняет выбранный язык
     */
    fun saveLanguage(context: Context, language: String) {
        val prefs: SharedPreferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString(KEY_LANGUAGE, language).apply()
    }
    
    /**
     * Получает сохраненный язык
     */
    fun getSavedLanguage(context: Context): String {
        val prefs: SharedPreferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getString(KEY_LANGUAGE, "ru") ?: "ru"
    }
    
    /**
     * Применяет язык к контексту и возвращает новый контекст
     */
    fun attachBaseContext(context: Context): Context {
        return setLocale(context)
    }
}

