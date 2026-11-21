package ai.cropsense.app.model

data class Livestock(
    val id: String,
    val tagId: String,
    val breed: String,
    val category: String, // "Dairy Cattle", "Buffalo"
    val ageText: String,
    val healthStatus: String, // "HEALTHY", "ATTENTION", "SICK"
    val avgMilkYieldLiters: Double? = null,
    val isPregnant: Boolean = false
)
