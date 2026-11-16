package ai.cropsense.app.model

data class AgriService(
    val id: String,
    val icon: String,
    val title: String,
    val description: String,
    val actionText: String,
    val badge: String? = null,
    val isPrimary: Boolean = false
)
