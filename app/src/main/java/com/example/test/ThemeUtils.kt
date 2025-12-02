package com.example.test

import android.content.Context
import android.content.SharedPreferences
import androidx.appcompat.app.AppCompatDelegate

/**
 * Утилита для управления темой приложения
 */
object ThemeUtils {
    
    private const val PREFS_NAME = "app_settings"
    private const val KEY_THEME = "theme"
    
    /**
     * Применяет сохраненную тему приложения
     */
    fun applyTheme(context: Context) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val theme = prefs.getString(KEY_THEME, "system") ?: "system"
        setTheme(theme)
    }
    
    /**
     * Устанавливает тему приложения
     * @param theme "light", "dark" или "system"
     */
    fun setTheme(theme: String) {
        val mode = when (theme) {
            "light" -> AppCompatDelegate.MODE_NIGHT_NO
            "dark" -> AppCompatDelegate.MODE_NIGHT_YES
            "system" -> AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM
            else -> AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM
        }
        AppCompatDelegate.setDefaultNightMode(mode)
    }
    
    /**
     * Сохраняет выбранную тему
     */
    fun saveTheme(context: Context, theme: String) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString(KEY_THEME, theme).apply()
        setTheme(theme)
    }
    
    /**
     * Получает текущую сохраненную тему
     */
    fun getSavedTheme(context: Context): String {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getString(KEY_THEME, "system") ?: "system"
    }
}

