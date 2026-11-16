package ai.cropsense.app.ui.menu

import android.content.Intent
import android.graphics.Color
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import ai.cropsense.app.R
import ai.cropsense.app.model.AgriService
import ai.cropsense.app.ui.auth.LoginActivity

class MenuFragment : Fragment() {

    private val viewModel: MenuViewModel by viewModels { MenuViewModelFactory(requireContext()) }

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_menu, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        setupObservers(view)
        
        view.findViewById<Button>(R.id.btnLogout).setOnClickListener {
            showLogoutDialog()
        }
    }

    private fun setupObservers(view: View) {
        val tvName = view.findViewById<TextView>(R.id.tvProfileName)
        val tvEmail = view.findViewById<TextView>(R.id.tvProfileEmail)
        val tvInitials = view.findViewById<TextView>(R.id.tvAvatarInitials)

        viewModel.userName.observe(viewLifecycleOwner) { name ->
            tvName.text = name
            val initials = name.split(" ").mapNotNull { it.firstOrNull()?.toString() }.take(2).joinToString("").uppercase()
            tvInitials.text = if (initials.isNotEmpty()) initials else "U"
        }

        viewModel.userEmail.observe(viewLifecycleOwner) { email ->
            tvEmail.text = email
        }

        viewModel.services.observe(viewLifecycleOwner) { services ->
            renderCatalog(view, services)
        }
    }

    private fun renderCatalog(view: View, services: List<AgriService>) {
        val container = view.findViewById<LinearLayout>(R.id.containerServices)
        container.removeAllViews()
        val inflater = LayoutInflater.from(requireContext())

        for (service in services) {
            val itemView = inflater.inflate(R.layout.item_service_card, container, false)
            val tvIcon = itemView.findViewById<TextView>(R.id.tvIcon)
            val tvTitle = itemView.findViewById<TextView>(R.id.tvTitle)
            val tvDesc = itemView.findViewById<TextView>(R.id.tvDescription)
            val tvBadge = itemView.findViewById<TextView>(R.id.tvBadge)
            val btnAction = itemView.findViewById<Button>(R.id.btnAction)
            val containerIcon = itemView.findViewById<LinearLayout>(R.id.containerIcon)

            tvTitle.text = service.title
            tvDesc.text = service.description
            btnAction.text = service.actionText

            // Map some placeholder text to emojis for quick 1:1 visual parity without needing custom SVG drawables for every icon
            tvIcon.text = when (service.icon) {
                "psychiatry" -> "🧠"
                "satellite_alt" -> "🛰️"
                "crop_landscape" -> "🌱"
                "pets" -> "🐄"
                else -> "✨"
            }

            if (service.isPrimary) {
                btnAction.setBackgroundColor(Color.parseColor("#065f46")) // primary dark
                containerIcon.setBackgroundColor(Color.parseColor("#d1fae5")) // emerald light
            } else {
                btnAction.setBackgroundColor(Color.parseColor("#16a34a")) // primary
            }

            if (service.badge != null) {
                tvBadge.visibility = View.VISIBLE
                tvBadge.text = service.badge
            } else {
                tvBadge.visibility = View.GONE
            }

            container.addView(itemView)
        }
    }

    private fun showLogoutDialog() {
        AlertDialog.Builder(requireContext())
            .setTitle("Sign Out")
            .setMessage("Are you sure you want to sign out of CropSense AI?")
            .setPositiveButton("Sign Out") { _, _ ->
                viewModel.logout()
                val intent = Intent(requireContext(), LoginActivity::class.java)
                intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                startActivity(intent)
            }
            .setNegativeButton("Cancel", null)
            .show()
    }
}
