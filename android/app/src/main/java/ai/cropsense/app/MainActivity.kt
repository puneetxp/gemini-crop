package ai.cropsense.app

import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import ai.cropsense.app.data.SessionManager
import ai.cropsense.app.ui.MainShellActivity
import ai.cropsense.app.ui.auth.LoginActivity

class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()
        super.onCreate(savedInstanceState)

        val sessionManager = SessionManager(this)
        
        if (!sessionManager.isLoggedIn()) {
            val intent = Intent(this, LoginActivity::class.java)
            startActivity(intent)
            finish()
            return
        }

        // If logged in, navigate directly to Native Shell
        val intent = Intent(this, MainShellActivity::class.java)
        startActivity(intent)
        finish()
    }
}
