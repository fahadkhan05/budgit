import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const ALL_INTERESTS = [
  { key: 'dining',        label: 'Dining' },
  { key: 'fitness',       label: 'Fitness' },
  { key: 'entertainment', label: 'Entertainment' },
  { key: 'travel',        label: 'Travel' },
  { key: 'shopping',      label: 'Shopping' },
  { key: 'arts',          label: 'Arts & Culture' },
  { key: 'outdoor',       label: 'Outdoor' },
  { key: 'technology',    label: 'Technology' },
]

/** Single row in the password requirements checklist */
function Requirement({ met, text }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '0.5rem',
      fontSize: '0.8rem',
      color: met ? 'var(--success)' : 'var(--text-muted)',
      transition: 'color 0.2s',
    }}>
      <span style={{
        width: '1rem',
        height: '1rem',
        borderRadius: '50%',
        border: `2px solid ${met ? 'var(--success)' : 'var(--border)'}`,
        background: met ? 'var(--success)' : 'transparent',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
        transition: 'all 0.2s',
      }}>
        {met && (
          <svg width="8" height="8" viewBox="0 0 10 10" fill="none">
            <polyline points="1.5,5 4,7.5 8.5,2.5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        )}
      </span>
      {text}
    </div>
  )
}

export default function Register() {
  const [form, setForm] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    password: '',
    password2: '',
    interests: [],
  })
  const [error, setError]     = useState('')
  const [loading, setLoading] = useState(false)

  const { register } = useAuth()
  const navigate      = useNavigate()

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
  }

  const toggleInterest = (key) => {
    setForm(prev => {
      const already = prev.interests.includes(key)
      return {
        ...prev,
        interests: already
          ? prev.interests.filter(i => i !== key)
          : [...prev.interests, key]
      }
    })
  }

  // Password requirement checks
  const req = {
    minLength:     form.password.length >= 8,
    hasLetter:     /[a-zA-Z]/.test(form.password),
    notCommon:     form.password.length >= 4,   // basic proxy — server validates fully
    passwordMatch: form.password.length > 0 && form.password === form.password2,
  }
  const allReqMet = req.minLength && req.hasLetter && req.passwordMatch

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (form.password !== form.password2) {
      setError("Passwords don't match.")
      return
    }

    setLoading(true)
    try {
      await register(form)
      navigate('/dashboard')
    } catch (err) {
      const data = err.response?.data
      if (typeof data === 'object') {
        const messages = Object.entries(data)
          .map(([field, errs]) => `${field}: ${Array.isArray(errs) ? errs.join(' ') : errs}`)
          .join('\n')
        setError(messages)
      } else {
        setError('Registration failed. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-card" style={{ maxWidth: '520px' }}>

        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
          <div style={{ fontFamily: "'Raleway', sans-serif", fontSize: '2.75rem', fontWeight: 700, letterSpacing: '0.01em', lineHeight: 1 }}>
            <span style={{ color: 'var(--primary)' }}>Budg</span><span style={{ color: '#f97316' }}>it</span>
          </div>
          <p style={{ marginTop: '0.5rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Create your account and start tracking
          </p>
        </div>

        {error && (
          <div className="alert alert-error" style={{ whiteSpace: 'pre-line' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="grid-2">
            <div className="form-group">
              <label>First Name</label>
              <input name="first_name" value={form.first_name} onChange={handleChange} placeholder="Jane" />
            </div>
            <div className="form-group">
              <label>Last Name</label>
              <input name="last_name" value={form.last_name} onChange={handleChange} placeholder="Doe" />
            </div>
          </div>

          <div className="form-group">
            <label>Username *</label>
            <input name="username" value={form.username} onChange={handleChange} placeholder="janedoe" required />
          </div>

          <div className="form-group">
            <label>Email</label>
            <input name="email" type="email" value={form.email} onChange={handleChange} placeholder="jane@example.com" />
          </div>

          {/* Password with live requirements */}
          <div className="form-group">
            <label>Password *</label>
            <input
              name="password"
              type="password"
              value={form.password}
              onChange={handleChange}
              placeholder="••••••••"
              required
            />
            {/* Show checklist once the user starts typing */}
            {form.password.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', marginTop: '0.6rem' }}>
                <Requirement met={req.minLength}  text="At least 8 characters" />
                <Requirement met={req.hasLetter}  text="Contains at least one letter" />
              </div>
            )}
          </div>

          <div className="form-group">
            <label>Confirm Password *</label>
            <input
              name="password2"
              type="password"
              value={form.password2}
              onChange={handleChange}
              placeholder="••••••••"
              required
            />
            {form.password2.length > 0 && (
              <div style={{ marginTop: '0.6rem' }}>
                <Requirement met={req.passwordMatch} text="Passwords match" />
              </div>
            )}
          </div>

          {/* Interest picker */}
          <div className="form-group">
            <label>What are you into? (optional)</label>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
              We'll use these to make personalized recommendations.
            </p>
            <div className="interest-grid">
              {ALL_INTERESTS.map(({ key, label }) => (
                <div
                  key={key}
                  className={`interest-chip ${form.interests.includes(key) ? 'selected' : ''}`}
                  onClick={() => toggleInterest(key)}
                >
                  {label}
                </div>
              ))}
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '0.5rem' }}
            disabled={loading || !allReqMet}
          >
            {loading ? 'Creating account...' : 'Create Account'}
          </button>

          {!allReqMet && form.password.length > 0 && (
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center', marginTop: '0.5rem' }}>
              Complete all password requirements to continue
            </p>
          )}
        </form>

        <div className="auth-link">
          Already have an account? <Link to="/login">Log in</Link>
        </div>
      </div>
    </div>
  )
}
