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
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class Registration : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.registration)
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom)
            insets
        }

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
                        "Регистрация успешна! ID: ${user?.id_user}",
                        Toast.LENGTH_LONG
                    ).show()


                    val intent = android.content.Intent(this@Registration, Auth::class.java)
                    startActivity(intent)
                    finish()
                } else {
                    val errorMessage = when (response.code()) {
                        400 -> "Пользователь с таким логином или почтой уже существует"
                        500 -> "Ошибка сервера"
                        else -> "Ошибка регистрации: ${response.message()}"
                    }
                    Toast.makeText(this@Registration, errorMessage, Toast.LENGTH_SHORT).show()
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
}