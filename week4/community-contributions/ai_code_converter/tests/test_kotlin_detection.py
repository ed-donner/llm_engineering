"""Test module for Kotlin language detection."""

import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ai_code_converter.core.language_detection import LanguageDetector


def test_kotlin_detection():
    """Test the Kotlin language detection functionality."""
    detector = LanguageDetector()
    
    # Sample Kotlin code
    kotlin_code = """
package com.example.myapp

import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import java.util.*

/**
 * Main Activity for the application
 */
class MainActivity : AppCompatActivity() {
    
    // Properties
    private lateinit var textView: TextView
    private lateinit var button: Button
    private val viewModel: MainViewModel by viewModels()
    private val job = Job()
    private val coroutineScope = CoroutineScope(Dispatchers.Main + job)
    
    // Immutable property
    val API_KEY: String = "abc123"
    
    // Computed property
    val isActive: Boolean
        get() = viewModel.isActive && !isFinishing
    
    // Data class
    data class User(
        val id: Int,
        val name: String,
        val email: String,
        var isActive: Boolean = true
    )
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        // View binding
        textView = findViewById(R.id.textView)
        button = findViewById(R.id.button)
        
        // Click listener
        button.setOnClickListener {
            fetchData()
        }
        
        // Observe live data
        viewModel.userData.observe(this) { user ->
            updateUI(user)
        }
        
        // Extension function call
        "Hello, Kotlin!".printDebug()
        
        // Using when expression
        val result = when(viewModel.status) {
            Status.LOADING -> "Loading..."
            Status.SUCCESS -> "Success!"
            Status.ERROR -> "Error!"
            else -> "Unknown"
        }
        
        textView.text = result
    }
    
    // Suspend function
    private suspend fun fetchUserData(): User {
        return withContext(Dispatchers.IO) {
            // Simulate network delay
            delay(1000)
            User(1, "John Doe", "john@example.com")
        }
    }
    
    // Coroutine usage
    private fun fetchData() {
        coroutineScope.launch {
            try {
                textView.text = "Loading..."
                val user = fetchUserData()
                updateUI(user)
            } catch (e: Exception) {
                textView.text = "Error: ${e.message}"
            }
        }
    }
    
    // Normal function
    private fun updateUI(user: User) {
        textView.text = "Welcome, ${user.name}!"
        
        // Smart cast
        val info: Any = user.email
        if (info is String) {
            // No need to cast, Kotlin knows it's a String
            textView.text = info.toUpperCase()
        }
        
        // Collection operations
        val numbers = listOf(1, 2, 3, 4, 5)
        val sum = numbers.filter { it % 2 == 0 }.sum()
        
        // String template
        val message = "Sum of even numbers: $sum"
        println(message)
    }
    
    // Higher-order function
    private inline fun performOperation(
        value: Int,
        operation: (Int) -> Int
    ): Int {
        return operation(value)
    }
    
    // Companion object
    companion object {
        const val TAG = "MainActivity"
        
        fun newInstance(): MainActivity {
            return MainActivity()
        }
    }
    
    // Enum class
    enum class Status {
        LOADING,
        SUCCESS,
        ERROR
    }
    
    // Interface definition
    interface OnDataLoadListener {
        fun onDataLoaded(data: Any)
        fun onError(message: String)
    }
    
    // Object declaration (singleton)
    object Logger {
        fun log(message: String) {
            println("[$TAG] $message")
        }
    }
    
    // Extension function
    fun String.printDebug() {
        println("Debug: $this")
    }
    
    override fun onDestroy() {
        super.onDestroy()
        job.cancel() // Cancel coroutines when activity is destroyed
    }
}
"""
    
    # Test the detection
    assert detector.detect_kotlin(kotlin_code) == True
    assert detector.detect_language(kotlin_code) == "Kotlin"
    
    # Check validation
    valid, _ = detector.validate_language(kotlin_code, "Kotlin")
    assert valid == True


if __name__ == "__main__":
    test_kotlin_detection()
    print("All Kotlin detection tests passed!")
