package ai.cropsense.app.ui.diagnose

import android.graphics.Bitmap
import android.util.Base64
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import ai.cropsense.app.network.AuthApiService
import ai.cropsense.app.network.DiagnoseRequest
import ai.cropsense.app.network.DiagnosisResult
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream

sealed class DiagnoseState {
    object Idle : DiagnoseState()
    data class ImageSelected(val bitmap: Bitmap) : DiagnoseState()
    object Analyzing : DiagnoseState()
    data class Success(val result: DiagnosisResult, val image: Bitmap) : DiagnoseState()
    data class Error(val message: String) : DiagnoseState()
}

class DiagnoseViewModel(
    private val apiService: AuthApiService
) : ViewModel() {

    private val _state = MutableLiveData<DiagnoseState>(DiagnoseState.Idle)
    val state: LiveData<DiagnoseState> = _state

    private var currentBitmap: Bitmap? = null

    fun setImage(bitmap: Bitmap) {
        currentBitmap = bitmap
        _state.value = DiagnoseState.ImageSelected(bitmap)
    }

    fun removeImage() {
        currentBitmap = null
        _state.value = DiagnoseState.Idle
    }

    fun analyzeImage() {
        val bitmap = currentBitmap ?: return
        _state.value = DiagnoseState.Analyzing

        viewModelScope.launch {
            try {
                // Compress and encode to Base64 on IO thread
                val base64Image = withContext(Dispatchers.IO) {
                    val outputStream = ByteArrayOutputStream()
                    // Resize if too large to save bandwidth & memory
                    val maxWidth = 1024
                    val maxHeight = 1024
                    val scale = Math.min(
                        maxWidth.toFloat() / bitmap.width,
                        maxHeight.toFloat() / bitmap.height
                    )
                    val scaledBitmap = if (scale < 1) {
                        Bitmap.createScaledBitmap(
                            bitmap,
                            (bitmap.width * scale).toInt(),
                            (bitmap.height * scale).toInt(),
                            true
                        )
                    } else bitmap

                    scaledBitmap.compress(Bitmap.CompressFormat.JPEG, 80, outputStream)
                    Base64.encodeToString(outputStream.toByteArray(), Base64.NO_WRAP)
                }

                val request = DiagnoseRequest(
                    image_base64 = base64Image,
                    lang = "en"
                )

                val response = apiService.diagnoseCrop(request)

                if (response.isSuccessful && response.body() != null) {
                    val result = response.body()!!.diagnosis
                    _state.value = DiagnoseState.Success(result, bitmap)
                } else {
                    _state.value = DiagnoseState.Error("Diagnosis failed: ${response.message()}")
                }

            } catch (e: Exception) {
                _state.value = DiagnoseState.Error(e.message ?: "Network error during analysis")
            }
        }
    }
}
