import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import axios from 'axios'

const API = 'http://localhost:8000'

export default function Respond() {
  const { token } = useParams()
  const [summary, setSummary] = useState(null)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [redactedUrl, setRedactedUrl] = useState(null)

  useEffect(() => {
    axios.get(`${API}/api/respond/${token}`)
      .then(r => setSummary(r.data))
      .catch(e => setError(e.response?.data?.detail || 'not found'))
  }, [token])

  const upload = async (e) => {
    const file = e.target.files[0]
    const form = new FormData()
    form.append('file', file)
    const res = await axios.post(`${API}/api/respond/${token}/verify`, form)
    setRedactedUrl(`${API}${res.data.redacted_url}`)
  }

  const accept = async () => {
    await axios.post(`${API}/api/respond/${token}/accept`)
    setResult('accepted')
  }

  const decline = async () => {
    await axios.post(`${API}/api/respond/${token}/decline`)
    setResult('declined')
  }

  if (error) return <div style={{ padding: 40 }}><h2>Request unavailable</h2><p>{error}</p></div>
  if (!summary) return <div style={{ padding: 40 }}>Loading...</div>

  return (
    <div style={{ maxWidth: 640, margin: '40px auto', padding: 24 }}>
      <h1>Someone has initiated a family reconnection request</h1>
      <p style={{ background: '#f5f5f5', padding: 16, borderRadius: 8 }}>{summary.redacted_summary}</p>

      <h3>Optional: verify your identity</h3>
      <input type="file" accept="image/*" onChange={upload} />
      {redactedUrl && (
        <div style={{ marginTop: 16 }}>
          <p style={{ fontSize: 12, color: '#999' }}>Redacted preview (only you and the seeker see this — never the original):</p>
          <img src={redactedUrl} alt="redacted" style={{ maxWidth: 300, border: '1px solid #ddd' }} />
        </div>
      )}

      {!result ? (
        <div style={{ marginTop: 24, display: 'flex', gap: 12 }}>
          <button onClick={accept} style={{ padding: '12px 24px', background: '#2e7d32', color: 'white', border: 0 }}>
            Accept and connect
          </button>
          <button onClick={decline} style={{ padding: '12px 24px', background: '#c62828', color: 'white', border: 0 }}>
            Decline
          </button>
        </div>
      ) : (
        <p style={{ marginTop: 24 }}><strong>{result === 'accepted' ? 'Consent given. A secure channel is open.' : 'Request closed.'}</strong></p>
      )}
    </div>
  )
}