package ai.cropsense.app.ui.diagnose

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.Color
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.FrameLayout
import android.widget.ImageButton
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import ai.cropsense.app.R

class DiagnoseFragment : Fragment() {

    private val viewModel: DiagnoseViewModel by viewModels { DiagnoseViewModelFactory(requireContext()) }

    private lateinit var boxImageUpload: FrameLayout
    private lateinit var containerPlaceholder: LinearLayout
    private lateinit var ivPreview: ImageView
    private lateinit var btnRemoveImage: TextView
    private lateinit var btnDiagnose: Button
    private lateinit var progressDiagnose: ProgressBar
    private lateinit var containerResults: LinearLayout

    private lateinit var tvDiseaseName: TextView
    private lateinit var tvSeverityBadge: TextView
    private lateinit var tvConfidence: TextView
    private lateinit var tvTreatment: TextView

    private val cameraLauncher = registerForActivityResult(
        ActivityResultContracts.TakePicturePreview()
    ) { bitmap: Bitmap? ->
        if (bitmap != null) {
            viewModel.setImage(bitmap)
        }
    }

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_diagnose, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        bindViews(view)
        setupListeners()
        setupObservers()
    }

    private fun bindViews(view: View) {
        boxImageUpload = view.findViewById(R.id.boxImageUpload)
        containerPlaceholder = view.findViewById(R.id.containerPlaceholder)
        ivPreview = view.findViewById(R.id.ivPreview)
        btnRemoveImage = view.findViewById(R.id.btnRemoveImage)
        btnDiagnose = view.findViewById(R.id.btnDiagnose)
        progressDiagnose = view.findViewById(R.id.progressDiagnose)
        containerResults = view.findViewById(R.id.containerResults)

        tvDiseaseName = view.findViewById(R.id.tvDiseaseName)
        tvSeverityBadge = view.findViewById(R.id.tvSeverityBadge)
        tvConfidence = view.findViewById(R.id.tvConfidence)
        tvTreatment = view.findViewById(R.id.tvTreatment)

        view.findViewById<ImageButton>(R.id.btnBack).setOnClickListener {
            parentFragmentManager.popBackStack()
        }
    }

    private fun setupListeners() {
        boxImageUpload.setOnClickListener {
            if (viewModel.state.value is DiagnoseState.Idle) {
                launchCamera()
            }
        }

        btnRemoveImage.setOnClickListener {
            viewModel.removeImage()
        }

        btnDiagnose.setOnClickListener {
            viewModel.analyzeImage()
        }
    }

    private fun launchCamera() {
        if (ContextCompat.checkSelfPermission(requireContext(), Manifest.permission.CAMERA)
            == PackageManager.PERMISSION_GRANTED) {
            cameraLauncher.launch(null)
        } else {
            requestPermissions(arrayOf(Manifest.permission.CAMERA), 101)
        }
    }

    private fun setupObservers() {
        viewModel.state.observe(viewLifecycleOwner) { state ->
            when (state) {
                is DiagnoseState.Idle -> {
                    containerPlaceholder.visibility = View.VISIBLE
                    ivPreview.visibility = View.GONE
                    btnRemoveImage.visibility = View.GONE
                    btnDiagnose.isEnabled = false
                    btnDiagnose.text = "✨ Run Instant AI Pathology Scan"
                    progressDiagnose.visibility = View.GONE
                    containerResults.visibility = View.GONE
                }
                is DiagnoseState.ImageSelected -> {
                    containerPlaceholder.visibility = View.GONE
                    ivPreview.visibility = View.VISIBLE
                    ivPreview.setImageBitmap(state.bitmap)
                    btnRemoveImage.visibility = View.VISIBLE
                    btnDiagnose.isEnabled = true
                    btnDiagnose.text = "✨ Run Instant AI Pathology Scan"
                    progressDiagnose.visibility = View.GONE
                    containerResults.visibility = View.GONE
                }
                is DiagnoseState.Analyzing -> {
                    btnDiagnose.text = ""
                    btnDiagnose.isEnabled = false
                    progressDiagnose.visibility = View.VISIBLE
                    btnRemoveImage.visibility = View.GONE
                    containerResults.visibility = View.GONE
                }
                is DiagnoseState.Success -> {
                    btnDiagnose.text = "✨ Run Instant AI Pathology Scan"
                    btnDiagnose.isEnabled = false
                    progressDiagnose.visibility = View.GONE
                    btnRemoveImage.visibility = View.VISIBLE

                    val result = state.result
                    containerResults.visibility = View.VISIBLE
                    tvDiseaseName.text = result.disease_name
                    tvConfidence.text = "Confidence: ${result.confidence}"
                    tvSeverityBadge.text = result.severity.uppercase()

                    when (result.severity.uppercase()) {
                        "LOW" -> tvSeverityBadge.setBackgroundColor(Color.parseColor("#16a34a"))
                        "MEDIUM", "MODERATE" -> tvSeverityBadge.setBackgroundColor(Color.parseColor("#ea580c"))
                        "HIGH", "SEVERE" -> tvSeverityBadge.setBackgroundColor(Color.parseColor("#dc2626"))
                        else -> tvSeverityBadge.setBackgroundColor(Color.parseColor("#475569"))
                    }

                    val treatments = mutableListOf<String>()
                    result.treatment?.organic?.forEach { treatments.add("• (Organic) $it") }
                    result.treatment?.chemical?.forEach { treatments.add("• (Chemical) $it") }
                    result.treatment?.cultural?.forEach { treatments.add("• (Cultural) $it") }

                    if (treatments.isEmpty()) {
                        tvTreatment.text = "No specific treatment required."
                    } else {
                        tvTreatment.text = treatments.joinToString("\n")
                    }
                }
                is DiagnoseState.Error -> {
                    btnDiagnose.text = "✨ Run Instant AI Pathology Scan"
                    btnDiagnose.isEnabled = true
                    progressDiagnose.visibility = View.GONE
                    btnRemoveImage.visibility = View.VISIBLE
                    Toast.makeText(requireContext(), state.message, Toast.LENGTH_LONG).show()
                }
            }
        }
    }
}
