package ai.cropsense.app.network

import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

data class SignInRequest(
    val username: String,
    val password: String? = null
)

data class DemoSignInRequest(
    val lang: String = "en"
)

data class SignInUser(
    val id: Long,
    val username: String,
    val email: String,
    val name: String,
    val user_type: String
)

data class SignInResponse(
    val access_token: String,
    val id_token: String,
    val refresh_token: String,
    val expires_in: Int,
    val token_type: String = "Bearer",
    val user: SignInUser? = null
)

data class DiagnoseRequest(
    val image_base64: String,
    val mime_type: String = "image/jpeg",
    val lang: String = "en"
)

data class DiagnosisTreatment(
    val cultural: List<String>? = null,
    val organic: List<String>? = null,
    val chemical: List<String>? = null
)

data class DiagnosisSafety(
    val removed: List<Map<String, String>>? = null,
    val label_note: String? = null
)

data class DiagnosisResult(
    val disease_name: String,
    val confidence: String,
    val severity: String,
    val treatment: DiagnosisTreatment? = null,
    val safety: DiagnosisSafety? = null,
    val better_photo_tip: String? = null
)

data class DiagnoseResponse(
    val success: Boolean,
    val diagnosis: DiagnosisResult
)

interface AuthApiService {
    @POST("api/v1/auth/signin")
    suspend fun signIn(@Body request: SignInRequest): Response<SignInResponse>

    @POST("api/v1/auth/demo")
    suspend fun demoSignIn(@Body request: DemoSignInRequest): Response<SignInResponse>

    @POST("api/v1/vision/diagnose-crop")
    suspend fun diagnoseCrop(@Body request: DiagnoseRequest): Response<DiagnoseResponse>
}
