package ai.cropsense.app.ui.menu

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import ai.cropsense.app.data.SessionManager

class MenuViewModelFactory(private val context: Context) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(MenuViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return MenuViewModel(SessionManager(context)) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
