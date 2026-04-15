import './RiskBadge.css'

const RISK_CONFIG = {
  CRITICAL:     { dot: true, pulse: true },
  HIGH:         { dot: true, pulse: false },
  MODERATE:     { dot: true, pulse: false },
  LOW:          { dot: true, pulse: false },
  INCONCLUSIVE: { dot: true, pulse: false },
}

export default function RiskBadge({ level }) {
  const key = (level || 'INCONCLUSIVE').toUpperCase()
  const config = RISK_CONFIG[key] || RISK_CONFIG.INCONCLUSIVE

  return (
    <span className={`risk-pill risk-${key.toLowerCase()}`}>
      <span className={`risk-dot ${config.pulse ? 'pulse' : ''}`} />
      {key}
    </span>
  )
}
