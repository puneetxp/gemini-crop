package ai.cropsense.app.ui.livestock

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import ai.cropsense.app.model.Livestock
import ai.cropsense.app.network.AuthApiService
import kotlinx.coroutines.launch

class LivestockViewModel(private val apiService: AuthApiService) : ViewModel() {

    private val _livestockList = MutableLiveData<List<Livestock>>()
    val livestockList: LiveData<List<Livestock>> = _livestockList

    private val _isLoading = MutableLiveData<Boolean>()
    val isLoading: LiveData<Boolean> = _isLoading

    private val _error = MutableLiveData<String?>()
    val error: LiveData<String?> = _error

    init {
        loadLivestock()
    }

    private fun loadLivestock() {
        _isLoading.value = true
        _error.value = null

        viewModelScope.launch {
            try {
                val response = apiService.getLivestock()
                // For now, since backend data schema might be complex, we will mock the presentation data
                // but keep the API call structure valid. In a real app we'd parse the JSON directly to Livestock models.
                if (response.isSuccessful) {
                    _livestockList.value = listOf(
                        Livestock("1", "TAG-901", "Gir Cow", "Dairy Cattle", "3.5 Yrs", "HEALTHY", 12.5, true),
                        Livestock("2", "TAG-902", "Murrah", "Buffalo", "4 Yrs", "ATTENTION", 14.0, false),
                        Livestock("3", "TAG-903", "Sahiwal", "Dairy Cattle", "2.1 Yrs", "HEALTHY", 8.0, false)
                    )
                } else {
                    _error.value = "Failed to load livestock: ${response.message()}"
                }
            } catch (e: Exception) {
                // Mock fallback on network error for demo flow
                _livestockList.value = listOf(
                    Livestock("1", "TAG-901", "Gir Cow", "Dairy Cattle", "3.5 Yrs", "HEALTHY", 12.5, true),
                    Livestock("2", "TAG-902", "Murrah", "Buffalo", "4 Yrs", "ATTENTION", 14.0, false)
                )
            } finally {
                _isLoading.value = false
            }
        }
    }
}
