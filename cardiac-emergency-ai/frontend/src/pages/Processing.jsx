import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { runPipeline } from '../services/api'
import './Processing.css'

const STEPS = [
  { icon: '📄', label: 'Extracting Vitals (Gemini 2.5 Flash)' },
  { icon: '🤖', label: 'Running specialized models concurrently' },
  { icon: '🧠', label: 'Synthesizing Action Plan (LangGraph)' },
]

export default function Processing() {
  const { patientId } = useParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState('running')
  const [error, setError] = useState(null)
  const [activeStep, setActiveStep] = useState(0)

  // Animate steps
  useEffect(() => {
    const timers = [
      setTimeout(() => setActiveStep(1), 3000),
      setTimeout(() => setActiveStep(2), 8000),
    ]
    return () => timers.forEach(clearTimeout)
  }, [])

  // Run pipeline
  useEffect(() => {
    let mounted = true
    async function process() {
      try {
        const res = await runPipeline(patientId)
        if (!mounted) return
        if (res.status === 'complete') {
          setStatus('complete')
          setTimeout(() => navigate(`/report/${res.report_id}`), 1000)
        } else {
          setStatus('failed')
          setError(res.error || 'Processing failed')
        }
      } catch (e) {
        if (!mounted) return
        setStatus('failed')
        setError(e.message)
      }
    }
    process()
    return () => { mounted = false }
  }, [patientId, navigate])

  return (
    <div className="processing-page">
      <div className="processing-card card">
        <div className={`proc-ring ${status}`}>
          <div className="proc-ring-inner">
            {status === 'running' && <div className="proc-spinner" />}
            {status === 'complete' && <span className="proc-done">✓</span>}
            {status === 'failed' && <span className="proc-fail">✕</span>}
          </div>
        </div>

        <h2>
          {status === 'running' && 'Analyzing Patient Data'}
          {status === 'complete' && 'Analysis Complete!'}
          {status === 'failed' && 'Processing Failed'}
        </h2>

        {status === 'running' && (
          <p className="proc-subtitle">AI agents are working concurrently to analyze the uploads</p>
        )}

        <div className="proc-steps">
          {STEPS.map((s, i) => (
            <div key={i} className={`proc-step ${i <= activeStep && status === 'running' ? 'active' : ''} ${status === 'complete' ? 'done' : ''}`}>
              <span className="step-icon">{s.icon}</span>
              <span className="step-label">{i + 1}. {s.label}</span>
              {i <= activeStep && status === 'running' && (
                <span className="step-indicator">
                  {i < activeStep ? '✓' : <span className="mini-spinner" />}
                </span>
              )}
              {status === 'complete' && <span className="step-indicator">✓</span>}
            </div>
          ))}
        </div>

        {error && (
          <div className="proc-error">
            <p>{error}</p>
            <button className="btn btn-primary" onClick={() => navigate('/')}>Back to Dashboard</button>
          </div>
        )}
      </div>
    </div>
  )
}
