/**
 * Authentication Context
 * =======================
 * LEARNING — React Context API:
 *   Context solves the "prop drilling" problem. Without context, if you need
 *   the logged-in user's data in a deeply nested component, you'd have to
 *   pass it as props through every intermediate component — tedious and messy.
 *
 *   Context creates a "global store" that any component in the tree can
 *   subscribe to directly, regardless of nesting depth.
 *
 * HOW IT WORKS:
 *   1. createContext() creates the context object
 *   2. AuthProvider wraps the app and provides values
 *   3. Any component calls useAuth() to access those values
 *
 * The AuthContext stores:
 *   - user:     The logged-in user object (null if logged out)
 *   - loading:  True while checking if the user is already logged in
 *   - login():  Authenticates and stores tokens
 *   - logout(): Clears tokens and user state
 *   - register(): Creates a new account
 *   - updateUser(): Updates local user state (e.g., after changing interests)
 */
import { createContext, useContext, useState, useEffect } from 'react'
import api from '../api/axios'

// Step 1: Create the context with a default value
const AuthContext = createContext(null)

// Step 2: Create the Provider component
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)  // True until we check localStorage

  // On app mount: check if a valid session exists in localStorage
  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      // Try to fetch the user's profile to verify the token is still valid
      api.get('/users/profile/')
        .then(({ data }) => setUser(data))
        .catch(() => {
          // Token is invalid or expired — clear it
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  /**
   * Login: exchange username + password for JWT tokens
   * The backend returns { access: "...", refresh: "..." }
   * We store both and fetch the user profile.
   */
  const login = async (username, password) => {
    const { data } = await api.post('/token/', { username, password })
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)

    // Fetch the full user profile to populate the user state
    const profileRes = await api.get('/users/profile/')
    setUser(profileRes.data)
    return profileRes.data
  }

  /**
   * Register: create a new account, then log in automatically
   */
  const register = async (userData) => {
    await api.post('/users/register/', userData)
    return login(userData.username, userData.password)
  }

  /**
   * Logout: clear all stored auth data
   */
  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setUser(null)
  }

  /**
   * Update the local user state (e.g., after the user changes their interests)
   * without needing a full re-login.
   */
  const updateUser = (updatedData) => {
    setUser(prev => ({ ...prev, ...updatedData }))
  }

  // Step 3: Provide values to all child components
  return (
    <AuthContext.Provider value={{ user, loading, login, logout, register, updateUser }}>
      {children}
    </AuthContext.Provider>
  )
}

// Step 4: Custom hook for easy access
// Instead of: const { user } = useContext(AuthContext)
// Components write: const { user } = useAuth()
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}
