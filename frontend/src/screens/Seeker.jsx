import { useState } from 'react'
import axios from 'axios'

const API = 'http://localhost:8000'

export default function Seeker() {
  const [rawText, setRawText] = useState('')
  const [contact, setContact] = useState('')
  const [relationship, setRelationship] = useState('')
  const [requestId, setRequestId] = useState(null)
  const [status, setStatus] = useState(null)

  const submit = async () => {
    const res = await axios.post(`${API}/api/submit`, {
      raw_text: rawText,
      contact,
      relationship: relationship || null,
    })
    setRequestId(res.data.request_id)
    setStatus('filed')
  }

  const refresh = async () => {
    const res = await axios.get(`${API}/api/status/${requestId}`)
    setStatus(res.data.status)
  }

  return (
    <div style={{ maxWidth: 640, margin: '40px auto', padding: 24 }}>
      <h1>Reunite</h1>
      <p style={{ color: '#555' }}>
        Your data is encrypted and never publicly visible. You will only hear back if they consent.
      </p>

      {!requestId ? (
        <>
          <label>Describe who you are looking for</label>
          <textarea
            rows={5}
            style={{ width: '100%', marginTop: 8, padding: 12 }}
            value={rawText}
            onChange={e => setRawText(e.target.value)}
            placeholder="My sister Layla, we lived near the old market in Mosul, her phone ended in 4471, born around 1988..."
          />

          <label style={{ display: 'block', marginTop: 16 }}>Relationship (optional)</label>
          <select value={relationship} onChange={e => setRelationship(e.target.value)} style={{ padding: 8 }}>
            <option value="">—</option>
            <option value="sibling">Sibling</option>
            <option value="parent">Parent</option>
            <option value="child">Child</option>
            <option value="spouse">Spouse</option>
            <option value="friend">Friend</option>
          </select>

          <label style={{ display: 'block', marginTop: 16 }}>Your contact (encrypted)</label>
          <input
            style={{ width: '100%', padding: 12 }}
            value={contact}
            onChange={e => setContact(e.target.value)}
            placeholder="phone or email"
          />

          <button onClick={submit} style={{ marginTop: 24, padding: '12px 24px' }}>
            File confidential request
          </button>
        </>
      ) : (
        <div style={{ marginTop: 24 }}>
          <p><strong>Application filed.</strong> Your request is encrypted. The person being sought will receive a private notification. If they decline, you will not be told — that is how we protect them.</p>
          <p style={{ fontSize: 12, color: '#999' }}>Request ID: {requestId}</p>
          <button onClick={refresh} style={{ padding: '8px 16px' }}>Refresh status</button>
          <p style={{ marginTop: 16 }}>Status: <strong>{status}</strong></p>
        </div>
      )}
    </div>
  )
}