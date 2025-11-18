package com.example.test

data class CreateUserRequest(
    val login: String,
    val email: String,
    val password: String
)

data class UserResponse(
    val id_user: Int,
    val login: String,
    val email: String
)

data class LoginRequest(
    val login: String,
    val password: String
)

data class LoginResponse(
    val access_token: String,
    val token_type: String,
    val user: UserResponse
)
