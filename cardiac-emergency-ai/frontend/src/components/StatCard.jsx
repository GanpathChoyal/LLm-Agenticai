import './StatCard.css'

export default function StatCard({ icon, value, label, variant, suffix = '' }) {
  return (
    <div className={`stat-card stat-${variant}`}>
      <div className="stat-card-icon">{icon}</div>
      <div className="stat-card-value">
        {value}{suffix}
      </div>
      <div className="stat-card-label">{label}</div>
      <div className="stat-card-glow" />
    </div>
  )
}
