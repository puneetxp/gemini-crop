package ai.cropsense.app.model

data class WeatherInfo(
    val location: String,
    val temperatureC: Int,
    val condition: String,
    val humidityPercent: Int,
    val windKmH: Int,
    val rainfallMm: Double,
    val isAlert: Boolean = false,
    val alertText: String = ""
)

data class CropOverview(
    val farmName: String,
    val cropName: String,
    val fieldAreaAcres: Double,
    val healthStatus: String, // "EXCELLENT", "MODERATE", "CRITICAL"
    val ndviScore: Double,
    val daysToHarvest: Int
)

data class QuickAction(
    val id: String,
    val title: String,
    val subtitle: String,
    val iconName: String,
    val badge: String? = null,
    val actionType: ActionType
)

enum class ActionType {
    DIAGNOSE_PATHOLOGY,
    PASHU_ASSISTANT,
    SOIL_HEALTH,
    BOOKING_SERVICES,
    MARKETPLACE,
    WEATHER_ALERTS
}

data class DiseaseAlert(
    val id: String,
    val cropName: String,
    val diseaseName: String,
    val severity: String, // "HIGH", "MEDIUM", "LOW"
    val affectedDistrict: String,
    val advisoryText: String,
    val timestampText: String
)
