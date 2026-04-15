import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import './Upload.css'

const FILE_TYPES = [
  {
    id: 'report_file',
    icon: '📄',
    title: 'Patient Report',
    description: 'Upload PDF or image containing blood work and vitals.',
    accept: '.pdf,.png,.jpg,.jpeg',
  },
  {
    id: 'ecg_file',
    icon: '❤️',
    title: 'ECG Rhythm',
    description: 'Upload the 12-lead Electrocardiogram image.',
    accept: '.png,.jpg,.jpeg,.dicom',
  },
  {
    id: 'echo_file',
    icon: '🫀',
    title: 'Echo / Cardiac Ultrasound',
    description: 'Upload echocardiogram video (MP4, AVI) or DICOM.',
    accept: '.mp4,.avi,.dicom,.dcm,.png,.jpg',
  },
]

export default function Upload() {
  const navigate = useNavigate()
  const [files, setFiles] = useState({})
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const inputRefs = useRef({})

  function handleFile(id, e) {
    const file = e.target.files[0]
    if (file) {
      setFiles(prev => ({ ...prev, [id]: file }))
    }
  }

  function handleDrop(id, e) {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) {
      setFiles(prev => ({ ...prev, [id]: file }))
    }
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setUploading(true)
    setError(null)

    try {
      const formData = new FormData()
      Object.entries(files).forEach(([key, file]) => {
        formData.append(key, file)
      })

      const res = await fetch('/upload/', {
        method: 'POST',
        body: formData,
      })

      const data = await res.json()

      if (data.status === 'ok' && data.patient_id) {
        navigate(`/processing/${data.patient_id}`)
      } else {
        setError(data.error || 'Upload failed')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  const hasFiles = Object.keys(files).length > 0

  return (
    <div className="upload-page">
      <div className="upload-header">
        <h1>AI Triaging Extraction</h1>
        <p>
          Upload patient files. Gemini 2.5 Flash will automatically extract vitals
          and biomarkers, then trigger ECG and X-Ray agents concurrently.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="upload-form">
        <div className="upload-grid">
          {FILE_TYPES.map((ft, idx) => {
            const file = files[ft.id]
            return (
              <div
                key={ft.id}
                className={`upload-card card ${file ? 'has-file' : ''}`}
                style={{ animationDelay: `${idx * 0.1}s` }}
                onDragOver={e => e.preventDefault()}
                onDrop={e => handleDrop(ft.id, e)}
                onClick={() => inputRefs.current[ft.id]?.click()}
              >
                <div className="upload-card-icon">{ft.icon}</div>
                <h3>{idx + 1}. {ft.title}</h3>
                <p>{ft.description}</p>
                {file ? (
                  <div className="file-selected">
                    <span className="file-check">✓</span>
                    <span className="file-name">{file.name.length > 25 ? file.name.slice(0, 22) + '...' : file.name}</span>
                  </div>
                ) : (
                  <div className="file-prompt">Click or drag to upload</div>
                )}
                <input
                  type="file"
                  id={ft.id}
                  name={ft.id}
                  accept={ft.accept}
                  ref={el => inputRefs.current[ft.id] = el}
                  onChange={e => handleFile(ft.id, e)}
                  className="file-input-hidden"
                />
              </div>
            )
          })}
        </div>

        {error && (
          <div className="upload-error">
            <span>⚠️</span> {error}
          </div>
        )}

        <button
          type="submit"
          className={`submit-btn btn btn-primary btn-lg ${!hasFiles ? 'disabled' : ''}`}
          disabled={!hasFiles || uploading}
        >
          {uploading ? (
            <>
              <span className="btn-spinner" />
              Processing...
            </>
          ) : (
            'Extract & Analyze Patient →'
          )}
        </button>
      </form>
    </div>
  )
}
