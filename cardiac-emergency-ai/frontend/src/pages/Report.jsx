import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getReportData, confirmReport } from '../services/api'
import RiskBadge from '../components/RiskBadge'
import './Report.css'

export default function Report() {
  const { reportId } = useParams()
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [confirming, setConfirming] = useState(false)

  useEffect(() => {
    async function load() {
      try {
        const data = await getReportData(reportId)
        setReport(data)
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [reportId])

  async function handleConfirm() {
    setConfirming(true)
    try {
      await confirmReport(reportId)
      setReport(prev => ({ ...prev, doctor_confirmed: true }))
    } catch (e) {
      alert('Failed to confirm: ' + e.message)
    } finally {
      setConfirming(false)
    }
  }

  if (loading) {
    return (
      <div className="report-loading">
        <div className="loading-spinner" />
        <p>Loading report...</p>
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="report-error">
        <span>⚠️</span>
        <h3>Failed to load report</h3>
        <p>{error}</p>
        <Link to="/" className="btn btn-primary">Back to Dashboard</Link>
      </div>
    )
  }

  const findings = [
    { 
      icon: '❤️', 
      title: 'ECG Findings', 
      data: report.ecg_findings,
      color: 'var(--accent-pink)',
    },
    { 
      icon: '🧬', 
      title: 'Biomarker Findings', 
      data: report.biomarker_findings,
      color: 'var(--accent-blue)',
    },
    { 
      icon: '🫀', 
      title: 'Imaging Findings', 
      data: report.imaging_findings,
      color: 'var(--accent-green)',
    },
  ]

  return (
    <div className="report-page">
      {/* Header */}
      <div className="report-top">
        <Link to="/" className="back-link">← Dashboard</Link>
        <div className="report-title-row">
          <div>
            <h1>Diagnostic Report</h1>
            <p className="report-patient">
              {report.patient_name} • {report.patient_age || '?'}y • {report.patient_sex || '—'}
            </p>
          </div>
          <RiskBadge level={report.risk_level} />
        </div>
      </div>

      {/* Summary Card */}
      <div className={`summary-card card risk-border-${(report.risk_level || 'inconclusive').toLowerCase()}`}>
        <div className="summary-header">
          <div>
            <h3>Overall Assessment</h3>
            <p className="confidence-text">Confidence: {report.confidence_score}%</p>
          </div>
          {report.processing_time_seconds && (
            <span className="proc-time">⚡ {report.processing_time_seconds}s</span>
          )}
        </div>
        <p className="summary-report">{report.final_report}</p>
      </div>

      {/* Findings Grid */}
      <div className="findings-grid">
        {findings.map((f, i) => {
          const items = f.data?.findings || []
          return (
            <div className="finding-card card" key={i} style={{ animationDelay: `${i * 0.1}s` }}>
              <h4 className="finding-title">
                <span>{f.icon}</span> {f.title}
              </h4>
              {items.length > 0 ? (
                <ul className="finding-list">
                  {items.map((item, j) => (
                    <li key={j}>{item}</li>
                  ))}
                </ul>
              ) : (
                <p className="finding-empty">No findings available</p>
              )}
            </div>
          )
        })}
      </div>

      {/* Recommended Actions */}
      {report.recommended_actions && report.recommended_actions.length > 0 && (
        <div className="actions-card card">
          <h3>🎯 Recommended Actions</h3>
          <div className="actions-list">
            {report.recommended_actions.map((a, i) => (
              <div className="action-item" key={i}>
                <span className="action-num">{i + 1}</span>
                <span>{a}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Doctor Confirm */}
      <div className="confirm-section">
        {report.doctor_confirmed ? (
          <div className="confirmed-badge">
            <span>✔</span> Confirmed by Doctor
          </div>
        ) : (
          <button
            className="btn btn-danger btn-lg confirm-btn"
            onClick={handleConfirm}
            disabled={confirming}
          >
            {confirming ? 'Confirming...' : 'Confirm Report ✓'}
          </button>
        )}
      </div>
    </div>
  )
}
