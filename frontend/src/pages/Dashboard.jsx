/**
 * Dashboard Page
 * ===============
 * LEARNING — Custom SVG Animation (the donut wheel):
 *   SVG (Scalable Vector Graphics) lets you draw shapes directly in HTML/JSX.
 *
 *   The animation uses two SVG stroke properties on <circle>:
 *
 *   strokeDasharray="dashLen gapLen"
 *     Turns a circle stroke into a dash. dashLen=0 = invisible, dashLen=C = full circle.
 *
 *   strokeDashoffset="offset"
 *     Rotates where the dash starts. offset=C/4 starts at 12 o'clock.
 *
 *   THE UNROLL ANIMATION:
 *     Start: strokeDasharray="0 C"  (invisible)
 *     End:   strokeDasharray="X C"  (visible segment of length X)
 *     CSS transitions between those two values — that IS the animation.
 *     Each segment gets a delay equal to how far around the circle it lives,
 *     so they draw one after another like a single line going around.
 */
import { useState, useEffect, useRef } from 'react'
import api from '../api/axios'

const COLORS = ['#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316']
const fmt      = (n) => `$${Number(n).toLocaleString('en-US', { minimumFractionDigits: 2 })}`
const fmtShort = (n) => n >= 1000 ? `$${(n / 1000).toFixed(1)}K` : `$${n.toFixed(0)}`

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

// ─── Donut Chart Component ────────────────────────────────────────────────────
function DonutChart({ data, totalSpent, totalBudget }) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 80)
    return () => clearTimeout(t)
  }, [])

  const SIZE           = 240
  const STROKE         = 34
  const R              = (SIZE - STROKE) / 2
  const C              = 2 * Math.PI * R
  const TOTAL_DURATION = 1400

  const total    = data.reduce((s, d) => s + d.value, 0)
  const pctSpent = totalBudget > 0 ? Math.min((totalSpent / totalBudget) * 100, 100) : 0

  // Each segment's arc = its spending as a fraction of the BUDGET, not total spent.
  // This means the gray background track shows through for unspent budget.
  // Falls back to fraction-of-spent when no budget is set.
  const divisor = totalBudget > 0 ? totalBudget : total

  let cumRatio = 0
  const segments = data.map((item) => {
    const ratio      = divisor > 0 ? item.value / divisor : 0
    const startRatio = cumRatio
    cumRatio += ratio
    return {
      ...item,
      ratio,
      startRatio,
      dashLen: ratio * C,
      /**
       * ROTATION APPROACH — cleaner than dashoffset math:
       *   Instead of calculating a complex dashoffset to position each segment,
       *   we rotate each circle so its path starts exactly where the segment begins.
       *
       *   SVG circles start their path at 3 o'clock (0°).
       *   -90° rotates that to 12 o'clock.
       *   +startRatio*360° advances it clockwise to the segment's start position.
       *
       *   So: rotation = startRatio*360 - 90
       *     Segment 1 (startRatio=0):   rotate(-90)   → starts at 12 o'clock ✓
       *     Segment 2 (startRatio=0.4): rotate(54)    → starts 144° past 12 o'clock ✓
       */
      rotateDeg: startRatio * 360 - 90,
    }
  })

  return (
    <div className="donut-wrap">
      <svg width={SIZE} height={SIZE}>
        {/* Grey background track */}
        <circle
          cx={SIZE / 2} cy={SIZE / 2} r={R}
          fill="none"
          stroke="var(--border)"
          strokeWidth={STROKE}
        />

        {total > 0 && segments.map((seg, i) => (
          <circle
            key={i}
            cx={SIZE / 2} cy={SIZE / 2} r={R}
            fill="none"
            stroke={COLORS[i % COLORS.length]}
            strokeWidth={STROKE - 3}
            strokeLinecap="butt"
            strokeDasharray={`${mounted ? seg.dashLen : 0} ${C}`}
            strokeDashoffset={0}
            transform={`rotate(${seg.rotateDeg} ${SIZE / 2} ${SIZE / 2})`}
            style={{
              transition: `stroke-dasharray ${seg.ratio * TOTAL_DURATION}ms cubic-bezier(0.4, 0, 0.2, 1) ${seg.startRatio * TOTAL_DURATION}ms`,
            }}
          />
        ))}
      </svg>

      <div className="donut-center">
        {total === 0 ? (
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>No spending yet</span>
        ) : (
          <>
            <div className="donut-spent">{fmt(totalSpent)}</div>
            <div className="donut-sub">of {fmt(totalBudget)}</div>
            <div
              className="donut-pct"
              style={{ color: pctSpent > 90 ? 'var(--danger)' : pctSpent > 70 ? 'var(--warning)' : 'var(--text-muted)' }}
            >
              {pctSpent.toFixed(0)}% used
            </div>
          </>
        )}
      </div>
    </div>
  )
}

// ─── Line Graph Component ─────────────────────────────────────────────────────
/**
 * LEARNING — Custom SVG Line Graph:
 *   We use a <path> element with a "d" attribute to draw the line.
 *   The "d" string is a series of drawing commands:
 *     M x y   → Move to (x, y) — the starting point
 *     C cx1 cy1 cx2 cy2 x y → Cubic bezier curve to (x, y)
 *       cx1/cy1 = first control point (influences how the curve leaves the start)
 *       cx2/cy2 = second control point (influences how the curve arrives at the end)
 *
 *   SMOOTH CURVE TRICK:
 *     For a smooth S-curve between point A and point B:
 *       cx1 = midX, cy1 = A.y   (leaves A horizontally)
 *       cx2 = midX, cy2 = B.y   (arrives at B horizontally)
 *     This creates a smooth "flow" between points without sharp corners.
 *
 *   The area fill uses the same path, then adds two lines to close it
 *   at the bottom of the chart, forming a filled polygon.
 */
function LineGraph({ monthly, year, onYearChange }) {
  const lineRef = useRef(null)
  const areaRef = useRef(null)

  const PAD   = { top: 16, right: 12, bottom: 30, left: 44 }
  const VW    = 500
  const VH    = 150
  const plotW = VW - PAD.left - PAD.right
  const plotH = VH - PAD.top  - PAD.bottom

  const totals = monthly.map(d => d.total)
  const maxVal = Math.max(...totals, 1) * 1.15

  const px = (i)   => PAD.left + (i / 11) * plotW
  const py = (val) => PAD.top + plotH - (val / maxVal) * plotH

  const points = totals.map((val, i) => [px(i), py(val)])

  const linePath = points.reduce((d, [x, y], i) => {
    if (i === 0) return `M ${x} ${y}`
    const [prevX, prevY] = points[i - 1]
    const midX = (prevX + x) / 2
    return `${d} C ${midX} ${prevY} ${midX} ${y} ${x} ${y}`
  }, '')

  const areaPath = `${linePath} L ${px(11)} ${PAD.top + plotH} L ${px(0)} ${PAD.top + plotH} Z`

  const gridLines = [0, 0.33, 0.66, 1].map(ratio => ({
    y:     py(maxVal * ratio),
    label: fmtShort(maxVal * ratio),
  }))

  const hasData = totals.some(v => v > 0)
  const animKey = totals.join(',')

  // Draw the line left-to-right using stroke-dashoffset animation.
  // Depends on animKey (a string of values) instead of the monthly array reference,
  // so the effect only re-runs when actual data changes — not when a new array
  // object with identical values is passed (e.g. cache hit then same API response).
  useEffect(() => {
    if (!lineRef.current || !hasData) return
    const len = lineRef.current.getTotalLength()
    const el = lineRef.current
    el.style.transition = 'none'
    el.style.strokeDasharray = len
    el.style.strokeDashoffset = len
    // Trigger reflow so the initial state is painted before animating
    el.getBoundingClientRect()
    el.style.transition = 'stroke-dashoffset 1s cubic-bezier(0.4, 0, 0.2, 1)'
    el.style.strokeDashoffset = 0

    // Fade in the area fill slightly after the line starts drawing
    if (areaRef.current) {
      areaRef.current.style.opacity = 0
      setTimeout(() => {
        if (areaRef.current) {
          areaRef.current.style.transition = 'opacity 0.6s ease'
          areaRef.current.style.opacity = 1
        }
      }, 400)
    }
  }, [animKey]) // Re-animate only when values actually change (year switch, etc.)

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.75rem' }}>
        <button className="btn btn-secondary btn-sm" onClick={() => onYearChange(year - 1)}>←</button>
        <span style={{ fontWeight: 600, fontSize: '0.9rem', minWidth: '3rem', textAlign: 'center' }}>{year}</span>
        <button className="btn btn-secondary btn-sm" onClick={() => onYearChange(year + 1)}>→</button>
      </div>

      <svg width="100%" viewBox={`0 0 ${VW} ${VH}`} style={{ overflow: 'visible' }}>
        {gridLines.map(({ y, label }, i) => (
          <g key={i}>
            <line x1={PAD.left} y1={y} x2={VW - PAD.right} y2={y} stroke="var(--border)" strokeWidth="1" />
            <text x={PAD.left - 6} y={y + 4} textAnchor="end" fontSize="10" fill="var(--text-muted)">{label}</text>
          </g>
        ))}

        {hasData && (
          <path ref={areaRef} d={areaPath} fill="var(--primary)" fillOpacity="0.08" style={{ opacity: 0 }} />
        )}

        {hasData && (
          <path
            ref={lineRef}
            d={linePath}
            fill="none"
            stroke="var(--primary)"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        )}

        {points.map(([x, y], i) => totals[i] > 0 && (
          <circle key={i} cx={x} cy={y} r="3.5" fill="var(--primary)"
            style={{ opacity: 0, animation: `fadeUp 0.3s ease ${0.8 + i * 0.04}s both` }}
          />
        ))}

        {MONTHS.map((m, i) => (
          <text key={i} x={px(i)} y={VH - 4} textAnchor="middle" fontSize="10" fill="var(--text-muted)">{m}</text>
        ))}
      </svg>

      {!hasData && (
        <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem', marginTop: '0.5rem' }}>
          No spending recorded in {year}
        </div>
      )}
    </div>
  )
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────
export default function Dashboard() {
  // Read cache synchronously so the very first render already has data (no loading flash)
  const _cached = sessionStorage.getItem('dashboard_cache')
  const _init   = _cached ? JSON.parse(_cached) : null

  const [budget, setBudget]           = useState(_init?.budget   || null)
  const [stats, setStats]             = useState(_init?.stats    || null)
  const [recentTx, setRecentTx]       = useState(_init?.recentTx || [])
  const [budgetInput, setBudgetInput] = useState(_init?.budget?.amount || '')
  const [savingBudget, setSavingBudget] = useState(false)
  const [loading, setLoading]         = useState(!_init)
  const [error, setError]             = useState('')

  const _initYear    = new Date().getFullYear()
  const _graphCached = sessionStorage.getItem(`graph_cache_${_initYear}`)
  const [graphYear, setGraphYear] = useState(_initYear)
  const [graphData, setGraphData] = useState(_graphCached ? JSON.parse(_graphCached) : null)

  useEffect(() => { fetchData() }, [])
  useEffect(() => { fetchGraphData(graphYear) }, [graphYear])

  const fetchData = async () => {
    const hasCached = !!sessionStorage.getItem('dashboard_cache')
    if (!hasCached) setLoading(true)
    try {
      const now = new Date()
      const [budgetRes, statsRes, txRes] = await Promise.all([
        api.get('/budgets/current/'),
        api.get('/transactions/stats/'),
        api.get(`/transactions/?month=${now.getMonth() + 1}&year=${now.getFullYear()}`),
      ])
      setBudget(budgetRes.data)
      setBudgetInput(budgetRes.data.amount || '')
      setStats(statsRes.data)
      setRecentTx(txRes.data.slice(0, 5))
      sessionStorage.setItem('dashboard_cache', JSON.stringify({
        budget: budgetRes.data,
        stats: statsRes.data,
        recentTx: txRes.data.slice(0, 5),
      }))
    } catch {
      if (!hasCached) setError('Failed to load dashboard data.')
    } finally {
      setLoading(false)
    }
  }

  const fetchGraphData = async (year) => {
    const cacheKey = `graph_cache_${year}`
    const cached = sessionStorage.getItem(cacheKey)
    if (cached) setGraphData(JSON.parse(cached))
    try {
      const { data } = await api.get(`/transactions/monthly-stats/?year=${year}`)
      setGraphData(data.monthly)
      sessionStorage.setItem(cacheKey, JSON.stringify(data.monthly))
    } catch {
      // Graph is non-critical — fail silently
    }
  }

  const saveBudget = async (e) => {
    e.preventDefault()
    setSavingBudget(true)
    try {
      const res = await api.post('/budgets/current/', { amount: budgetInput })
      setBudget(res.data)
      sessionStorage.removeItem('dashboard_cache')
      fetchData()
    } catch {
      setError('Failed to save budget.')
    } finally {
      setSavingBudget(false)
    }
  }

  if (loading) return <div className="loading">Loading your dashboard...</div>

  const budgetAmount = parseFloat(budget?.amount || 0)
  const totalSpent   = parseFloat(stats?.total_spent || 0)
  const remaining    = budgetAmount - totalSpent
  const pctSpent     = budgetAmount > 0 ? Math.min((totalSpent / budgetAmount) * 100, 100) : 0

  const chartData = Object.entries(stats?.by_category || {}).map(([name, value]) => ({
    name,
    value: parseFloat(value),
  }))

  const monthLabel = new Date().toLocaleString('default', { month: 'long', year: 'numeric' })

  return (
    <div className="page">
      <h1 className="page-title">Dashboard — {monthLabel}</h1>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Compact budget input */}
      <div className="card" style={{ marginBottom: '1.25rem' }}>
        <form onSubmit={saveBudget} style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-end' }}>
          <div className="form-group" style={{ margin: 0, flex: 1 }}>
            <label htmlFor="budget-input">Monthly budget</label>
            <input
              id="budget-input"
              type="number"
              min="0"
              step="0.01"
              value={budgetInput}
              onChange={e => setBudgetInput(e.target.value)}
              placeholder="e.g. 2000"
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={savingBudget}>
            {savingBudget ? 'Saving...' : 'Save'}
          </button>
        </form>
      </div>

      {/* Main section: chart card (left) + stats column (right) */}
      <div className="dashboard-main">

        {/* Chart card: donut wheel on the left, legend on the right */}
        <div className="card dashboard-chart-card">
          <div className="card-title" style={{ marginBottom: '0' }}>Spending breakdown</div>

          <div className="chart-inner">
            {/* The animated donut wheel */}
            <DonutChart
              data={chartData}
              totalSpent={totalSpent}
              totalBudget={budgetAmount}
            />

            {/*
             * Legend — shown next to the wheel.
             * Each row has a colored dot, the category name, and the amount.
             * This updates automatically as chartData changes (new transactions).
             */}
            <div className="donut-legend">
              {chartData.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem', lineHeight: 1.6 }}>
                  Add transactions to see your spending broken down by category here.
                </div>
              ) : (
                chartData.map((item, i) => (
                  <div key={i} className="donut-legend-item">
                    <span
                      className="donut-legend-dot"
                      style={{ background: COLORS[i % COLORS.length] }}
                    />
                    <span className="donut-legend-name">{item.name}</span>
                    <span className="donut-legend-val">{fmt(item.value)}</span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Line graph sits below the donut + legend, full width of the card */}
          {graphData && (
            <>
              <hr className="divider" />
              <div className="card-title" style={{ marginBottom: '0.5rem' }}>Monthly trend</div>
              <LineGraph
                monthly={graphData}
                year={graphYear}
                onYearChange={setGraphYear}
              />
            </>
          )}
        </div>

        {/* Right column: 3 stats + recent transactions */}
        <div className="dashboard-side">
          <div className="card dashboard-stat">
            <div className="card-title">Budget</div>
            <div className="stat-number" style={{ color: 'var(--primary)' }}>{fmt(budgetAmount)}</div>
            <div className="stat-label">This month's limit</div>
          </div>

          <div className="card dashboard-stat">
            <div className="card-title">Spent</div>
            <div className="stat-number" style={{ color: 'var(--danger)' }}>{fmt(totalSpent)}</div>
            <div className="stat-label">{stats?.transaction_count || 0} transactions</div>
            <div className="progress-bar-container">
              <div
                className="progress-bar-fill"
                style={{
                  width: `${pctSpent}%`,
                  background: pctSpent > 90 ? 'var(--danger)' : pctSpent > 70 ? 'var(--warning)' : 'var(--primary)',
                }}
              />
            </div>
          </div>

          <div className="card dashboard-stat">
            <div className="card-title">Remaining</div>
            <div
              className="stat-number"
              style={{ color: remaining >= 0 ? 'var(--success)' : 'var(--danger)' }}
            >
              {fmt(remaining)}
            </div>
            <div className="stat-label">{(100 - pctSpent).toFixed(0)}% still available</div>
          </div>

          {/* Recent transactions */}
          <div className="card" style={{ flex: 1 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <div className="card-title" style={{ margin: 0 }}>Recent</div>
              <a href="/transactions" style={{ fontSize: '0.8rem', color: 'var(--primary)', textDecoration: 'none' }}>
                View all →
              </a>
            </div>

            {recentTx.length === 0 ? (
              <div className="empty-state" style={{ padding: '1rem 0' }}>
                <p>No transactions this month.</p>
              </div>
            ) : (
              recentTx.map(tx => (
                <div key={tx.id} className="transaction-item">
                  <div>
                    <div className="transaction-title">{tx.title}</div>
                    <div className="transaction-meta">
                      <span className={`badge badge-${tx.category}`}>{tx.category_display}</span>
                      <span>{tx.date}</span>
                    </div>
                  </div>
                  <div className={`transaction-amount ${tx.category === 'income' ? 'amount-income' : 'amount-expense'}`}>
                    {tx.category === 'income' ? '+' : '-'}{fmt(tx.amount)}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

    </div>
  )
}
