package com.example.test

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.bottomnavigation.BottomNavigationView

open class BaseActivity : AppCompatActivity() {

    protected lateinit var bottomNavigationView: BottomNavigationView

    override fun onCreate(savedInstanceState: Bundle?) {
        // Применяем тему перед setContentView
        ThemeUtils.applyTheme(this)
        super.onCreate(savedInstanceState)
        // Базовая инициализация будет в дочерних классах
    }

    protected fun setupBottomNavigation(menuItemId: Int) {
        bottomNavigationView = findViewById(R.id.bottom_navigation)

        // Устанавливаем текущий выбранный пункт
        bottomNavigationView.selectedItemId = menuItemId

        bottomNavigationView.setOnNavigationItemSelectedListener { item ->
            when (item.itemId) {
                R.id.navigation_home -> {
                    if (this !is Main) {
                        startActivity(Intent(this, Main::class.java))
                        finish()
                    }
                    true
                }
                R.id.navigation_settings -> {
                    if (this !is Settings) {
                        startActivity(Intent(this, Settings::class.java))
                    }
                    true
                }
                R.id.navigation_profile -> {
                    if (this !is ProfileActivity) {
                        startActivity(Intent(this, ProfileActivity::class.java))
                    }
                    true
                }
                else -> false
            }
        }
    }
}