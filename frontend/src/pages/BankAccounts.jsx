/**
 * Bank Accounts Page
 * ===================
 * Lets users connect their bank accounts via Plaid and sync real transactions.
 *
 * FLOW:
 *   1. Page loads → fetch existing connected banks from backend
 *   2. User clicks "Connect Bank" → backend creates a link_token
 *   3. Plaid Link popup opens → user selects bank + authenticates
 *   4. Plaid calls onSuccess with a public_token
 *   5. We send public_token to backend → backend exchanges it for access_token
 *   6. New bank appears in the list
 *   7. User clicks "Sync" → backend pulls latest transactions from Plaid
 *
 * LEARNING — usePlaidLink hook:
 *   The react-plaid-link library provides a hook that manages the Plaid
 *   Link iframe popup. It needs a link_token (fetched from our backend),
 *   and calls onSuccess when the user successfully authenticates.
 *   'ready' becomes true once the iframe has loaded and open() can be called.
 *
 * LEARNING — Why server-side link_token?
 *   The link_token is created on the backend with our Plaid secret key.
 *   This keeps the secret off the frontend. The token is tied to the user
 *   so Plaid knows which user is connecting.
 */
import { useState, useEffect, useCallback } from 'react'
import { usePlaidLink } from 'react-plaid-link'
import api from '../api/axios'

const fmt = (dt) => {
  if (!dt) return 'Never'
  return new Date(dt).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
  })
}

export default function BankAccounts() {
  // Read cache synchronously so the list renders on first paint
  const _cached    = sessionStorage.getItem('bank_items_cache')
  const _initItems = _cached ? JSON.parse(_cached) : []

  const [items, setItems]           = useState(_initItems)
  const [linkToken, setLinkToken]   = useState(null)
  const [syncing, setSyncing]       = useState(null)  // item id being synced, or 'all'
  const [connecting, setConnecting] = useState(false)
  const [error, setError]           = useState('')
  const [successMsg, setSuccessMsg] = useState('')

  const fetchItems = async () => {
    try {
      const { data } = await api.get('/plaid/items/')
      setItems(data)
      sessionStorage.setItem('bank_items_cache', JSON.stringify(data))
    } catch {
      setError('Failed to load connected banks.')
    }
  }

  const fetchLinkToken = async () => {
    try {
      const { data } = await api.post('/plaid/create-link-token/')
      setLinkToken(data.link_token)
    } catch {
      setError('Could not initialize bank connection. Check your Plaid credentials.')
    }
  }

  useEffect(() => {
    fetchItems()
    fetchLinkToken()
  }, [])

  // Called by Plaid Link after the user successfully authenticates with their bank.
  // public_token is a one-time code we exchange server-side for a permanent access_token.
  const onPlaidSuccess = useCallback(async (public_token, metadata) => {
    setConnecting(true)
    setError('')
    try {
      const institution_name = metadata?.institution?.name || 'Your Bank'
      await api.post('/plaid/exchange-token/', { public_token, institution_name })
      setSuccessMsg(`${institution_name} connected! Click "Sync" to import your transactions.`)
      setTimeout(() => setSuccessMsg(''), 6000)
      await fetchItems()
      // Fetch a fresh link_token for the next connection attempt
      await fetchLinkToken()
    } catch {
      setError('Failed to connect bank. Please try again.')
    } finally {
      setConnecting(false)
    }
  }, [])

  // usePlaidLink manages the Plaid Link popup iframe.
  // 'ready' becomes true once the popup is loaded and safe to open.
  const { open, ready } = usePlaidLink({
    token: linkToken,
    onSuccess: onPlaidSuccess,
  })

  const handleSync = async (itemId = null) => {
    setSyncing(itemId ?? 'all')
    setError('')
    try {
      const body = itemId != null ? { item_id: itemId } : {}
      const { data } = await api.post('/plaid/sync/', body)
      setSuccessMsg(data.message)
      setTimeout(() => setSuccessMsg(''), 5000)
      await fetchItems()
    } catch {
      setError('Sync failed. Please try again.')
    } finally {
      setSyncing(null)
    }
  }

  const handleRemove = async (itemId) => {
    if (!window.confirm('Disconnect this bank account? Your existing transactions will stay.')) return
    try {
      await api.delete(`/plaid/items/${itemId}/remove/`)
      setItems(prev => {
        const updated = prev.filter(i => i.id !== itemId)
        sessionStorage.setItem('bank_items_cache', JSON.stringify(updated))
        return updated
      })
    } catch {
      setError('Failed to disconnect bank.')
    }
  }

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 className="page-title" style={{ margin: 0 }}>Bank Accounts</h1>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          {items.length > 1 && (
            <button
              className="btn btn-secondary"
              onClick={() => handleSync()}
              disabled={syncing !== null}
            >
              {syncing === 'all' ? 'Syncing all…' : '↺ Sync All Banks'}
            </button>
          )}
          <button
            className="btn btn-primary"
            onClick={() => open()}
            disabled={!ready || connecting}
          >
            {connecting ? 'Connecting…' : '+ Connect Bank Account'}
          </button>
        </div>
      </div>

      {error      && <div className="alert alert-error">{error}</div>}
      {successMsg && <div className="alert alert-success">{successMsg}</div>}

      {/* No banks connected yet */}
      {items.length === 0 && (
        <div className="empty-state">
          <h3>No banks connected</h3>
          <p>
            Connect your bank account to automatically import transactions.<br />
            Your credentials are handled securely by Plaid — we never see your password.
          </p>
          <button
            className="btn btn-primary"
            onClick={() => open()}
            disabled={!ready}
            style={{ marginTop: '1rem' }}
          >
            Connect Bank Account
          </button>
        </div>
      )}

      {/* Connected bank cards */}
      {items.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {items.map(item => (
            <BankCard
              key={item.id}
              item={item}
              syncing={syncing === item.id}
              onSync={() => handleSync(item.id)}
              onRemove={() => handleRemove(item.id)}
              fmt={fmt}
            />
          ))}
        </div>
      )}

      {/* Sandbox help box */}
      <div className="card" style={{ marginTop: '2rem', background: 'var(--primary-light)', border: '1px solid var(--primary)' }}>
        <div className="card-title" style={{ color: 'var(--primary)' }}>Sandbox Testing</div>
        <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
          In sandbox mode, use these test credentials in the Plaid popup:
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.875rem' }}>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Username: </span>
            <code style={{ fontFamily: 'monospace', fontWeight: 600 }}>user_good</code>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Password: </span>
            <code style={{ fontFamily: 'monospace', fontWeight: 600 }}>pass_good</code>
          </div>
        </div>
      </div>
    </div>
  )
}

/**
 * BankCard — Displays one connected bank with its accounts and controls.
 *
 * LEARNING: Extracting a sub-component keeps BankAccounts readable.
 * This component is "dumb" — it only receives props and renders + handles clicks.
 */
function BankCard({ item, syncing, onSync, onRemove, fmt }) {
  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.75rem' }}>

        {/* Bank name + last synced */}
        <div>
          <div style={{ fontWeight: 700, fontSize: '1.05rem', marginBottom: '0.25rem' }}>
            {item.institution_name || 'Connected Bank'}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Last synced: {fmt(item.last_synced)}
          </div>
        </div>

        {/* Action buttons */}
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            className="btn btn-primary btn-sm"
            onClick={onSync}
            disabled={syncing}
          >
            {syncing ? 'Syncing…' : '↺ Sync'}
          </button>
          <button
            className="btn btn-secondary btn-sm"
            onClick={onRemove}
            style={{ color: 'var(--danger)' }}
          >
            Disconnect
          </button>
        </div>
      </div>

      {/* Account list */}
      {item.accounts?.length > 0 && (
        <div style={{ marginTop: '1rem' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>
            Accounts
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {item.accounts.map(acct => (
              <div key={acct.account_id} className="badge" style={{ fontSize: '0.8rem', padding: '0.3rem 0.7rem' }}>
                {acct.name}
                {acct.mask && <span style={{ color: 'var(--text-muted)', marginLeft: '0.3rem' }}>••{acct.mask}</span>}
                <span style={{ color: 'var(--text-muted)', marginLeft: '0.3rem', textTransform: 'capitalize' }}>· {acct.type}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
