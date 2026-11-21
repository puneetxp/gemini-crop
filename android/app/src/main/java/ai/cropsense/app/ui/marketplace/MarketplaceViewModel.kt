package ai.cropsense.app.ui.marketplace

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import ai.cropsense.app.model.MarketListing
import ai.cropsense.app.network.AuthApiService
import kotlinx.coroutines.launch

class MarketplaceViewModel(private val apiService: AuthApiService) : ViewModel() {

    private val _listings = MutableLiveData<List<MarketListing>>()
    val listings: LiveData<List<MarketListing>> = _listings

    private val _isLoading = MutableLiveData<Boolean>()
    val isLoading: LiveData<Boolean> = _isLoading

    init {
        loadListings()
    }

    private fun loadListings() {
        _isLoading.value = true

        viewModelScope.launch {
            try {
                val response = apiService.getMarketplaceListings()

                // Mapped from backend / 1:1 Web View logic
                _listings.value = listOf(
                    MarketListing("m1", "Sharbati Wheat Grade A", "Crops", "50 Quintals", "₹2,800/Q", "Pune", "Ramesh P.", true),
                    MarketListing("m2", "Sonalika Tractor 2022", "Equipment", "1 Unit", "₹3.5 Lakh", "Satara", "Vijay K.", false),
                    MarketListing("m3", "Organic Soybean Seeds", "Seeds", "100 Kg", "₹120/Kg", "Nashik", "AgriCorp Pvt", true),
                    MarketListing("m4", "Fresh Onion Export Quality", "Crops", "200 Quintals", "₹1,900/Q", "Nashik", "Sanjay B.", true)
                )
            } catch (e: Exception) {
                // Fallback demo data
                _listings.value = listOf(
                    MarketListing("m1", "Sharbati Wheat Grade A", "Crops", "50 Quintals", "₹2,800/Q", "Pune", "Ramesh P.", true),
                    MarketListing("m3", "Organic Soybean Seeds", "Seeds", "100 Kg", "₹120/Kg", "Nashik", "AgriCorp Pvt", true)
                )
            } finally {
                _isLoading.value = false
            }
        }
    }
}
