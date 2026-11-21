package ai.cropsense.app.model

data class MarketListing(
    val id: String,
    val title: String,
    val category: String,
    val quantityText: String,
    val priceText: String,
    val location: String,
    val sellerName: String,
    val isVerified: Boolean = false
)
