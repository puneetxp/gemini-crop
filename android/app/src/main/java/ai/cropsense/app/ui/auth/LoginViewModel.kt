package ai.cropsense.app.ui.auth

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import ai.cropsense.app.data.SessionManager
import ai.cropsense.app.network.AuthApiService
import ai.cropsense.app.network.DemoSignInRequest
import ai.cropsense.app.network.SignInRequest
import kotlinx.coroutines.launch

sealed class AuthState {
    object Idle : AuthState()
    object Loading : AuthState()
    object DemoLoading : AuthState()
    data class Success(val email: String) : AuthState()
    data class Error(val message: String) : AuthState()
}

class LoginViewModel(
    private val authApiService: AuthApiService,
    private val sessionManager: SessionManager
) : ViewModel() {

    private val _authState = MutableLiveData<AuthState>(AuthState.Idle)
    val authState: LiveData<AuthState> = _authState

    fun signIn(username: String, password: String?) {
        _authState.value = AuthState.Loading
        viewModelScope.launch {
            try {
                val response = authApiService.signIn(SignInRequest(username, password))
                if (response.isSuccessful && response.body() != null) {
                    val body = response.body()!!
                    sessionManager.saveTokens(body.access_token, body.refresh_token)
                    sessionManager.saveUserDetails(body.user?.email ?: "", body.user?.name ?: "")
                    _authState.value = AuthState.Success(body.user?.email ?: username)
                } else {
                    _authState.value = AuthState.Error("Sign in failed: ${response.message()}")
                }
            } catch (e: Exception) {
                _authState.value = AuthState.Error(e.message ?: "Network error occurred")
            }
        }
    }

    fun demoSignIn() {
        _authState.value = AuthState.DemoLoading
        viewModelScope.launch {
            try {
                val response = authApiService.demoSignIn(DemoSignInRequest())
                if (response.isSuccessful && response.body() != null) {
                    val body = response.body()!!
                    sessionManager.saveTokens(body.access_token, body.refresh_token)
                    sessionManager.saveUserDetails(body.user?.email ?: "", body.user?.name ?: "")
                    _authState.value = AuthState.Success(body.user?.email ?: "demo@cropsense.ai")
                } else {
                    _authState.value = AuthState.Error("Demo login failed: ${response.message()}")
                }
            } catch (e: Exception) {
                _authState.value = AuthState.Error(e.message ?: "Network error occurred")
            }
        }
    }
}
