package ai.cropsense.app.viewmodel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import ai.cropsense.app.model.ActionType
import ai.cropsense.app.model.CropOverview
import ai.cropsense.app.model.DiseaseAlert
import ai.cropsense.app.model.QuickAction
import ai.cropsense.app.model.WeatherInfo

class DashboardViewModel : ViewModel() {

    private val _weather = MutableLiveData<WeatherInfo>()
    val weather: LiveData<WeatherInfo> = _weather

    private val _crops = MutableLiveData<List<CropOverview>>()
    val crops: LiveData<List<CropOverview>> = _crops

    private val _quickActions = MutableLiveData<List<QuickAction>>()
    val quickActions: LiveData<List<QuickAction>> = _quickActions

    private val _alerts = MutableLiveData<List<DiseaseAlert>>()
    val alerts: LiveData<List<DiseaseAlert>> = _alerts

    init {
        loadDashboardData()
    }

    fun loadDashboardData() {
        _weather.value = WeatherInfo(
            location = "Pune, Maharashtra",
            temperatureC = 29,
            condition = "Partly Cloudy • High Humidity",
            humidityPercent = 74,
            windKmH = 14,
            rainfallMm = 12.5,
            isAlert = true,
            alertText = "Heavy Rain Advisory in next 48 hrs"
        )

        _crops.value = listOf(
            CropOverview(
                farmName = "Shivaji Farm Plot #1",
                cropName = "Soybean (JS 335)",
                fieldAreaAcres = 3.5,
                healthStatus = "EXCELLENT",
                ndviScore = 0.82,
                daysToHarvest = 35
            ),
            CropOverview(
                farmName = "Riverbed Plot #2",
                cropName = "Sugarcane (Co 86032)",
                fieldAreaAcres = 5.0,
                healthStatus = "MODERATE",
                ndviScore = 0.68,
                daysToHarvest = 110
            )
        )

        _quickActions.value = listOf(
            QuickAction(
                id = "qa_1",
                title = "AI Pathology Doctor",
                subtitle = "Instant crop disease scan",
                iconName = "psychology",
                badge = "NEW AI",
                actionType = ActionType.DIAGNOSE_PATHOLOGY
            ),
            QuickAction(
                id = "qa_2",
                title = "Pashu Assistant",
                subtitle = "Cattle & breed management",
                iconName = "pets",
                badge = "VOICE",
                actionType = ActionType.PASHU_ASSISTANT
            ),
            QuickAction(
                id = "qa_3",
                title = "Soil & Satellite",
                subtitle = "NDVI & soil health card",
                iconName = "satellite_alt",
                actionType = ActionType.SOIL_HEALTH
            ),
            QuickAction(
                id = "qa_4",
                title = "Advance Booking",
                subtitle = "Tractors, drones & labor",
                iconName = "calendar_month",
                actionType = ActionType.BOOKING_SERVICES
            ),
            QuickAction(
                id = "qa_5",
                title = "Krishi Marketplace",
                subtitle = "Buy & sell crop yields",
                iconName = "storefront",
                actionType = ActionType.MARKETPLACE
            )
        )

        _alerts.value = listOf(
            DiseaseAlert(
                id = "alt_101",
                cropName = "Soybean",
                diseaseName = "Yellow Mosaic Virus",
                severity = "HIGH",
                affectedDistrict = "Pune & Satara",
                advisoryText = "Spray Imidacloprid 17.8 SL @ 0.5ml/L to control whitefly vector.",
                timestampText = "2 hrs ago"
            ),
            DiseaseAlert(
                id = "alt_102",
                cropName = "Cotton",
                diseaseName = "Pink Bollworm Alert",
                severity = "MEDIUM",
                affectedDistrict = "Solapur",
                advisoryText = "Install Phero-Sens pheromone traps (5 traps/acre).",
                timestampText = "Yesterday"
            )
        )
    }
}
