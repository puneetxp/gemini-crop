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

interface AuthApiService {
    @POST("api/v1/auth/signin")
    suspend fun signIn(@Body request: SignInRequest): Response<SignInResponse>

    @POST("api/v1/auth/demo")
    suspend fun demoSignIn(@Body request: DemoSignInRequest): Response<SignInResponse>
}
