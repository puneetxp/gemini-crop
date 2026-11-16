package ai.cropsense.app.ui

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.WindowCompat
import androidx.fragment.app.Fragment
import com.google.android.material.bottomnavigation.BottomNavigationView
import ai.cropsense.app.R
import ai.cropsense.app.ui.dashboard.DashboardFragment
import ai.cropsense.app.ui.diagnose.DiagnoseFragment
import ai.cropsense.app.ui.livestock.LivestockHubFragment
import ai.cropsense.app.ui.marketplace.MarketplaceFragment
import ai.cropsense.app.ui.menu.MenuFragment

class MainShellActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        WindowCompat.setDecorFitsSystemWindows(window, false)
        setContentView(R.layout.activity_main_shell)

        val bottomNav = findViewById<BottomNavigationView>(R.id.bottom_navigation)

        bottomNav.setOnItemSelectedListener { item ->
            val fragment: Fragment = when (item.itemId) {
                R.id.nav_home -> DashboardFragment()
                R.id.nav_diagnose -> DiagnoseFragment()
                R.id.nav_pashu -> LivestockHubFragment()
                R.id.nav_mandi -> MarketplaceFragment()
                R.id.nav_menu -> MenuFragment()
                else -> DashboardFragment()
            }
            loadFragment(fragment)
            true
        }

        // Set default selection
        if (savedInstanceState == null) {
            bottomNav.selectedItemId = R.id.nav_home
        }
    }

    private fun loadFragment(fragment: Fragment) {
        supportFragmentManager.beginTransaction()
            .replace(R.id.nav_host_fragment, fragment)
            .commit()
    }
}
