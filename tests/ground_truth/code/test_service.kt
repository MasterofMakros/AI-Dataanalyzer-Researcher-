// Kotlin Test File
package com.example.test

data class User(val name: String, val email: String, val age: Int)

class UserService {
    private val users = mutableListOf<User>()
    
    fun addUser(user: User) = users.add(user)
    
    fun findByName(name: String): User? = users.find { it.name == name }
}

fun main() {
    val service = UserService()
    service.addUser(User("Max", "max@example.com", 30))
    println("User Service gestartet")
}
