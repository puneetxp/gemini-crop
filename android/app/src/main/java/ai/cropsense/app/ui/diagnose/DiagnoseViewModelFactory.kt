package ai.cropsense.app.ui.diagnose

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import ai.cropsense.app.data.SessionManager
import ai.cropsense.app.network.RetrofitClient

class DiagnoseViewModelFactory(private val context: Context) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(DiagnoseViewModel::class.java)) {
            val sessionManager = SessionManager(context)
            val apiService = RetrofitClient.getAuthApiService(sessionManager)
            @Suppress("UNCHECKED_CAST")
            return DiagnoseViewModel(apiService) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
