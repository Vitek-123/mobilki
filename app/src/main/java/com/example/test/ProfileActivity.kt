package com.example.test

import android.content.Intent
import android.os.Bundle
import android.util.Log
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AlertDialog
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch

class ProfileActivity : BaseActivity() {
    
    private lateinit var authManager: AuthManager
    
    // Views для профиля
    private lateinit var layoutNotLoggedIn: LinearLayout
    private lateinit var layoutLoggedIn: LinearLayout
    private lateinit var buttonLogin: Button
    private lateinit var buttonRegister: Button
    private lateinit var buttonLogout: Button
    private lateinit var textViewUserLogin: TextView
    private lateinit var textViewUserEmail: TextView
    
    // Views для статистики
    private lateinit var textViewStatsViewed: TextView
    private lateinit var textViewStatsFavorites: TextView
    private lateinit var textViewStatsAlerts: TextView
    
    // Views для секций
    private lateinit var layoutFavorites: LinearLayout
    private lateinit var layoutViewHistory: LinearLayout
    private lateinit var layoutPriceAlerts: LinearLayout
    private lateinit var layoutShoppingLists: LinearLayout
    private lateinit var layoutComparisons: LinearLayout
    private lateinit var layoutNotifications: LinearLayout
    private lateinit var layoutPremium: LinearLayout
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_profile)
        
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

        setupBottomNavigation(R.id.navigation_profile)
        initViews()
        setupProfile()
        setupStatistics()
        setupSections()
    }
    
    private fun initViews() {
        // Профиль
        layoutNotLoggedIn = findViewById(R.id.Profile_layout_notLoggedIn)
        layoutLoggedIn = findViewById(R.id.Profile_layout_loggedIn)
        buttonLogin = findViewById(R.id.Profile_button_login)
        buttonRegister = findViewById(R.id.Profile_button_register)
        buttonLogout = findViewById(R.id.Profile_button_logout)
        textViewUserLogin = findViewById(R.id.Profile_textView_userLogin)
        textViewUserEmail = findViewById(R.id.Profile_textView_userEmail)
        
        // Статистика
        textViewStatsViewed = findViewById(R.id.Profile_textView_statsViewed)
        textViewStatsFavorites = findViewById(R.id.Profile_textView_statsFavorites)
        textViewStatsAlerts = findViewById(R.id.Profile_textView_statsAlerts)
        
        // Секции
        layoutFavorites = findViewById(R.id.Profile_layout_favorites)
        layoutViewHistory = findViewById(R.id.Profile_layout_viewHistory)
        layoutPriceAlerts = findViewById(R.id.Profile_layout_priceAlerts)
        layoutShoppingLists = findViewById(R.id.Profile_layout_shoppingLists)
        layoutComparisons = findViewById(R.id.Profile_layout_comparisons)
        layoutNotifications = findViewById(R.id.Profile_layout_notifications)
        layoutPremium = findViewById(R.id.Profile_layout_premium)
        
        // Переход к настройкам
        findViewById<LinearLayout>(R.id.Profile_layout_settings).setOnClickListener {
            val intent = Intent(this, Settings::class.java)
            startActivity(intent)
        }
    }
    
    private fun setupProfile() {
        // Проверяем, авторизован ли пользователь
        if (authManager.isLoggedIn()) {
            showLoggedInState()
        } else {
            showNotLoggedInState()
        }
        
        // Обработчики кнопок
        buttonLogin.setOnClickListener {
            val intent = Intent(this, Auth::class.java)
            startActivity(intent)
        }
        
        buttonRegister.setOnClickListener {
            val intent = Intent(this, Registration::class.java)
            startActivity(intent)
        }
        
        buttonLogout.setOnClickListener {
            showLogoutDialog()
        }
    }
    
    private fun showLoggedInState() {
        layoutNotLoggedIn.visibility = View.GONE
        layoutLoggedIn.visibility = View.VISIBLE
        
        // Показываем секции только для авторизованных пользователей
        layoutFavorites.visibility = View.VISIBLE
        layoutViewHistory.visibility = View.VISIBLE
        layoutPriceAlerts.visibility = View.VISIBLE
        layoutShoppingLists.visibility = View.VISIBLE
        layoutComparisons.visibility = View.VISIBLE
        layoutNotifications.visibility = View.VISIBLE
        layoutPremium.visibility = View.VISIBLE
        
        // Получаем данные пользователя
        val user = authManager.getCurrentUser()
        if (user != null) {
            textViewUserLogin.text = user.login
            textViewUserEmail.text = user.email
        }
    }
    
    private fun showNotLoggedInState() {
        layoutNotLoggedIn.visibility = View.VISIBLE
        layoutLoggedIn.visibility = View.GONE
        
        // Скрываем секции для неавторизованных пользователей
        layoutFavorites.visibility = View.GONE
        layoutViewHistory.visibility = View.GONE
        layoutPriceAlerts.visibility = View.GONE
        layoutShoppingLists.visibility = View.GONE
        layoutComparisons.visibility = View.GONE
        layoutNotifications.visibility = View.GONE
        layoutPremium.visibility = View.GONE
    }
    
    private fun showLogoutDialog() {
        AlertDialog.Builder(this)
            .setTitle("Выход из аккаунта")
            .setMessage("Вы уверены, что хотите выйти из аккаунта?")
            .setPositiveButton("Выйти") { _, _ ->
                logout()
            }
            .setNegativeButton("Отмена", null)
            .show()
    }
    
    private fun logout() {
        authManager.logout()
        Toast.makeText(this, "Вы вышли из аккаунта", Toast.LENGTH_SHORT).show()
        showNotLoggedInState()
        setupStatistics()
    }
    
    private fun setupStatistics() {
        if (!authManager.isLoggedIn()) {
            textViewStatsViewed.text = "0"
            textViewStatsFavorites.text = "0"
            textViewStatsAlerts.text = "0"
            return
        }
        
        // Загружаем статистику с сервера
        lifecycleScope.launch {
            try {
                val response = RetrofitClient.apiService.getUserStats()
                if (response.isSuccessful) {
                    val stats = response.body()
                    if (stats != null) {
                        textViewStatsViewed.text = stats.viewed_count.toString()
                        textViewStatsFavorites.text = stats.favorites_count.toString()
                        textViewStatsAlerts.text = stats.alerts_count.toString()
                    }
                } else {
                    Log.e("Profile", "Error loading stats: ${response.code()}")
                }
            } catch (e: Exception) {
                Log.e("Profile", "Error loading stats", e)
                // В случае ошибки показываем 0
                textViewStatsViewed.text = "0"
                textViewStatsFavorites.text = "0"
                textViewStatsAlerts.text = "0"
            }
        }
    }
    
    private fun setupSections() {
        // Избранное
        layoutFavorites.setOnClickListener {
            if (!authManager.isLoggedIn()) {
                Toast.makeText(this, "Войдите в аккаунт для использования этой функции", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            // TODO: Открыть FavoritesActivity
            Toast.makeText(this, "Избранное - в разработке", Toast.LENGTH_SHORT).show()
        }
        
        // История просмотров
        layoutViewHistory.setOnClickListener {
            if (!authManager.isLoggedIn()) {
                Toast.makeText(this, "Войдите в аккаунт для использования этой функции", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            // TODO: Открыть ViewHistoryActivity
            Toast.makeText(this, "История просмотров - в разработке", Toast.LENGTH_SHORT).show()
        }
        
        // Отслеживание цен
        layoutPriceAlerts.setOnClickListener {
            if (!authManager.isLoggedIn()) {
                Toast.makeText(this, "Войдите в аккаунт для использования этой функции", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            // TODO: Открыть PriceAlertsActivity
            Toast.makeText(this, "Отслеживание цен - в разработке", Toast.LENGTH_SHORT).show()
        }
        
        // Списки покупок
        layoutShoppingLists.setOnClickListener {
            if (!authManager.isLoggedIn()) {
                Toast.makeText(this, "Войдите в аккаунт для использования этой функции", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            // TODO: Открыть ShoppingListsActivity
            Toast.makeText(this, "Списки покупок - в разработке", Toast.LENGTH_SHORT).show()
        }
        
        // Сравнение товаров
        layoutComparisons.setOnClickListener {
            if (!authManager.isLoggedIn()) {
                Toast.makeText(this, "Войдите в аккаунт для использования этой функции", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            // TODO: Открыть ComparisonsActivity
            Toast.makeText(this, "Сравнение товаров - в разработке", Toast.LENGTH_SHORT).show()
        }
        
        // Уведомления
        layoutNotifications.setOnClickListener {
            if (!authManager.isLoggedIn()) {
                Toast.makeText(this, "Войдите в аккаунт для использования этой функции", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            // TODO: Открыть NotificationsActivity
            Toast.makeText(this, "Уведомления - в разработке", Toast.LENGTH_SHORT).show()
        }
        
        // Premium
        layoutPremium.setOnClickListener {
            if (!authManager.isLoggedIn()) {
                Toast.makeText(this, "Войдите в аккаунт для использования этой функции", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            // TODO: Открыть PremiumActivity
            Toast.makeText(this, "Premium подписка - в разработке", Toast.LENGTH_SHORT).show()
        }
    }
    
    override fun onResume() {
        super.onResume()
        // Обновляем состояние профиля при возврате на экран
        setupProfile()
        setupStatistics()
    }
}

