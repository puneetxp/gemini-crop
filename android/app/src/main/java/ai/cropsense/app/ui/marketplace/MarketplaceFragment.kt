package ai.cropsense.app.ui.marketplace

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
import ai.cropsense.app.data.SessionManager
import ai.cropsense.app.network.RetrofitClient

class MarketplaceFragment : Fragment() {

    private val viewModel: MarketplaceViewModel by viewModels {
        object : androidx.lifecycle.ViewModelProvider.Factory {
            override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T {
                return MarketplaceViewModel(RetrofitClient.getAuthApiService(SessionManager(requireContext()))) as T
            }
        }
    }

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_marketplace, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val containerMarketplace = view.findViewById<LinearLayout>(R.id.containerMarketplace)
        val progressMarketplace = view.findViewById<ProgressBar>(R.id.progressMarketplace)

        viewModel.isLoading.observe(viewLifecycleOwner) { isLoading ->
            progressMarketplace.visibility = if (isLoading) View.VISIBLE else View.GONE
        }

        viewModel.listings.observe(viewLifecycleOwner) { listings ->
            containerMarketplace.removeAllViews()
            val inflater = LayoutInflater.from(requireContext())

            for (listing in listings) {
                val itemView = inflater.inflate(R.layout.item_market_listing, containerMarketplace, false)

                itemView.findViewById<TextView>(R.id.tvTitle).text = listing.title
                itemView.findViewById<TextView>(R.id.tvPrice).text = listing.priceText
                itemView.findViewById<TextView>(R.id.tvQuantityLocation).text = "${listing.quantityText} • ${listing.location}"

                val tvCategory = itemView.findViewById<TextView>(R.id.tvCategory)
                tvCategory.text = listing.category

                containerMarketplace.addView(itemView)
            }
        }
    }
}
