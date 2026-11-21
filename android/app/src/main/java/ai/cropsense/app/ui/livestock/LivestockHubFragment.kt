package ai.cropsense.app.ui.livestock

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import ai.cropsense.app.R
import ai.cropsense.app.model.Livestock
import ai.cropsense.app.network.RetrofitClient
import ai.cropsense.app.data.SessionManager

class LivestockHubFragment : Fragment() {

    // Ideally use a ViewModelFactory to pass dependencies, doing simple lazy init here
    private val viewModel: LivestockViewModel by viewModels {
        object : androidx.lifecycle.ViewModelProvider.Factory {
            override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T {
                return LivestockViewModel(RetrofitClient.getAuthApiService(SessionManager(requireContext()))) as T
            }
        }
    }

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_livestock_hub, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val containerLivestock = view.findViewById<LinearLayout>(R.id.containerLivestock)
        val progressLivestock = view.findViewById<ProgressBar>(R.id.progressLivestock)
        val tvError = view.findViewById<TextView>(R.id.tvLivestockError)

        viewModel.isLoading.observe(viewLifecycleOwner) { isLoading ->
            progressLivestock.visibility = if (isLoading) View.VISIBLE else View.GONE
        }

        viewModel.error.observe(viewLifecycleOwner) { errorMsg ->
            if (errorMsg != null) {
                tvError.visibility = View.VISIBLE
                tvError.text = errorMsg
            } else {
                tvError.visibility = View.GONE
            }
        }

        viewModel.livestockList.observe(viewLifecycleOwner) { livestockList ->
            containerLivestock.removeAllViews()
            val inflater = LayoutInflater.from(requireContext())

            for (animal in livestockList) {
                val itemView = inflater.inflate(R.layout.item_livestock_card, containerLivestock, false)

                itemView.findViewById<TextView>(R.id.tvTagId).text = animal.tagId
                itemView.findViewById<TextView>(R.id.tvBreed).text = "${animal.breed} • ${animal.ageText}"

                val tvYield = itemView.findViewById<TextView>(R.id.tvYield)
                if (animal.avgMilkYieldLiters != null) {
                    tvYield.text = "Avg Yield: ${animal.avgMilkYieldLiters} L/day"
                    tvYield.visibility = View.VISIBLE
                } else {
                    tvYield.visibility = View.GONE
                }

                val tvHealth = itemView.findViewById<TextView>(R.id.tvHealthBadge)
                tvHealth.text = animal.healthStatus
                if (animal.healthStatus == "HEALTHY") {
                    tvHealth.setTextColor(android.graphics.Color.parseColor("#16a34a"))
                    tvHealth.setBackgroundColor(android.graphics.Color.parseColor("#dcfce7"))
                } else {
                    tvHealth.setTextColor(android.graphics.Color.parseColor("#dc2626"))
                    tvHealth.setBackgroundColor(android.graphics.Color.parseColor("#fee2e2"))
                }

                containerLivestock.addView(itemView)
            }
        }
    }
}
