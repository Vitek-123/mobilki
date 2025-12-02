package com.example.test

import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.widget.SwitchCompat
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat

class Settings : BaseActivity() {
    
    private lateinit var authManager: AuthManager
    
    // Views для настроек
    private lateinit var switchNotifications: SwitchCompat
    private lateinit var switchPriceAlerts: SwitchCompat
    private lateinit var switchNewProducts: SwitchCompat
    private lateinit var switchAutoUpdate: SwitchCompat
    private lateinit var layoutTheme: LinearLayout
    private lateinit var textViewThemeValue: TextView
    private lateinit var layoutLanguage: LinearLayout
    private lateinit var textViewLanguageValue: TextView
    private lateinit var layoutCurrency: LinearLayout
    private lateinit var textViewCurrencyValue: TextView
    private lateinit var layoutClearCache: LinearLayout
    private lateinit var layoutExportData: LinearLayout
    private lateinit var layoutPrivacy: LinearLayout
    private lateinit var layoutHelp: LinearLayout
    private lateinit var textViewVersion: TextView
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_settings)
        
        // Инициализация
        authManager = AuthManager.getInstance(this)
        RetrofitClient.initialize(this)
        
        // Обработка system bars
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, 0)
            insets
        }
        
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.content_container)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, v.paddingBottom + systemBars.bottom)
            insets
        }

        setupBottomNavigation(R.id.navigation_settings)
        initViews()
        setupSettings()
    }
    
    private fun initViews() {
        // Настройки
        switchNotifications = findViewById(R.id.Settings_switch_notifications)
        switchPriceAlerts = findViewById(R.id.Settings_switch_priceAlerts)
        switchNewProducts = findViewById(R.id.Settings_switch_newProducts)
        switchAutoUpdate = findViewById(R.id.Settings_switch_autoUpdate)
        layoutTheme = findViewById(R.id.Settings_layout_theme)
        textViewThemeValue = findViewById(R.id.Settings_textView_themeValue)
        layoutLanguage = findViewById(R.id.Settings_layout_language)
        textViewLanguageValue = findViewById(R.id.Settings_textView_languageValue)
        layoutCurrency = findViewById(R.id.Settings_layout_currency)
        textViewCurrencyValue = findViewById(R.id.Settings_textView_currencyValue)
        layoutClearCache = findViewById(R.id.Settings_layout_clearCache)
        layoutExportData = findViewById(R.id.Settings_layout_exportData)
        layoutPrivacy = findViewById(R.id.Settings_layout_privacy)
        layoutHelp = findViewById(R.id.Settings_layout_help)
        textViewVersion = findViewById(R.id.Settings_textView_version)
    }
    
    private fun setupSettings() {
        // Проверяем авторизацию для настроек, требующих входа
        val isLoggedIn = authManager.isLoggedIn()
        switchPriceAlerts.isEnabled = isLoggedIn
        // Загружаем сохраненные настройки
        val prefs = getSharedPreferences("app_settings", MODE_PRIVATE)
        
        // Уведомления
        switchNotifications.isChecked = prefs.getBoolean("notifications_enabled", true)
        switchNotifications.setOnCheckedChangeListener { _, isChecked ->
            prefs.edit().putBoolean("notifications_enabled", isChecked).apply()
            Toast.makeText(this, if (isChecked) "Уведомления включены" else "Уведомления выключены", Toast.LENGTH_SHORT).show()
        }
        
        // Уведомления о ценах (только для авторизованных)
        switchPriceAlerts.isChecked = prefs.getBoolean("price_alerts_enabled", false)
        switchPriceAlerts.setOnCheckedChangeListener { _, isChecked ->
            if (!authManager.isLoggedIn()) {
                switchPriceAlerts.isChecked = false
                Toast.makeText(this, "Войдите в аккаунт для использования этой функции", Toast.LENGTH_SHORT).show()
                return@setOnCheckedChangeListener
            }
            prefs.edit().putBoolean("price_alerts_enabled", isChecked).apply()
            Toast.makeText(this, if (isChecked) "Уведомления о ценах включены" else "Уведомления о ценах выключены", Toast.LENGTH_SHORT).show()
        }
        
        // Новые товары
        switchNewProducts.isChecked = prefs.getBoolean("new_products_enabled", true)
        switchNewProducts.setOnCheckedChangeListener { _, isChecked ->
            prefs.edit().putBoolean("new_products_enabled", isChecked).apply()
            Toast.makeText(this, if (isChecked) "Уведомления о новых товарах включены" else "Уведомления о новых товарах выключены", Toast.LENGTH_SHORT).show()
        }
        
        // Автообновление цен
        switchAutoUpdate.isChecked = prefs.getBoolean("auto_update_enabled", true)
        switchAutoUpdate.setOnCheckedChangeListener { _, isChecked ->
            prefs.edit().putBoolean("auto_update_enabled", isChecked).apply()
            Toast.makeText(this, if (isChecked) "Автообновление цен включено" else "Автообновление цен выключено", Toast.LENGTH_SHORT).show()
        }
        
        // Тема
        val currentTheme = ThemeUtils.getSavedTheme(this)
        updateThemeDisplay(currentTheme)
        layoutTheme.setOnClickListener {
            showThemeDialog(currentTheme)
        }
        
        // Язык
        val currentLanguage = prefs.getString("language", "ru") ?: "ru"
        updateLanguageDisplay(currentLanguage)
        layoutLanguage.setOnClickListener {
            showLanguageDialog(currentLanguage)
        }
        
        // Валюта
        val currentCurrency = prefs.getString("currency", "rub") ?: "rub"
        updateCurrencyDisplay(currentCurrency)
        layoutCurrency.setOnClickListener {
            showCurrencyDialog(currentCurrency)
        }
        
        // Очистить кэш
        layoutClearCache.setOnClickListener {
            showClearCacheDialog()
        }
        
        // Экспорт данных
        layoutExportData.setOnClickListener {
            showExportDataDialog()
        }
        
        // Конфиденциальность
        layoutPrivacy.setOnClickListener {
            showPrivacyDialog()
        }
        
        // Помощь и поддержка
        layoutHelp.setOnClickListener {
            showHelpDialog()
        }
        
        // Версия приложения
        try {
            val packageInfo = packageManager.getPackageInfo(packageName, 0)
            val versionName = packageInfo.versionName ?: "1.0"
            textViewVersion.text = getString(R.string.settings_version, versionName)
        } catch (e: PackageManager.NameNotFoundException) {
            textViewVersion.text = getString(R.string.settings_version, "1.0")
        }
    }
    
    private fun updateThemeDisplay(theme: String) {
        val themeText = when (theme) {
            "light" -> getString(R.string.settings_theme_light)
            "dark" -> getString(R.string.settings_theme_dark)
            "system" -> getString(R.string.settings_theme_system)
            else -> getString(R.string.settings_theme_light)
        }
        textViewThemeValue.text = themeText
    }
    
    private fun showThemeDialog(currentTheme: String) {
        val themes = arrayOf(
            getString(R.string.settings_theme_light),
            getString(R.string.settings_theme_dark),
            getString(R.string.settings_theme_system)
        )
        
        val themeValues = arrayOf("light", "dark", "system")
        val currentIndex = themeValues.indexOf(currentTheme).takeIf { it >= 0 } ?: 0
        
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.settings_theme))
            .setSingleChoiceItems(themes, currentIndex) { dialog, which ->
                val selectedTheme = themeValues[which]
                // Сохраняем и применяем тему сразу
                ThemeUtils.saveTheme(this, selectedTheme)
                updateThemeDisplay(selectedTheme)
                // Перезагружаем активность для применения темы
                recreate()
                dialog.dismiss()
            }
            .setNegativeButton("Отмена", null)
            .show()
    }
    
    private fun showClearCacheDialog() {
        AlertDialog.Builder(this)
            .setTitle("Очистить кэш")
            .setMessage("Это действие удалит сохраненные данные приложения. Продолжить?")
            .setPositiveButton("Очистить") { _, _ ->
                clearCache()
            }
            .setNegativeButton("Отмена", null)
            .show()
    }
    
    private fun clearCache() {
        // Очищаем кэш приложения
        try {
            val cacheDir = cacheDir
            if (cacheDir.exists() && cacheDir.isDirectory) {
                cacheDir.deleteRecursively()
            }
            Toast.makeText(this, "Кэш очищен", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            Toast.makeText(this, "Ошибка при очистке кэша", Toast.LENGTH_SHORT).show()
        }
    }
    
    private fun updateLanguageDisplay(language: String) {
        val languageText = when (language) {
            "ru" -> getString(R.string.settings_language_russian)
            "en" -> getString(R.string.settings_language_english)
            else -> getString(R.string.settings_language_russian)
        }
        textViewLanguageValue.text = languageText
    }
    
    private fun showLanguageDialog(currentLanguage: String) {
        val languages = arrayOf(
            getString(R.string.settings_language_russian),
            getString(R.string.settings_language_english)
        )
        
        val languageValues = arrayOf("ru", "en")
        val currentIndex = languageValues.indexOf(currentLanguage).takeIf { it >= 0 } ?: 0
        
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.settings_language))
            .setSingleChoiceItems(languages, currentIndex) { dialog, which ->
                val selectedLanguage = languageValues[which]
                val prefs = getSharedPreferences("app_settings", MODE_PRIVATE)
                prefs.edit().putString("language", selectedLanguage).apply()
                updateLanguageDisplay(selectedLanguage)
                Toast.makeText(this, "Язык изменен. Перезапустите приложение для применения изменений.", Toast.LENGTH_LONG).show()
                dialog.dismiss()
            }
            .setNegativeButton("Отмена", null)
            .show()
    }
    
    private fun updateCurrencyDisplay(currency: String) {
        val currencyText = when (currency) {
            "rub" -> getString(R.string.settings_currency_rub)
            "usd" -> getString(R.string.settings_currency_usd)
            "eur" -> getString(R.string.settings_currency_eur)
            else -> getString(R.string.settings_currency_rub)
        }
        textViewCurrencyValue.text = currencyText
    }
    
    private fun showCurrencyDialog(currentCurrency: String) {
        val currencies = arrayOf(
            getString(R.string.settings_currency_rub),
            getString(R.string.settings_currency_usd),
            getString(R.string.settings_currency_eur)
        )
        
        val currencyValues = arrayOf("rub", "usd", "eur")
        val currentIndex = currencyValues.indexOf(currentCurrency).takeIf { it >= 0 } ?: 0
        
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.settings_currency))
            .setSingleChoiceItems(currencies, currentIndex) { dialog, which ->
                val selectedCurrency = currencyValues[which]
                val prefs = getSharedPreferences("app_settings", MODE_PRIVATE)
                prefs.edit().putString("currency", selectedCurrency).apply()
                updateCurrencyDisplay(selectedCurrency)
                Toast.makeText(this, "Валюта изменена на ${currencies[which]}", Toast.LENGTH_SHORT).show()
                dialog.dismiss()
            }
            .setNegativeButton("Отмена", null)
            .show()
    }
    
    private fun showExportDataDialog() {
        AlertDialog.Builder(this)
            .setTitle("Экспорт данных")
            .setMessage("Экспортировать избранное и историю просмотров?")
            .setPositiveButton("Экспортировать") { _, _ ->
                // TODO: Реализовать экспорт данных
                Toast.makeText(this, "Функция экспорта данных будет реализована в будущем", Toast.LENGTH_SHORT).show()
            }
            .setNegativeButton("Отмена", null)
            .show()
    }
    
    private fun showPrivacyDialog() {
        AlertDialog.Builder(this)
            .setTitle("Конфиденциальность")
            .setMessage("Политика конфиденциальности\n\n" +
                    "Мы собираем только необходимые данные для работы приложения:\n" +
                    "- Логин и email для авторизации\n" +
                    "- Данные о просмотренных товарах\n" +
                    "- Настройки приложения\n\n" +
                    "Все данные хранятся локально на вашем устройстве и на защищенном сервере.\n\n" +
                    "Мы не передаем ваши данные третьим лицам.")
            .setPositiveButton("Понятно", null)
            .show()
    }
    
    private fun showHelpDialog() {
        AlertDialog.Builder(this)
            .setTitle("Помощь и поддержка")
            .setMessage("Часто задаваемые вопросы:\n\n" +
                    "1. Как добавить товар в избранное?\n" +
                    "Нажмите на иконку ❤️ на карточке товара.\n\n" +
                    "2. Как настроить уведомления о ценах?\n" +
                    "Перейдите в Настройки → Уведомления о ценах.\n\n" +
                    "3. Как изменить тему приложения?\n" +
                    "Настройки → Тема приложения.\n\n" +
                    "4. Как связаться с поддержкой?\n" +
                    "Email: support@scanprice.app\n\n" +
                    "Если у вас есть вопросы, напишите нам!")
            .setPositiveButton("Понятно", null)
            .show()
    }
    
    override fun onResume() {
        super.onResume()
        // Обновляем настройки при возврате на экран
        setupSettings()
    }
}
