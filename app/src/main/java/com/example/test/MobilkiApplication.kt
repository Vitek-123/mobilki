package com.example.test

import android.app.Application
import android.content.Context

/**
 * Application класс для инициализации темы и языка при запуске приложения
 */
class MobilkiApplication : Application() {
    
    override fun onCreate() {
        super.onCreate()
        // Применяем сохраненную тему при запуске приложения
        ThemeUtils.applyTheme(this)
    }
    
    override fun attachBaseContext(base: Context) {
        // Применяем сохраненный язык при запуске приложения
        super.attachBaseContext(LocaleHelper.attachBaseContext(base))
    }
}

