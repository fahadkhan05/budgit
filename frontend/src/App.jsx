/**
 * App.jsx — Root Component and Router
 * =====================================
 * LEARNING — React Router v6:
 *   React Router enables "client-side routing" — navigating between pages
 *   without a full browser reload. The URL changes, but only the React
 *   components swap out. This is what makes it a Single Page Application (SPA).
 *
 *   Key components:
 *     <BrowserRouter>    — Uses the HTML5 History API for clean URLs (/dashboard)
 *     <Routes>           — Container for all <Route> definitions
 *     <Route>            — Maps a URL path to a component
 *     <Navigate>         — Programmatically redirects to a different route
 *
 * LEARNING — Protected Routes:
 *   We create a <PrivateRoute> component that checks if the user is logged in.
 *   If not, it redirects to /login. This prevents unauthenticated users from
 *   accessing pages like the dashboard.
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Navbar from './components/Navbar'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Transactions from './pages/Transactions'
import Recommendations from './pages/Recommendations'
import BankAccounts from './pages/BankAccounts'

/**
 * PrivateRoute: Wraps pages that require authentication.
 *
 * How it works:
 *   - If still checking auth status (loading=true): show nothing
 *   - If user is logged in: render the requested page + Navbar
 *   - If not logged in: redirect to /login
 */
function PrivateRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  if (!user) {
    // <Navigate> replaces the current URL — the user ends up at /login
    // replace={true} means the current entry is replaced in history,
    // so hitting "back" won't loop them back to the protected page
    return <Navigate to="/login" replace />
  }

  return (
    <>
      <Navbar />
      {children}
    </>
  )
}

/**
 * PublicRoute: Wraps auth pages (login, register).
 * If the user is ALREADY logged in, redirect them to the dashboard.
 */
function PublicRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (user) return <Navigate to="/dashboard" replace />
  return children
}

export default function App() {
  return (
    // BrowserRouter provides routing context to all child components
    <BrowserRouter>
      {/* AuthProvider provides authentication context to the entire app */}
      <AuthProvider>
        <Routes>
          {/* Public routes — redirect to dashboard if already logged in */}
          <Route path="/login" element={
            <PublicRoute><Login /></PublicRoute>
          } />
          <Route path="/register" element={
            <PublicRoute><Register /></PublicRoute>
          } />

          {/* Protected routes — redirect to login if not authenticated */}
          <Route path="/dashboard" element={
            <PrivateRoute><Dashboard /></PrivateRoute>
          } />
          <Route path="/transactions" element={
            <PrivateRoute><Transactions /></PrivateRoute>
          } />
          <Route path="/recommendations" element={
            <PrivateRoute><Recommendations /></PrivateRoute>
          } />
          <Route path="/bank-accounts" element={
            <PrivateRoute><BankAccounts /></PrivateRoute>
          } />

          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
