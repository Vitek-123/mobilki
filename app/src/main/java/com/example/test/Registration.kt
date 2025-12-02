package com.example.test

import android.os.Bundle
import android.util.Log
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import com.google.gson.Gson
import com.google.gson.JsonObject
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class Registration : AppCompatActivity() {

    private lateinit var authManager: AuthManager

    override fun onCreate(savedInstanceState: Bundle?) {
        // Применяем тему перед setContentView
        ThemeUtils.applyTheme(this)
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.registration)
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom)
            insets
        }

        // Инициализация RetrofitClient и AuthManager
        RetrofitClient.initialize(this)
        authManager = AuthManager.getInstance(this)

        val loginData: EditText = findViewById(R.id.Reg_editText_login)
        val emailData: EditText = findViewById(R.id.Reg_editText_email)
        val passwordData: EditText = findViewById(R.id.Reg_editText_password)
        val passwordCheckData: EditText = findViewById(R.id.Reg_editText_password_check)
        val registerData: Button = findViewById(R.id.Reg_button_registr)
        val autoData: TextView = findViewById(R.id.Reg_TextView_Auto)

        autoData.setOnClickListener {
            val intent = android.content.Intent(this, Auth::class.java)
            startActivity(intent)
            finish()
        }



        registerData.setOnClickListener {
            val login = loginData.text.toString().trim()
            val email = emailData.text.toString().trim()
            val password = passwordData.text.toString().trim()
            val passwordCheck = passwordCheckData.text.toString().trim()

            if (login.isEmpty() || email.isEmpty() || password.isEmpty()) {
                Toast.makeText(this, "Заполните все поля", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            if (login.length < 3) {
                Toast.makeText(this, "Логин должен содержать минимум 3 символа", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            if (!android.util.Patterns.EMAIL_ADDRESS.matcher(email).matches()) {
                Toast.makeText(this, "Введите корректный email адрес", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            if (password.length < 4) {
                Toast.makeText(this, "Пароль должен содержать минимум 4 символа", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            
            // Bcrypt имеет ограничение в 72 байта для пароля
            // Проверяем только если пароль явно очень длинный (больше 100 символов)
            // Для обычных паролей проверка будет на сервере
            if (password.length > 100) {
                Toast.makeText(this, "Пароль слишком длинный (максимум 100 символов)", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            if (password != passwordCheck) {
                Toast.makeText(this, "Пароли не совпадают", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }


            registerUser(login, email, password)
        }
    }

    private fun registerUser(login: String, email: String, password: String) {
        val userRequest = CreateUserRequest(login, email, password)

        RetrofitClient.apiService.registerUser(userRequest).enqueue(object : Callback<UserResponse> {
            override fun onResponse(call: Call<UserResponse>, response: Response<UserResponse>) {
                if (response.isSuccessful) {
                    val user = response.body()
                    Toast.makeText(
                        this@Registration,
                        "Регистрация успешна! Выполняется вход...",
                        Toast.LENGTH_SHORT
                    ).show()

                    // После успешной регистрации автоматически логиним пользователя
                    autoLoginAfterRegistration(login, password)
                } else {
                    // Пытаемся получить детальное сообщение об ошибке от сервера
                    val errorMessage = try {
                        val errorBody = response.errorBody()?.string()
                        Log.e("Registration", "Registration failed: ${response.code()}, body: $errorBody")
                        
                        if (errorBody != null) {
                            try {
                                // Пытаемся распарсить JSON с деталями ошибки
                                val gson = Gson()
                                val jsonObject = gson.fromJson(errorBody, JsonObject::class.java)
                                val detail = jsonObject.get("detail")?.asString
                                
                                if (detail != null) {
                                    detail
                                } else {
                                    getDefaultErrorMessage(response.code())
                                }
                            } catch (e: Exception) {
                                // Если не удалось распарсить JSON, ищем "detail" в тексте
                                if (errorBody.contains("\"detail\"")) {
                                    val detailStart = errorBody.indexOf("\"detail\":\"") + 10
                                    val detailEnd = errorBody.indexOf("\"", detailStart)
                                    if (detailStart > 9 && detailEnd > detailStart) {
                                        errorBody.substring(detailStart, detailEnd)
                                    } else {
                                        getDefaultErrorMessage(response.code())
                                    }
                                } else {
                                    getDefaultErrorMessage(response.code())
                                }
                            }
                        } else {
                            getDefaultErrorMessage(response.code())
                        }
                    } catch (e: Exception) {
                        Log.e("Registration", "Error parsing error body: ${e.message}", e)
                        getDefaultErrorMessage(response.code())
                    }
                    Toast.makeText(this@Registration, errorMessage, Toast.LENGTH_LONG).show()
                }
            }

            override fun onFailure(call: Call<UserResponse>, t: Throwable) {
                Toast.makeText(
                    this@Registration,
                    "Ошибка сети: ${t.message}",
                    Toast.LENGTH_LONG
                ).show()
                Log.e("Registration", "Network error: ${t.message}", t)
                Log.d("Registration", "Detailed error: ${t.stackTraceToString()}")
            }
        })
    }
    
    private fun getDefaultErrorMessage(code: Int): String {
        return when (code) {
            400 -> "Пользователь с таким логином или почтой уже существует"
            500 -> "Ошибка сервера. Проверьте подключение к БД и логи сервера"
            404 -> "Сервер не найден. Проверьте BASE_URL"
            else -> "Ошибка регистрации (код: $code)"
        }
    }
    
    /**
     * Автоматический вход после успешной регистрации
     */
    private fun autoLoginAfterRegistration(login: String, password: String) {
        val loginRequest = LoginRequest(login, password)
        
        RetrofitClient.apiService.loginUser(loginRequest).enqueue(object : Callback<LoginResponse> {
            override fun onResponse(call: Call<LoginResponse>, response: Response<LoginResponse>) {
                if (response.isSuccessful) {
                    val loginResponse = response.body()
                    if (loginResponse != null) {
                        // Сохраняем токен и данные пользователя
                        authManager.saveAuthData(
                            loginResponse.access_token,
                            loginResponse.user
                        )
                        
                        Toast.makeText(
                            this@Registration,
                            "Добро пожаловать, ${loginResponse.user.login}!",
                            Toast.LENGTH_LONG
                        ).show()

                        // Переходим на главный экран
                        val intent = android.content.Intent(this@Registration, Main::class.java)
                        startActivity(intent)
                        finish()
                    } else {
                        // Если логин не удался, все равно переходим на главный экран
                        // (пользователь зарегистрирован, но не авторизован)
                        Toast.makeText(
                            this@Registration,
                            "Регистрация успешна, но не удалось выполнить автоматический вход. Войдите вручную.",
                            Toast.LENGTH_LONG
                        ).show()
                        val intent = android.content.Intent(this@Registration, Main::class.java)
                        startActivity(intent)
                        finish()
                    }
                } else {
                    // Если логин не удался, все равно переходим на главный экран
                    // (пользователь зарегистрирован, но не авторизован)
                    Log.w("Registration", "Auto-login failed after registration: ${response.code()}")
                    Toast.makeText(
                        this@Registration,
                        "Регистрация успешна, но не удалось выполнить автоматический вход. Войдите вручную.",
                        Toast.LENGTH_LONG
                    ).show()
                    val intent = android.content.Intent(this@Registration, Main::class.java)
                    startActivity(intent)
                    finish()
                }
            }

            override fun onFailure(call: Call<LoginResponse>, t: Throwable) {
                // Если логин не удался из-за сети, все равно переходим на главный экран
                Log.e("Registration", "Auto-login network error: ${t.message}", t)
                Toast.makeText(
                    this@Registration,
                    "Регистрация успешна, но не удалось выполнить автоматический вход. Войдите вручную.",
                    Toast.LENGTH_LONG
                ).show()
                val intent = android.content.Intent(this@Registration, Main::class.java)
                startActivity(intent)
                finish()
            }
        })
    }
}