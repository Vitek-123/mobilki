package com.example.test

import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.util.Log
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import android.os.Handler
import android.os.Looper
import android.widget.Toast
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.widget.SwitchCompat
import androidx.core.content.FileProvider
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch
import java.io.File

class Settings : BaseActivity() {
    
    /**
     * Показывает Toast с кастомным временем показа
     * @param message Текст сообщения
     * @param duration Длительность в миллисекундах (по умолчанию 1500 мс = 1.5 секунды)
     */
    private fun showShortToast(message: String, duration: Int = 1500) {
        val toast = Toast.makeText(this, message, Toast.LENGTH_LONG)
        toast.show()
        Handler(Looper.getMainLooper()).postDelayed({
            toast.cancel()
        }, duration.toLong())
    }
    
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
        }
        
        // Уведомления о ценах (только для авторизованных)
        switchPriceAlerts.isChecked = prefs.getBoolean("price_alerts_enabled", false)
        switchPriceAlerts.setOnCheckedChangeListener { _, isChecked ->
            if (!authManager.isLoggedIn()) {
                switchPriceAlerts.isChecked = false
                showShortToast(getString(R.string.toast_login_required))
                return@setOnCheckedChangeListener
            }
            prefs.edit().putBoolean("price_alerts_enabled", isChecked).apply()
        }
        
        // Новые товары
        switchNewProducts.isChecked = prefs.getBoolean("new_products_enabled", true)
        switchNewProducts.setOnCheckedChangeListener { _, isChecked ->
            prefs.edit().putBoolean("new_products_enabled", isChecked).apply()
        }
        
        // Автообновление цен
        switchAutoUpdate.isChecked = prefs.getBoolean("auto_update_enabled", true)
        switchAutoUpdate.setOnCheckedChangeListener { _, isChecked ->
            prefs.edit().putBoolean("auto_update_enabled", isChecked).apply()
        }
        
        // Тема
        val currentTheme = ThemeUtils.getSavedTheme(this)
        updateThemeDisplay(currentTheme)
        layoutTheme.setOnClickListener {
            showThemeDialog(currentTheme)
        }
        
        // Язык
        val currentLanguage = LocaleHelper.getSavedLanguage(this)
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
            .setNegativeButton(getString(R.string.dialog_button_cancel), null)
            .show()
    }
    
    private fun showClearCacheDialog() {
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.dialog_clear_cache_title))
            .setMessage(getString(R.string.dialog_clear_cache_message))
            .setPositiveButton(getString(R.string.dialog_button_clear)) { _, _ ->
                clearCache()
            }
            .setNegativeButton(getString(R.string.dialog_button_cancel), null)
            .show()
    }
    
    private fun clearCache() {
        // Очищаем кэш приложения
        try {
            val cacheDir = cacheDir
            if (cacheDir.exists() && cacheDir.isDirectory) {
                cacheDir.deleteRecursively()
            }
            showShortToast(getString(R.string.toast_cache_cleared))
        } catch (e: Exception) {
            showShortToast(getString(R.string.toast_cache_clear_error))
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
                
                // Сохраняем выбранный язык
                LocaleHelper.saveLanguage(this, selectedLanguage)
                
                // Применяем язык немедленно
                val context = LocaleHelper.updateLocale(this, selectedLanguage)
                val resources = context.resources
                
                // Обновляем отображение
                updateLanguageDisplay(selectedLanguage)
                
                dialog.dismiss()
                
                // Перезапускаем активность для применения языка
                recreate()
            }
            .setNegativeButton(getString(R.string.dialog_button_cancel), null)
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
                dialog.dismiss()
            }
            .setNegativeButton(getString(R.string.dialog_button_cancel), null)
            .show()
    }
    
    private fun showExportDataDialog() {
        // Проверяем, авторизован ли пользователь
        if (!authManager.isLoggedIn()) {
            showShortToast(getString(R.string.export_error_not_logged_in))
            return
        }
        
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.dialog_export_data_title))
            .setMessage(getString(R.string.dialog_export_data_message))
            .setPositiveButton(getString(R.string.dialog_button_export)) { _, _ ->
                exportData()
            }
            .setNegativeButton(getString(R.string.dialog_button_cancel), null)
            .show()
    }
    
    private fun exportData() {
        val user = authManager.getCurrentUser()
        if (user == null) {
            showShortToast(getString(R.string.export_error_not_logged_in))
            return
        }
        
        // Показываем прогресс
        val progressDialog = AlertDialog.Builder(this)
            .setTitle(getString(R.string.dialog_export_data_title))
            .setMessage(getString(R.string.export_loading))
            .setCancelable(false)
            .create()
        progressDialog.show()
        
        lifecycleScope.launch {
            try {
                // Загружаем избранное
                var allFavorites = mutableListOf<FavoriteResponse>()
                var skip = 0
                val limit = 50
                
                while (true) {
                    val response = RetrofitClient.apiService.getFavorites(skip = skip, limit = limit)
                    if (response.isSuccessful) {
                        val favoritesList = response.body()
                        if (favoritesList != null) {
                            if (favoritesList.favorites.isNotEmpty()) {
                                allFavorites.addAll(favoritesList.favorites)
                                if (favoritesList.favorites.size < limit) {
                                    break
                                }
                                skip += limit
                            } else {
                                // Нет больше товаров
                                break
                            }
                        } else {
                            Log.e("Settings", "Error: favoritesList is null")
                            break
                        }
                    } else {
                        val errorBody = try {
                            response.errorBody()?.string()
                        } catch (e: Exception) {
                            null
                        }
                        Log.e("Settings", "Error loading favorites: ${response.code()}, message: ${response.message()}, body: $errorBody")
                        progressDialog.dismiss()
                        val errorMsg = when (response.code()) {
                            401 -> getString(R.string.export_error_not_logged_in)
                            404 -> getString(R.string.export_error_no_data)
                            else -> "${getString(R.string.export_error)}: ${response.code()} - ${response.message()}"
                        }
                        showShortToast(errorMsg)
                        return@launch
                    }
                }
                
                progressDialog.dismiss()
                
                if (allFavorites.isEmpty()) {
                    showShortToast(getString(R.string.export_error_no_data))
                    return@launch
                }
                
                Log.d("Settings", "Loaded ${allFavorites.size} favorites for export")
                
                // Экспортируем в PDF
                val exporter = DataExporter(this@Settings)
                val result = exporter.exportFavoritesToPdf(user, allFavorites)
                
                result.onSuccess { file ->
                    // Открываем Share Intent
                    sharePdfFile(file)
                    showShortToast(getString(R.string.export_success))
                }.onFailure { exception ->
                    Log.e("Settings", "Error exporting data", exception)
                    val errorMessage = exception.message ?: getString(R.string.export_error)
                    showShortToast("${getString(R.string.export_error)}: $errorMessage")
                }
                
            } catch (e: Exception) {
                progressDialog.dismiss()
                Log.e("Settings", "Error exporting data", e)
                val errorMessage = e.message ?: getString(R.string.export_error)
                showShortToast("${getString(R.string.export_error)}: $errorMessage")
            }
        }
    }
    
    private fun sharePdfFile(file: File) {
        try {
            val uri = FileProvider.getUriForFile(
                this,
                "${packageName}.fileprovider",
                file
            )
            
            val shareIntent = Intent(Intent.ACTION_SEND).apply {
                type = "application/pdf"
                putExtra(Intent.EXTRA_STREAM, uri)
                putExtra(Intent.EXTRA_SUBJECT, getString(R.string.dialog_export_data_title))
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            
            startActivity(Intent.createChooser(shareIntent, getString(R.string.dialog_export_data_title)))
        } catch (e: Exception) {
            Log.e("Settings", "Error sharing file", e)
            showShortToast(getString(R.string.export_error))
        }
    }
    
    private fun showPrivacyDialog() {
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.dialog_privacy_title))
            .setMessage(getString(R.string.dialog_privacy_message))
            .setPositiveButton(getString(R.string.dialog_button_ok), null)
            .show()
    }
    
    private fun showHelpDialog() {
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.dialog_help_title))
            .setMessage(getString(R.string.dialog_help_message))
            .setPositiveButton(getString(R.string.dialog_button_ok), null)
            .show()
    }
    
    override fun onResume() {
        super.onResume()
        // Обновляем настройки при возврате на экран
        setupSettings()
    }
}
