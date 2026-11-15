package ai.cropsense.app.ui.dashboard

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.widget.LinearLayout
import android.widget.TextView
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.WindowCompat
import ai.cropsense.app.R
import ai.cropsense.app.model.ActionType
import ai.cropsense.app.model.CropOverview
import ai.cropsense.app.model.DiseaseAlert
import ai.cropsense.app.model.QuickAction
import ai.cropsense.app.viewmodel.DashboardViewModel

class DashboardActivity : AppCompatActivity() {

    private val viewModel: DashboardViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        WindowCompat.setDecorFitsSystemWindows(window, false)
        setContentView(R.layout.activity_dashboard)

        setupObservers()
    }

    private fun setupObservers() {
        val tvLocation = findViewById<TextView>(R.id.tvWeatherLocation)
        val tvCondition = findViewById<TextView>(R.id.tvWeatherCondition)
        val tvTemp = findViewById<TextView>(R.id.tvWeatherTemp)
        val tvAlert = findViewById<TextView>(R.id.tvWeatherAlert)

        viewModel.weather.observe(this) { weather ->
            tvLocation.text = weather.location
            tvCondition.text = weather.condition
            tvTemp.text = "${weather.temperatureC}°C"
            if (weather.isAlert) {
                tvAlert.visibility = View.VISIBLE
                tvAlert.text = "⚠ ${weather.alertText}"
            } else {
                tvAlert.visibility = View.GONE
            }
        }

        viewModel.quickActions.observe(this) { actions ->
            renderQuickActions(actions)
        }

        viewModel.crops.observe(this) { crops ->
            renderCrops(crops)
        }

        viewModel.alerts.observe(this) { alerts ->
            renderAlerts(alerts)
        }
    }

    private fun renderQuickActions(actions: List<QuickAction>) {
        val container = findViewById<LinearLayout>(R.id.containerQuickActions)
        container.removeAllViews()
        val inflater = LayoutInflater.from(this)

        for (action in actions) {
            val itemView = inflater.inflate(R.layout.item_quick_action, container, false)
            val tvIcon = itemView.findViewById<TextView>(R.id.tvActionIcon)
            val tvTitle = itemView.findViewById<TextView>(R.id.tvActionTitle)
            val tvSubtitle = itemView.findViewById<TextView>(R.id.tvActionSubtitle)
            val tvBadge = itemView.findViewById<TextView>(R.id.tvActionBadge)

            tvTitle.text = action.title
            tvSubtitle.text = action.subtitle
            tvIcon.text = when (action.actionType) {
                ActionType.DIAGNOSE_PATHOLOGY -> "🔍"
                ActionType.PASHU_ASSISTANT -> "🐄"
                ActionType.SOIL_HEALTH -> "🛰️"
                ActionType.BOOKING_SERVICES -> "🚜"
                ActionType.MARKETPLACE -> "🛒"
                ActionType.WEATHER_ALERTS -> "⛈️"
            }

            if (action.badge != null) {
                tvBadge.visibility = View.VISIBLE
                tvBadge.text = action.badge
            } else {
                tvBadge.visibility = View.GONE
            }

            itemView.setOnClickListener {
                if (action.actionType == ActionType.DIAGNOSE_PATHOLOGY) {
                    val intent = android.content.Intent(this, ai.cropsense.app.ui.diagnose.DiagnoseActivity::class.java)
                    startActivity(intent)
                } else {
                    android.widget.Toast.makeText(this, "${action.title} coming soon!", android.widget.Toast.LENGTH_SHORT).show()
                }
            }

            container.addView(itemView)
        }
    }

    private fun renderCrops(crops: List<CropOverview>) {
        val container = findViewById<LinearLayout>(R.id.containerCrops)
        container.removeAllViews()
        val inflater = LayoutInflater.from(this)

        for (crop in crops) {
            val itemView = inflater.inflate(R.layout.item_crop_card, container, false)
            val tvFarm = itemView.findViewById<TextView>(R.id.tvFarmName)
            val tvCrop = itemView.findViewById<TextView>(R.id.tvCropName)
            val tvHealth = itemView.findViewById<TextView>(R.id.tvHealthBadge)
            val tvNdvi = itemView.findViewById<TextView>(R.id.tvNdviScore)
            val tvHarvest = itemView.findViewById<TextView>(R.id.tvHarvestDays)

            tvFarm.text = crop.farmName
            tvCrop.text = "${crop.cropName} (${crop.fieldAreaAcres} Acres)"
            tvHealth.text = crop.healthStatus
            tvNdvi.text = "NDVI Score: ${crop.ndviScore}"
            tvHarvest.text = "${crop.daysToHarvest} Days to Harvest"

            container.addView(itemView)
        }
    }

    private fun renderAlerts(alerts: List<DiseaseAlert>) {
        val container = findViewById<LinearLayout>(R.id.containerAlerts)
        container.removeAllViews()
        val inflater = LayoutInflater.from(this)

        for (alert in alerts) {
            val itemView = inflater.inflate(R.layout.item_disease_alert, container, false)
            val tvSeverity = itemView.findViewById<TextView>(R.id.tvAlertSeverity)
            val tvDistrict = itemView.findViewById<TextView>(R.id.tvAlertDistrict)
            val tvTime = itemView.findViewById<TextView>(R.id.tvAlertTime)
            val tvTitle = itemView.findViewById<TextView>(R.id.tvAlertTitle)
            val tvAdvisory = itemView.findViewById<TextView>(R.id.tvAlertAdvisory)

            tvSeverity.text = "${alert.severity} SEVERITY"
            tvDistrict.text = alert.affectedDistrict
            tvTime.text = alert.timestampText
            tvTitle.text = "${alert.cropName}: ${alert.diseaseName}"
            tvAdvisory.text = "Advisory: ${alert.advisoryText}"

            container.addView(itemView)
        }
    }
}
