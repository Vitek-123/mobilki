package com.example.test

import android.app.Application

/**
 * Application класс для инициализации темы при запуске приложения
 */
class MobilkiApplication : Application() {
    
    override fun onCreate() {
        super.onCreate()
        // Применяем сохраненную тему при запуске приложения
        ThemeUtils.applyTheme(this)
    }
}

