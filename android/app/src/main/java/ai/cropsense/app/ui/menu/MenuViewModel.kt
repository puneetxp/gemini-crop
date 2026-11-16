package ai.cropsense.app.ui.menu

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import ai.cropsense.app.data.SessionManager
import ai.cropsense.app.model.AgriService

class MenuViewModel(private val sessionManager: SessionManager) : ViewModel() {

    private val _userName = MutableLiveData<String>()
    val userName: LiveData<String> = _userName

    private val _userEmail = MutableLiveData<String>()
    val userEmail: LiveData<String> = _userEmail

    private val _services = MutableLiveData<List<AgriService>>()
    val services: LiveData<List<AgriService>> = _services

    init {
        loadUserProfile()
        loadCatalog()
    }

    private fun loadUserProfile() {
        _userName.value = sessionManager.getUserName()
        _userEmail.value = sessionManager.getUserEmail()
    }

    private fun loadCatalog() {
        _services.value = listOf(
            AgriService(
                id = "srv_1",
                icon = "psychiatry",
                title = "AI Crop Diagnosis",
                description = "Instant foliar disease scanning with Vision AI, lesion segmentation, and ICAR treatment plans.",
                actionText = "Launch Scanner",
                badge = "Multimodal AI",
                isPrimary = true
            ),
            AgriService(
                id = "srv_2",
                icon = "satellite_alt",
                title = "Satellite NDVI Health",
                description = "Sentinel-2 multispectral NDVI/NDMI vegetation indices, moisture gradients, and drone imagery sync.",
                actionText = "View Satellite",
                badge = "10m Spatial"
            ),
            AgriService(
                id = "srv_3",
                icon = "crop_landscape",
                title = "Field & Crop Management",
                description = "Cadastral plot boundaries, sowing timeline tracker, and acreage analytics.",
                actionText = "Open Plots",
                badge = "Geo-Tagged"
            ),
            AgriService(
                id = "srv_4",
                icon = "pets",
                title = "Pashu & Livestock",
                description = "Dairy cattle management, vaccination schedule, and automated breeding lifecycle tracking.",
                actionText = "View Pashu Hub"
            )
        )
    }

    fun logout() {
        sessionManager.logout()
    }
}
