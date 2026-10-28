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
  const [answer, setAnswer] = useState('')
  const [verified, setVerified] = useState(false)
  const [verifyError, setVerifyError] = useState(null)
  const [fails, setFails] = useState(0)

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

  const submitAnswer = async () => {
    try {
      await axios.post(`${API}/api/respond/${token}/verify-answer`, { answer })
      setVerified(true)
      setVerifyError(null)
    } catch (e) {
      const status = e.response?.status
      if (status === 403) {
        const nextFails = fails + 1
        setFails(nextFails)
        const left = 3 - nextFails
        setVerifyError(left > 0 ? `Incorrect. ${left} attempt${left === 1 ? '' : 's'} left.` : 'Incorrect.')
      } else {
        setError(e.response?.data?.detail || 'locked')
      }
    }
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

      {!verified ? (
        <div style={{ marginTop: 16 }}>
          <h3>Confirm this request is for you</h3>
          <p>To confirm this request is for you, enter the last two digits of a phone number you have used.</p>
          <input
            value={answer}
            onChange={e => setAnswer(e.target.value)}
            placeholder="Last two digits"
            maxLength={8}
            style={{ padding: 8, marginRight: 8 }}
          />
          <button onClick={submitAnswer} style={{ padding: '8px 16px' }}>Verify</button>
          {verifyError && <p style={{ color: '#c62828' }}>{verifyError}</p>}
        </div>
      ) : (
        <p style={{ marginTop: 16, color: '#2e7d32' }}><strong>Identity confirmed.</strong></p>
      )}

      <h3>Optional: verify your identity</h3>
      <input type="file" accept="image/*" onChange={upload} />
      {redactedUrl && (
        <div style={{ marginTop: 16 }}>
          <p style={{ fontSize: 12, color: '#999' }}>Redacted preview (only you and the seeker see this — never the original):</p>
          <img src={redactedUrl} alt="redacted" style={{ maxWidth: 300, border: '1px solid #ddd' }} />
        </div>
      )}

      {!result ? (
        verified ? (
          <div style={{ marginTop: 24, display: 'flex', gap: 12 }}>
            <button onClick={accept} style={{ padding: '12px 24px', background: '#2e7d32', color: 'white', border: 0 }}>
              Accept and connect
            </button>
            <button onClick={decline} style={{ padding: '12px 24px', background: '#c62828', color: 'white', border: 0 }}>
              Decline
            </button>
          </div>
        ) : (
          <p style={{ marginTop: 24, color: '#555' }}>Answer the confirmation question above to unlock Accept and Decline.</p>
        )
      ) : (
        <p style={{ marginTop: 24 }}><strong>{result === 'accepted' ? 'Consent given. A secure channel is open.' : 'Request closed.'}</strong></p>
      )}
    </div>
  )
}