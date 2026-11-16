package ai.cropsense.app.ui.auth

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.ProgressBar
import android.widget.Toast
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.WindowCompat
import ai.cropsense.app.MainActivity
import ai.cropsense.app.R
import ai.cropsense.app.data.SessionManager

class LoginActivity : AppCompatActivity() {

    private lateinit var sessionManager: SessionManager
    private val viewModel: LoginViewModel by viewModels { LoginViewModelFactory(sessionManager) }

    private lateinit var btnLogin: Button
    private lateinit var progressLogin: ProgressBar
    private lateinit var btnDemo: Button
    private lateinit var progressDemo: ProgressBar

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        sessionManager = SessionManager(this)

        // If already logged in, skip to MainActivity (Router)
        if (sessionManager.isLoggedIn()) {
            navigateToMain()
            return
        }

        WindowCompat.setDecorFitsSystemWindows(window, false)
        setContentView(R.layout.activity_login)

        val etEmail = findViewById<EditText>(R.id.etEmail)
        val etPassword = findViewById<EditText>(R.id.etPassword)
        btnLogin = findViewById(R.id.btnLogin)
        progressLogin = findViewById(R.id.progressLogin)
        btnDemo = findViewById(R.id.btnDemo)
        progressDemo = findViewById(R.id.progressDemo)

        btnLogin.setOnClickListener {
            val email = etEmail.text.toString().trim()
            val password = etPassword.text.toString().trim()
            if (email.isNotEmpty() && password.isNotEmpty()) {
                viewModel.signIn(email, password)
            } else {
                Toast.makeText(this, "Enter email and password", Toast.LENGTH_SHORT).show()
            }
        }

        btnDemo.setOnClickListener {
            viewModel.demoSignIn()
        }

        viewModel.authState.observe(this) { state ->
            when (state) {
                is AuthState.Idle -> resetUi()
                is AuthState.Loading -> {
                    btnLogin.text = ""
                    progressLogin.visibility = View.VISIBLE
                    btnDemo.isEnabled = false
                }
                is AuthState.DemoLoading -> {
                    btnDemo.text = ""
                    progressDemo.visibility = View.VISIBLE
                    btnLogin.isEnabled = false
                }
                is AuthState.Success -> {
                    Toast.makeText(this, "Welcome, ${state.email}!", Toast.LENGTH_SHORT).show()
                    navigateToMain()
                }
                is AuthState.Error -> {
                    resetUi()
                    Toast.makeText(this, state.message, Toast.LENGTH_LONG).show()
                }
            }
        }
    }

    private fun resetUi() {
        btnLogin.text = "Sign In"
        btnLogin.isEnabled = true
        progressLogin.visibility = View.GONE

        btnDemo.text = "Continue as Demo Farmer"
        btnDemo.isEnabled = true
        progressDemo.visibility = View.GONE
    }

    private fun navigateToMain() {
        val intent = Intent(this, ai.cropsense.app.ui.MainShellActivity::class.java)
        intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        startActivity(intent)
        finish()
    }
}
