/**
 * Transactions Page
 * ==================
 * Features:
 *   - Form to add a new transaction (title, amount, category, date, description)
 *   - Full list of this month's transactions
 *   - Delete button for each transaction
 *   - Month/year navigation
 *
 * LEARNING — Optimistic vs Pessimistic UI updates:
 *   "Pessimistic" (what we use): Wait for the API to confirm success,
 *    THEN update the UI. Safer. We re-fetch after every create/delete.
 *
 *   "Optimistic": Update the UI IMMEDIATELY, then confirm with the API.
 *    If the API fails, roll back. Feels faster but more complex to implement.
 *
 * LEARNING — Derived State:
 *   Instead of storing totals in state, we COMPUTE them from existing state:
 *     const total = transactions.reduce((sum, t) => sum + t.amount, 0)
 *   If the transactions array changes (add/delete), the total auto-updates.
 *   Never store data that can be derived from other state.
 */
import { useState, useEffect } from 'react'
import api from '../api/axios'

const CATEGORIES = [
  { value: 'food',          label: 'Food & Dining' },
  { value: 'entertainment', label: 'Entertainment' },
  { value: 'shopping',      label: 'Shopping' },
  { value: 'fitness',       label: 'Fitness' },
  { value: 'travel',        label: 'Travel' },
  { value: 'utilities',     label: 'Utilities & Bills' },
  { value: 'income',        label: 'Income' },
  { value: 'other',         label: 'Other' },
]

const fmt = (n) => `$${Number(n).toLocaleString('en-US', { minimumFractionDigits: 2 })}`

const EMPTY_FORM = {
  title: '',
  amount: '',
  category: 'food',
  date: new Date().toISOString().split('T')[0],  // Today's date in YYYY-MM-DD
  description: '',
}

export default function Transactions() {
  // Read cache synchronously for current month so first render has data immediately
  const _now        = new Date()
  const _initMonth  = _now.getMonth() + 1
  const _initYear   = _now.getFullYear()
  const _txCached   = sessionStorage.getItem(`tx_cache_${_initMonth}_${_initYear}`)
  const _initTx     = _txCached ? JSON.parse(_txCached) : []

  const [transactions, setTransactions] = useState(_initTx)
  const [form, setForm]       = useState(EMPTY_FORM)
  const [loading, setLoading] = useState(!_txCached)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError]     = useState('')
  const [showForm, setShowForm] = useState(false)

  // Month/year filter — defaults to current month
  const [month, setMonth] = useState(_initMonth)
  const [year, setYear]   = useState(_initYear)

  useEffect(() => {
    fetchTransactions()
  }, [month, year])  // Re-fetch whenever month or year changes

  const fetchTransactions = async () => {
    const cacheKey = `tx_cache_${month}_${year}`
    const cached = sessionStorage.getItem(cacheKey)
    if (cached) {
      setTransactions(JSON.parse(cached))
      setLoading(false)
    } else {
      setLoading(true)
    }
    try {
      const { data } = await api.get(`/transactions/?month=${month}&year=${year}`)
      setTransactions(data)
      sessionStorage.setItem(cacheKey, JSON.stringify(data))
    } catch (err) {
      if (!cached) setError('Failed to load transactions.')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')

    try {
      await api.post('/transactions/', form)
      setForm(EMPTY_FORM)
      setShowForm(false)
      sessionStorage.removeItem(`tx_cache_${month}_${year}`)
      fetchTransactions()
    } catch (err) {
      const data = err.response?.data
      if (typeof data === 'object') {
        setError(Object.values(data).flat().join(' '))
      } else {
        setError('Failed to add transaction.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this transaction?')) return

    try {
      await api.delete(`/transactions/${id}/`)
      sessionStorage.removeItem(`tx_cache_${month}_${year}`)
      setTransactions(prev => prev.filter(t => t.id !== id))
    } catch (err) {
      setError('Failed to delete transaction.')
    }
  }

  // Derived values — computed from state, not stored separately
  const expenses = transactions.filter(t => t.category !== 'income')
  const income   = transactions.filter(t => t.category === 'income')
  const totalExpenses = expenses.reduce((sum, t) => sum + parseFloat(t.amount), 0)
  const totalIncome   = income.reduce((sum, t)   => sum + parseFloat(t.amount), 0)

  const monthName = new Date(year, month - 1).toLocaleString('default', { month: 'long' })

  return (
    <div className="page">
      {/* Header row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 className="page-title" style={{ margin: 0 }}>Transactions</h1>
        <button
          className="btn btn-primary"
          onClick={() => setShowForm(v => !v)}
        >
          {showForm ? 'Cancel' : '+ Add Transaction'}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Add Transaction Form */}
      {showForm && (
        <div className="card" style={{ marginBottom: '1.25rem' }}>
          <div className="card-title">New Transaction</div>
          <form onSubmit={handleSubmit}>
            <div className="grid-2">
              <div className="form-group">
                <label>Title *</label>
                <input
                  name="title"
                  value={form.title}
                  onChange={handleChange}
                  placeholder="e.g. Grocery run"
                  required
                />
              </div>
              <div className="form-group">
                <label>Amount ($) *</label>
                <input
                  name="amount"
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={form.amount}
                  onChange={handleChange}
                  placeholder="0.00"
                  required
                />
              </div>
            </div>

            <div className="grid-2">
              <div className="form-group">
                <label>Category *</label>
                <select name="category" value={form.category} onChange={handleChange}>
                  {CATEGORIES.map(c => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Date *</label>
                <input
                  name="date"
                  type="date"
                  value={form.date}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label>Notes (optional)</label>
              <input
                name="description"
                value={form.description}
                onChange={handleChange}
                placeholder="Any extra details..."
              />
            </div>

            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Saving...' : 'Add Transaction'}
            </button>
          </form>
        </div>
      )}

      {/* Month Navigation + Summary */}
      <div className="card" style={{ marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          {/* Month/Year controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <select
              value={month}
              onChange={e => setMonth(Number(e.target.value))}
              style={{ width: 'auto' }}
            >
              {Array.from({ length: 12 }, (_, i) => (
                <option key={i+1} value={i+1}>
                  {new Date(2000, i).toLocaleString('default', { month: 'long' })}
                </option>
              ))}
            </select>
            <select
              value={year}
              onChange={e => setYear(Number(e.target.value))}
              style={{ width: 'auto' }}
            >
              {[year - 1, year, year + 1].map(y => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>

          {/* Summary totals */}
          <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.9rem' }}>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Expenses: </span>
              <strong style={{ color: 'var(--danger)' }}>{fmt(totalExpenses)}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Income: </span>
              <strong style={{ color: 'var(--success)' }}>{fmt(totalIncome)}</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>{transactions.length} transactions</span>
            </div>
          </div>
        </div>
      </div>

      {/* Transaction List */}
      <div className="card">
        <div className="card-title">{monthName} {year}</div>

        {loading ? (
          <div className="loading">Loading...</div>
        ) : transactions.length === 0 ? (
          <div className="empty-state">
            <h3>No transactions yet</h3>
            <p>Click "Add Transaction" above to record your first one.</p>
          </div>
        ) : (
          transactions.map(tx => (
            <div key={tx.id} className="transaction-item">
              <div>
                <div className="transaction-title">{tx.title}</div>
                <div className="transaction-meta">
                  <span className={`badge badge-${tx.category}`}>{tx.category_display}</span>
                  <span>{tx.date}</span>
                  {tx.description && <span>· {tx.description}</span>}
                </div>
              </div>
              <div className={`transaction-amount ${tx.category === 'income' ? 'amount-income' : 'amount-expense'}`}>
                {tx.category === 'income' ? '+' : '-'}{fmt(tx.amount)}
              </div>
              <button
                className="btn btn-danger btn-sm"
                onClick={() => handleDelete(tx.id)}
                title="Delete transaction"
              >
                ×
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
