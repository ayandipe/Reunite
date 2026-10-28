import { useState } from 'react'
import axios from 'axios'

const API = 'http://localhost:8000'

export default function Admin() {
  const [requestId, setRequestId] = useState('')
  const [match, setMatch] = useState(null)
  const [token, setToken] = useState(null)

  const runMatch = async () => {
    const res = await axios.post(`${API}/api/match/${requestId}`)
    setMatch(res.data)
  }

  const issueToken = async () => {
    const res = await axios.post(`${API}/api/consent/${requestId}?candidate_id=${match.winner_id}`)
    setToken(res.data.token)
  }

  return (
    <div style={{ maxWidth: 800, margin: '40px auto', padding: 24 }}>
      <h1>Admin (demo only)</h1>
      <p style={{ color: '#999', fontSize: 12 }}>Hidden panel. Used to trigger the matching engine live for judges.</p>

      <label>Request ID</label>
      <input
        style={{ width: '100%', padding: 8, marginTop: 8 }}
        value={requestId}
        onChange={e => setRequestId(e.target.value)}
        placeholder="paste request_id from seeker submit"
      />

      <button onClick={runMatch} style={{ marginTop: 16, padding: '10px 20px' }}>Run match</button>

      {match && (
        <pre style={{
          background: '#ffffff',
          color: '#000000',
          padding: 20,
          borderRadius: 8,
          fontSize: 14,
          lineHeight: 1.5,
          fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
          fontWeight: 600,
          overflowX: 'auto',
          border: '2px solid #000000',
        }}>
          {JSON.stringify(match, null, 2)}
        </pre>
      )}

      {match && match.threshold_met && !token && (
        <button onClick={issueToken} style={{ marginTop: 16, padding: '10px 20px' }}>
          Issue consent token
        </button>
      )}

      {token && (
        <div style={{ marginTop: 16 }}>
          <p><strong>Recipient link:</strong></p>
          <code style={{ background: '#f5f5f5', padding: 8, display: 'block' }}>
            http://localhost:5173/respond/{token}
          </code>
        </div>
      )}
    </div>
  )
}