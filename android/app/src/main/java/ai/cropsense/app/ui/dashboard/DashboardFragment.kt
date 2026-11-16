package ai.cropsense.app.ui.dashboard

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import ai.cropsense.app.R
import ai.cropsense.app.model.ActionType
import ai.cropsense.app.model.CropOverview
import ai.cropsense.app.model.DiseaseAlert
import ai.cropsense.app.model.QuickAction
import ai.cropsense.app.ui.diagnose.DiagnoseFragment
import ai.cropsense.app.viewmodel.DashboardViewModel

class DashboardFragment : Fragment() {

    private val viewModel: DashboardViewModel by viewModels()

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_dashboard, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        setupObservers(view)
    }

    private fun setupObservers(view: View) {
        val tvLocation = view.findViewById<TextView>(R.id.tvWeatherLocation)
        val tvCondition = view.findViewById<TextView>(R.id.tvWeatherCondition)
        val tvTemp = view.findViewById<TextView>(R.id.tvWeatherTemp)
        val tvAlert = view.findViewById<TextView>(R.id.tvWeatherAlert)

        viewModel.weather.observe(viewLifecycleOwner) { weather ->
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

        viewModel.quickActions.observe(viewLifecycleOwner) { actions ->
            renderQuickActions(view, actions)
        }

        viewModel.crops.observe(viewLifecycleOwner) { crops ->
            renderCrops(view, crops)
        }

        viewModel.alerts.observe(viewLifecycleOwner) { alerts ->
            renderAlerts(view, alerts)
        }
    }

    private fun renderQuickActions(view: View, actions: List<QuickAction>) {
        val container = view.findViewById<LinearLayout>(R.id.containerQuickActions)
        container.removeAllViews()
        val inflater = LayoutInflater.from(requireContext())

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
                    parentFragmentManager.beginTransaction()
                        .replace(R.id.nav_host_fragment, DiagnoseFragment())
                        .addToBackStack(null)
                        .commit()

                    // Update bottom navigation selected item if possible (handled in MainActivityShell typically, but ok for now)
                } else {
                    Toast.makeText(requireContext(), "${action.title} coming soon!", Toast.LENGTH_SHORT).show()
                }
            }

            container.addView(itemView)
        }
    }

    private fun renderCrops(view: View, crops: List<CropOverview>) {
        val container = view.findViewById<LinearLayout>(R.id.containerCrops)
        container.removeAllViews()
        val inflater = LayoutInflater.from(requireContext())

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

    private fun renderAlerts(view: View, alerts: List<DiseaseAlert>) {
        val container = view.findViewById<LinearLayout>(R.id.containerAlerts)
        container.removeAllViews()
        val inflater = LayoutInflater.from(requireContext())

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
