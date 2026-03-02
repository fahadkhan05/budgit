/**
 * Navbar Component
 * =================
 * LEARNING — Dark Mode with useEffect + localStorage:
 *   We store the theme preference in localStorage so it persists across
 *   page refreshes. On mount, we read it. On toggle, we write it.
 *
 *   document.documentElement is the <html> element. Setting a data-theme
 *   attribute on it lets CSS target [data-theme="dark"] globally.
 *
 *   The () => ... initializer in useState runs ONCE on mount, so reading
 *   from localStorage here is efficient — it doesn't run on every render.
 */
import { useState, useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()

  const [theme, setTheme] = useState(
    () => localStorage.getItem('theme') || 'light'
  )

  // Apply the theme to the <html> element whenever it changes
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggleTheme = () => setTheme(t => t === 'light' ? 'dark' : 'light')

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <NavLink to="/dashboard" className="navbar-brand">
          Budg<span style={{ color: '#f97316' }}>it</span>
        </NavLink>

        <div className="navbar-links">
          <NavLink to="/dashboard" className={({ isActive }) =>
            `navbar-link ${isActive ? 'active' : ''}`
          }>
            Dashboard
          </NavLink>
          <NavLink to="/transactions" className={({ isActive }) =>
            `navbar-link ${isActive ? 'active' : ''}`
          }>
            Transactions
          </NavLink>
          <NavLink to="/recommendations" className={({ isActive }) =>
            `navbar-link ${isActive ? 'active' : ''}`
          }>
            Recommendations
          </NavLink>
          <NavLink to="/bank-accounts" className={({ isActive }) =>
            `navbar-link ${isActive ? 'active' : ''}`
          }>
            Bank Accounts
          </NavLink>
        </div>

        <div className="navbar-user">
          <span>Hi, {user?.first_name || user?.username}</span>
          <button className="btn btn-icon" onClick={toggleTheme} title="Toggle theme">
            {theme === 'light' ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="5"/>
                <line x1="12" y1="1" x2="12" y2="3"/>
                <line x1="12" y1="21" x2="12" y2="23"/>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                <line x1="1" y1="12" x2="3" y2="12"/>
                <line x1="21" y1="12" x2="23" y2="12"/>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
              </svg>
            )}
          </button>
          <button className="btn btn-secondary btn-sm" onClick={logout}>
            Log out
          </button>
        </div>
      </div>
    </nav>
  )
}
