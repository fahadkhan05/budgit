/**
 * Recommendations Page
 * =====================
 * This page lets users:
 *   1. View and update their interest categories
 *   2. See their remaining budget
 *   3. Get personalized activity/purchase recommendations
 *
 * LEARNING — Lifting State:
 *   The user's interests exist on the server. We fetch them, let the user
 *   modify them locally (pending state), then SAVE with an API call.
 *   This is the "optimistic form" pattern — local state for the form,
 *   server state is the source of truth.
 *
 * LEARNING — Separation of edit vs display:
 *   We keep `pendingInterests` separate from what's shown in the recs.
 *   The recs only update after the user saves, preventing confusion.
 */
import { useState, useEffect } from 'react'
import api from '../api/axios'
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

const TIER_LABELS = {
  tier1: 'Under $25',
  tier2: '$25 – $75',
  tier3: '$75 – $200',
  tier4: '$200+',
}

const fmt = (n) => `$${Number(n).toLocaleString('en-US', { minimumFractionDigits: 2 })}`

export default function Recommendations() {
  const { user, updateUser } = useAuth()

  const [data, setData]             = useState(null)  // { recommendations, interests, ... }
  const [budgetStats, setBudgetStats] = useState(null) // { budget_amount, total_spent, remaining_budget }
  const [loading, setLoading]       = useState(true)   // true only on the very first load
  const [refreshing, setRefreshing] = useState(false)  // true only when re-fetching after first load
  const [saving, setSaving]         = useState(false)
  const [error, setError]           = useState('')
  const [successMsg, setSuccessMsg] = useState('')

  // Local copy of interests for the edit form
  const [pendingInterests, setPendingInterests] = useState(user?.interests || [])

  useEffect(() => {
    // Always fetch live budget stats so the numbers reflect latest transactions
    fetchBudgetStats()

    // LEARNING — sessionStorage caching:
    //   sessionStorage persists data for the lifetime of the browser tab.
    //   On the first visit we fetch from the API and save the result.
    //   On every return visit we load from cache instantly — no API call needed.
    //   The user can still force a fresh AI call by clicking Refresh.
    const cached = sessionStorage.getItem('recommendations_cache')
    if (cached) {
      const parsed = JSON.parse(cached)
      setData(parsed)
      setPendingInterests(parsed.interests || [])
      setLoading(false)
    } else {
      fetchRecommendations(true)
    }
  }, [])

  const fetchBudgetStats = async () => {
    try {
      const now = new Date()
      const [budgetRes, statsRes] = await Promise.all([
        api.get('/budgets/current/'),
        api.get(`/transactions/stats/?month=${now.getMonth() + 1}&year=${now.getFullYear()}`),
      ])
      const budgetAmount = parseFloat(budgetRes.data.amount || 0)
      const totalSpent   = parseFloat(statsRes.data.total_spent || 0)
      setBudgetStats({
        budget_amount:    budgetAmount,
        total_spent:      totalSpent,
        remaining_budget: budgetAmount - totalSpent,
      })
    } catch {
      // Non-critical — fall back to cached data if available
    }
  }

  const fetchRecommendations = async (isInitial = false) => {
    // LEARNING — Two loading states:
    //   isInitial=true  → blank the whole page (first visit, nothing to show yet)
    //   isInitial=false → only the cards grid shows a spinner; the rest stays visible
    if (isInitial) setLoading(true)
    else setRefreshing(true)

    try {
      const { data: res } = await api.get('/recommendations/')
      sessionStorage.setItem('recommendations_cache', JSON.stringify(res))
      setData(res)
      setPendingInterests(res.interests || [])
    } catch (err) {
      setError('Failed to load recommendations.')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const toggleInterest = (key) => {
    setPendingInterests(prev =>
      prev.includes(key)
        ? prev.filter(i => i !== key)
        : [...prev, key]
    )
  }

  const saveInterestsAndRefresh = async () => {
    setSaving(true)
    setError('')
    setSuccessMsg('')

    try {
      // Save the updated interests to the user profile
      await api.patch('/users/profile/', { interests: pendingInterests })

      // Update the local auth context so the navbar/other components see the new interests
      updateUser({ interests: pendingInterests })

      // Re-fetch recommendations with the new interests
      await fetchRecommendations()

      setSuccessMsg('Interests updated! Here are your new recommendations.')
      setTimeout(() => setSuccessMsg(''), 3000)
    } catch (err) {
      setError('Failed to save interests.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="loading">Loading recommendations...</div>

  const hasInterestChanges =
    JSON.stringify([...pendingInterests].sort()) !==
    JSON.stringify([...(data?.interests || [])].sort())

  return (
    <div className="page">
      <h1 className="page-title">Recommendations</h1>

      {error   && <div className="alert alert-error">{error}</div>}
      {successMsg && <div className="alert alert-success">{successMsg}</div>}

      {/* Budget Context — always live, fetched independently from recommendations cache */}
      {budgetStats && (
        <div className="grid-3" style={{ marginBottom: '1.25rem' }}>
          <div className="card">
            <div className="card-title">Monthly Budget</div>
            <div className="stat-number" style={{ color: 'var(--primary)' }}>
              {fmt(budgetStats.budget_amount)}
            </div>
          </div>
          <div className="card">
            <div className="card-title">Spent So Far</div>
            <div className="stat-number" style={{ color: 'var(--danger)' }}>
              {fmt(budgetStats.total_spent)}
            </div>
          </div>
          <div className="card">
            <div className="card-title">Still Available</div>
            <div className="stat-number" style={{
              color: budgetStats.remaining_budget >= 0 ? 'var(--success)' : 'var(--danger)'
            }}>
              {fmt(budgetStats.remaining_budget)}
            </div>
            <div className="stat-label">
              Recommendations based on this amount
            </div>
          </div>
        </div>
      )}

      {/* Interest Selector */}
      <div className="card" style={{ marginBottom: '1.25rem' }}>
        <div className="card-title">Your Interests</div>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
          Select what you enjoy. We'll suggest activities and purchases that fit your remaining budget.
        </p>

        <div className="interest-grid" style={{ marginBottom: '1rem' }}>
          {ALL_INTERESTS.map(({ key, label }) => (
            <div
              key={key}
              className={`interest-chip ${pendingInterests.includes(key) ? 'selected' : ''}`}
              onClick={() => toggleInterest(key)}
            >
              {label}
            </div>
          ))}
        </div>

        <button
          className="btn btn-primary"
          onClick={saveInterestsAndRefresh}
          disabled={saving || pendingInterests.length === 0}
        >
          {saving ? 'Updating...' : hasInterestChanges ? '✓ Save & Refresh Recommendations' : '↺ Refresh Recommendations'}
        </button>

        {pendingInterests.length === 0 && (
          <p style={{ fontSize: '0.8rem', color: 'var(--danger)', marginTop: '0.5rem' }}>
            Please select at least one interest.
          </p>
        )}
      </div>

      {/* Recommendations Grid */}
      <div className="card-title" style={{ marginBottom: '0.75rem' }}>
        {data?.recommendations?.length > 0
          ? `${data.recommendations.length} ideas for you`
          : 'No recommendations yet'}
      </div>

      {refreshing ? (
        <div className="spinner-wrap">
          <div className="spinner" />
          Generating recommendations...
        </div>
      ) : data?.recommendations?.length === 0 ? (
        <div className="empty-state">
          <h3>Select your interests above</h3>
          <p>Choose what you enjoy and we'll find things that fit your budget.</p>
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
          gap: '1rem'
        }}>
          {data.recommendations.map((rec, i) => (
            <RecommendationCard key={i} rec={rec} />
          ))}
        </div>
      )}
    </div>
  )
}

/**
 * RecommendationCard — A presentational component.
 *
 * LEARNING: Extracting a small component for a repeated UI element is good practice.
 * This card is "dumb" — it only receives props and renders. No state, no side effects.
 * These are the easiest components to understand and test.
 */
function RecommendationCard({ rec }) {
  return (
    <div className="rec-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div className="rec-card-title">{rec.title}</div>
        <span className="badge" style={{
          background: 'var(--primary-light)',
          color: 'var(--primary)',
          marginLeft: '0.5rem',
          flexShrink: 0,
          fontSize: '0.7rem'
        }}>
          {TIER_LABELS[rec.budget_tier] || rec.budget_tier}
        </span>
      </div>

      <div className="rec-card-desc">{rec.description}</div>

      <hr className="divider" style={{ margin: '0.5rem 0' }} />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div className="rec-card-cost">{rec.estimated_cost}</div>
        <div className="rec-card-category" style={{ textTransform: 'capitalize' }}>
          {rec.interest_category}
        </div>
      </div>
    </div>
  )
}
