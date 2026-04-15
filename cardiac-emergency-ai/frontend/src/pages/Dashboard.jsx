import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import { getDashboardData } from '../services/api'
import StatCard from '../components/StatCard'
import RiskBadge from '../components/RiskBadge'
import DonutChart from '../components/DonutChart'
import './Dashboard.css'

function timeAgo(isoStr) {
  if (!isoStr) return '—'
  const diff = Date.now() - new Date(isoStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

function getGreeting() {
  const h = new Date().getHours()
  if (h < 12) return 'Good Morning'
  if (h < 17) return 'Good Afternoon'
  return 'Good Evening'
}

function getInitials(name) {
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
}

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [riskFilter, setRiskFilter] = useState('ALL')
  const [clock, setClock] = useState(new Date())

  // Fetch dashboard data
  useEffect(() => {
    let mounted = true
    async function load() {
      try {
        const result = await getDashboardData()
        if (mounted) { setData(result); setLoading(false) }
      } catch (e) {
        if (mounted) { setError(e.message); setLoading(false) }
      }
    }
    load()
    const interval = setInterval(load, 30000) // auto-refresh
    return () => { mounted = false; clearInterval(interval) }
  }, [])

  // Live clock
  useEffect(() => {
    const id = setInterval(() => setClock(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  // Filter reports
  const filteredReports = useMemo(() => {
    if (!data) return []
    return data.reports.filter(r => {
      const matchSearch = r.patient_name.toLowerCase().includes(search.toLowerCase())
      const matchRisk = riskFilter === 'ALL' || r.risk_level === riskFilter
      return matchSearch && matchRisk
    })
  }, [data, search, riskFilter])

  if (loading) {
    return (
      <div className="dash-loading">
        <div className="loading-spinner" />
        <p>Loading dashboard...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="dash-error">
        <span className="error-icon">⚠️</span>
        <h3>Failed to load dashboard</h3>
        <p>{error}</p>
        <button className="btn btn-primary" onClick={() => window.location.reload()}>Retry</button>
      </div>
    )
  }

  const { reports, stats, risk_distribution } = data
  const criticals = reports.filter(r => r.risk_level === 'CRITICAL' && !r.doctor_confirmed)
  const clockStr = clock.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
  const dateStr = clock.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
  const filters = ['ALL', 'CRITICAL', 'HIGH', 'MODERATE', 'LOW']

  return (
    <div className="dashboard">
      {/* ── Greeting ── */}
      <section className="dash-greeting">
        <div className="greeting-left">
          <h1>{getGreeting()}, Doctor</h1>
          <p className="greeting-subtitle">Cardiac Emergency AI monitoring • {dateStr}</p>
        </div>
        <div className="greeting-right">
          <div className="live-clock">
            <span className="clock-pulse" />
            {clockStr}
          </div>
          <Link to="/upload" className="btn btn-primary">+ New Patient</Link>
        </div>
      </section>

      {/* ── Stats ── */}
      <section className="stats-grid">
        <StatCard icon="🚨" value={stats.critical_count} label="Critical Alerts" variant="critical" />
        <StatCard icon="📊" value={stats.total_reports} label="Total Reports" variant="total" />
        <StatCard icon="📈" value={stats.avg_confidence} suffix="%" label="Avg Confidence" variant="confidence" />
        <StatCard icon="⚡" value={stats.avg_processing_time} suffix="s" label="Avg Process Time" variant="speed" />
      </section>

      {/* ── Emergency Alerts ── */}
      {criticals.length > 0 && (
        <section className="emergency-section">
          <div className="emergency-header">
            <span className="emergency-dot" />
            <h3>Active Emergency Alerts</h3>
            <span className="emergency-count">{criticals.length}</span>
          </div>
          <div className="emergency-list">
            {criticals.map(r => (
              <div className="alert-card" key={r.id}>
                <div className="alert-top">
                  <div>
                    <h4>{r.patient_name} ({r.patient_age || '?'}y) — CRITICAL</h4>
                    <p className="alert-summary">
                      {r.final_report ? r.final_report.substring(0, 180) + '...' : 'Analysis complete. Requires immediate review.'}
                    </p>
                  </div>
                  <Link to={`/report/${r.id}`} className="btn btn-danger btn-sm">
                    Review →
                  </Link>
                </div>
                <span className="alert-time">{timeAgo(r.created_at)}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ── Bottom Grid: Table + Sidebar ── */}
      <section className="dash-grid">
        {/* Reports Table */}
        <div className="reports-panel card">
          <div className="panel-header">
            <div className="panel-title">
              <span>📋 Recent Reports</span>
              <span className="badge">{filteredReports.length}</span>
            </div>
            <div className="panel-controls">
              <div className="search-box">
                <span>🔍</span>
                <input
                  type="text"
                  placeholder="Search patients..."
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  id="search-reports"
                />
              </div>
              <div className="filter-group">
                {filters.map(f => (
                  <button
                    key={f}
                    className={`filter-chip ${riskFilter === f ? 'active' : ''}`}
                    onClick={() => setRiskFilter(f)}
                  >
                    {f === 'ALL' ? 'All' : f.charAt(0) + f.slice(1).toLowerCase()}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="table-container">
            <table className="reports-table">
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Risk Level</th>
                  <th>Confidence</th>
                  <th>Time</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredReports.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="empty-row">
                      {reports.length === 0
                        ? '🩺 No reports yet. Upload your first patient.'
                        : 'No reports match your criteria.'}
                    </td>
                  </tr>
                ) : (
                  filteredReports.map((r, idx) => {
                    const avatarClass = r.patient_sex === 'M' ? 'av-m' : r.patient_sex === 'F' ? 'av-f' : 'av-d'
                    return (
                      <tr key={r.id} style={{ animationDelay: `${idx * 0.05}s` }}>
                        <td>
                          <div className="patient-cell">
                            <div className={`avatar ${avatarClass}`}>
                              {getInitials(r.patient_name)}
                            </div>
                            <div>
                              <div className="patient-name">{r.patient_name}</div>
                              <div className="patient-meta">{r.patient_age || '?'}y • {r.patient_sex || '—'}</div>
                            </div>
                          </div>
                        </td>
                        <td><RiskBadge level={r.risk_level} /></td>
                        <td>
                          <div className="confidence-cell">
                            <div className="conf-track">
                              <div
                                className={`conf-fill ${r.confidence_score >= 80 ? 'conf-high' : r.confidence_score >= 60 ? 'conf-mid' : 'conf-low'}`}
                                style={{ width: `${r.confidence_score}%` }}
                              />
                            </div>
                            <span className="conf-val">{r.confidence_score}%</span>
                          </div>
                        </td>
                        <td className="time-cell">{timeAgo(r.created_at)}</td>
                        <td>
                          {r.doctor_confirmed
                            ? <span className="status-confirmed">✔ Confirmed</span>
                            : <span className="status-pending">⏳ Pending</span>
                          }
                        </td>
                        <td>
                          <Link to={`/report/${r.id}`} className="view-link">
                            View →
                          </Link>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Sidebar */}
        <aside className="dash-sidebar">
          <div className="sidebar-card card">
            <h4 className="sidebar-title">🎯 Risk Distribution</h4>
            <DonutChart distribution={risk_distribution} />
          </div>

          <div className="sidebar-card card">
            <h4 className="sidebar-title">🤖 Agent Activity</h4>
            <AgentBars reports={reports} />
          </div>

          <div className="sidebar-card card">
            <h4 className="sidebar-title">⚡ Quick Actions</h4>
            <div className="quick-actions">
              <Link to="/upload" className="action-btn" id="qa-upload">
                <span>📄</span> Upload New Patient
              </Link>
              <a href="/admin/" className="action-btn" id="qa-admin">
                <span>⚙️</span> Admin Panel
              </a>
            </div>
          </div>
        </aside>
      </section>
    </div>
  )
}

/* Agent performance mini-component */
function AgentBars({ reports }) {
  const total = reports.length || 1
  const agents = [
    {
      name: 'ECG Agent',
      icon: '❤️',
      pct: Math.round((reports.filter(r => r.ecg_findings && Object.keys(r.ecg_findings).length).length / total) * 100),
      color: 'var(--accent-pink)',
    },
    {
      name: 'Biomarker Agent',
      icon: '🧬',
      pct: Math.round((reports.filter(r => r.biomarker_findings && Object.keys(r.biomarker_findings).length).length / total) * 100),
      color: 'var(--accent-blue)',
    },
    {
      name: 'Imaging Agent',
      icon: '🫀',
      pct: Math.round((reports.filter(r => r.imaging_findings && Object.keys(r.imaging_findings).length).length / total) * 100),
      color: 'var(--accent-green)',
    },
  ]

  return (
    <div className="agent-bars">
      {agents.map(a => (
        <div className="agent-bar-item" key={a.name}>
          <div className="agent-bar-header">
            <span>{a.icon} {a.name}</span>
            <span className="agent-pct">{a.pct}%</span>
          </div>
          <div className="agent-track">
            <div className="agent-fill" style={{ width: `${a.pct}%`, background: a.color }} />
          </div>
        </div>
      ))}
    </div>
  )
}
