import './DonutChart.css'

const COLORS = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MODERATE: '#eab308',
  LOW: '#22c55e',
  INCONCLUSIVE: '#94a3b8',
}

const LABELS = {
  CRITICAL: 'Critical',
  HIGH: 'High',
  MODERATE: 'Moderate',
  LOW: 'Low',
  INCONCLUSIVE: 'Inconclusive',
}

export default function DonutChart({ distribution }) {
  const total = Object.values(distribution).reduce((a, b) => a + b, 0)

  if (total === 0) {
    return (
      <div className="donut-empty">
        <p>No data yet</p>
      </div>
    )
  }

  const radius = 40
  const circumference = 2 * Math.PI * radius
  let offset = 0

  const segments = Object.entries(distribution)
    .filter(([, count]) => count > 0)
    .map(([level, count]) => {
      const pct = count / total
      const dashLen = circumference * pct
      const seg = { level, count, color: COLORS[level], dashLen, offset }
      offset += dashLen
      return seg
    })

  return (
    <div className="donut-wrapper">
      <div className="donut-chart">
        <svg viewBox="0 0 100 100">
          {segments.map((s, i) => (
            <circle
              key={i}
              cx="50" cy="50" r={radius}
              stroke={s.color}
              fill="none"
              strokeWidth="7"
              strokeDasharray={`${s.dashLen} ${circumference - s.dashLen}`}
              strokeDashoffset={-s.offset + s.dashLen}
              strokeLinecap="round"
              style={{ transition: 'stroke-dashoffset 1s ease' }}
            />
          ))}
        </svg>
        <div className="donut-center">
          <div className="donut-total">{total}</div>
          <div className="donut-label">Total</div>
        </div>
      </div>
      <div className="donut-legend">
        {Object.entries(distribution)
          .filter(([, c]) => c > 0)
          .map(([level, count]) => (
            <div className="legend-item" key={level}>
              <div className="legend-left">
                <span className="legend-dot" style={{ background: COLORS[level] }} />
                <span className="legend-name">{LABELS[level]}</span>
              </div>
              <span className="legend-count">{count}</span>
            </div>
          ))}
      </div>
    </div>
  )
}
