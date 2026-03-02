/**
 * Axios Instance with JWT Interceptors
 * ======================================
 * Instead of using the raw `axios` library everywhere, we create a
 * pre-configured INSTANCE that automatically:
 *
 *   1. Attaches the Authorization header to every request
 *   2. Handles 401 (Unauthorized) errors by trying to refresh the token
 *   3. If the refresh fails, logs the user out
 *
 * LEARNING — Why Interceptors?
 *   Without interceptors, every component that makes an API call would need
 *   to manually attach the token header, check for 401s, and refresh.
 *   That's a LOT of duplicated code. Interceptors centralize this logic.
 *
 * LEARNING — Access Token vs Refresh Token flow:
 *   1. User logs in → backend returns { access: "...", refresh: "..." }
 *   2. We store both in localStorage
 *   3. Every API request: attach access token in Authorization header
 *   4. Access token expires after 1 hour → backend returns 401
 *   5. Our interceptor catches 401, sends refresh token to /api/token/refresh/
 *   6. Backend returns a new access token → retry the original request
 *   7. If refresh also fails → force logout
 */
import axios from 'axios'

// In dev: falls back to '/api' (Vite proxy forwards to localhost:8000)
// In prod: set VITE_API_URL=https://your-backend.up.railway.app/api in Vercel
const BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: BASE_URL,
})

// ---- REQUEST Interceptor ----
// Runs BEFORE every request is sent
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    // Attach the token as a Bearer token in the Authorization header
    // This is how DRF's JWTAuthentication identifies the user
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ---- RESPONSE Interceptor ----
// Runs AFTER every response is received (including errors)
api.interceptors.response.use(
  // Success: just pass the response through unchanged
  (response) => response,

  // Error: check if it's a 401, and if so, try to refresh
  async (error) => {
    const originalRequest = error.config

    // _retry flag prevents infinite loops
    // (if the refresh request itself fails with 401, don't retry again)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) throw new Error('No refresh token')

        // Call the token refresh endpoint
        // Note: we use plain axios (not our instance) to avoid the interceptor loop
        const { data } = await axios.post(`${BASE_URL}/token/refresh/`, {
          refresh: refreshToken,
        })

        // Store the new access token
        localStorage.setItem('access_token', data.access)

        // Update the Authorization header and retry the original request
        originalRequest.headers.Authorization = `Bearer ${data.access}`
        return api(originalRequest)

      } catch (refreshError) {
        // Refresh token is also expired or invalid → force logout
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default api
