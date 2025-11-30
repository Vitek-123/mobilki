package com.example.test

import android.content.Context
import android.content.SharedPreferences

/**
 * Менеджер для управления аутентификацией пользователя
 * Сохраняет и управляет JWT токенами через SharedPreferences
 */
class AuthManager private constructor(context: Context) {
    
    companion object {
        private const val PREFS_NAME = "auth_prefs"
        private const val KEY_ACCESS_TOKEN = "access_token"
        private const val KEY_USER_ID = "user_id"
        private const val KEY_USER_LOGIN = "user_login"
        private const val KEY_USER_EMAIL = "user_email"
        
        @Volatile
        private var INSTANCE: AuthManager? = null
        
        fun getInstance(context: Context): AuthManager {
            return INSTANCE ?: synchronized(this) {
                val instance = AuthManager(context.applicationContext)
                INSTANCE = instance
                instance
            }
        }
    }
    
    private val prefs: SharedPreferences = 
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    
    /**
     * Сохраняет токен и данные пользователя после успешного входа
     */
    fun saveAuthData(token: String, user: UserResponse) {
        prefs.edit().apply {
            putString(KEY_ACCESS_TOKEN, token)
            putInt(KEY_USER_ID, user.id_user)
            putString(KEY_USER_LOGIN, user.login)
            putString(KEY_USER_EMAIL, user.email)
            apply()
        }
    }
    
    /**
     * Получает сохраненный токен доступа
     */
    fun getToken(): String? {
        return prefs.getString(KEY_ACCESS_TOKEN, null)
    }
    
    /**
     * Получает ID текущего пользователя
     */
    fun getUserId(): Int? {
        val userId = prefs.getInt(KEY_USER_ID, -1)
        return if (userId != -1) userId else null
    }
    
    /**
     * Получает логин текущего пользователя
     */
    fun getUserLogin(): String? {
        return prefs.getString(KEY_USER_LOGIN, null)
    }
    
    /**
     * Получает email текущего пользователя
     */
    fun getUserEmail(): String? {
        return prefs.getString(KEY_USER_EMAIL, null)
    }
    
    /**
     * Проверяет, авторизован ли пользователь
     */
    fun isLoggedIn(): Boolean {
        return getToken() != null
    }
    
    /**
     * Выход из аккаунта - очищает все сохраненные данные
     */
    fun logout() {
        prefs.edit().clear().apply()
    }
    
    /**
     * Получает полные данные пользователя
     */
    fun getCurrentUser(): UserResponse? {
        val userId = getUserId() ?: return null
        val login = getUserLogin() ?: return null
        val email = getUserEmail() ?: return null
        
        return UserResponse(
            id_user = userId,
            login = login,
            email = email
        )
    }
}

