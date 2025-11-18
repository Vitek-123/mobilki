package com.example.test

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.Toast
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class Auth : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.auth)
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom)
            insets
        }

        val userLogin: EditText = findViewById(R.id.Auth_editText_login)
        val userPassword: EditText = findViewById(R.id.AuthEditTextPassword)
        val button: Button = findViewById(R.id.Auth_Button_Comein)
        val button_on_guest: Button = findViewById(R.id.Auth_Button_guest)
        val button_on_reg: Button = findViewById(R.id.Auth_Button_registration)

        button_on_reg.setOnClickListener {
            val intent = Intent(this, Registration::class.java)
            startActivity(intent)
        }

        button_on_guest.setOnClickListener {
            val intent = Intent(this, Main::class.java)
            startActivity(intent)
        }

        button.setOnClickListener {
            val login = userLogin.text.toString().trim()
            val password = userPassword.text.toString().trim()

            if (login.isEmpty() || password.isEmpty()) {
                Toast.makeText(this, "Заполните все поля", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            loginUser(login, password)
        }
    }

    private fun loginUser(login: String, password: String) {
        val loginRequest = LoginRequest(login, password)

        RetrofitClient.apiService.loginUser(loginRequest).enqueue(object : Callback<LoginResponse> {
            override fun onResponse(call: Call<LoginResponse>, response: Response<LoginResponse>) {
                if (response.isSuccessful) {
                    val loginResponse = response.body()
                    Toast.makeText(
                        this@Auth,
                        "Вход выполнен! Добро пожаловать, ${loginResponse?.user?.login}",
                        Toast.LENGTH_LONG
                    ).show()

                    // Переход на главный экран
                    val intent = Intent(this@Auth, Main::class.java)
                    startActivity(intent)
                    finish()
                } else {
                    val errorMessage = when (response.code()) {
                        401 -> "Неверный логин или пароль"
                        500 -> "Ошибка сервера"
                        else -> "Ошибка входа: ${response.message()}"
                    }
                    Toast.makeText(this@Auth, errorMessage, Toast.LENGTH_LONG).show()
                }
            }

            override fun onFailure(call: Call<LoginResponse>, t: Throwable) {
                Toast.makeText(
                    this@Auth,
                    "Ошибка сети: ${t.message}",
                    Toast.LENGTH_LONG
                ).show()
            }
        })
    }
}