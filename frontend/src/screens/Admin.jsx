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

      {match && match.ranked && (
        <table style={{ width: '100%', marginTop: 16, borderCollapse: 'collapse', fontSize: 15 }}>
          <caption style={{ textAlign: 'left', fontSize: 16, fontWeight: 700, paddingBottom: 8 }}>
            Ranked candidates (threshold 0.72)
          </caption>
          <thead>
            <tr>
              <th style={{ textAlign: 'left', fontWeight: 700, fontSize: 15, padding: 8, borderBottom: '2px solid #000' }}>Candidate</th>
              <th style={{ textAlign: 'left', fontWeight: 700, fontSize: 15, padding: 8, borderBottom: '2px solid #000' }}>Score</th>
              <th style={{ textAlign: 'left', fontWeight: 700, fontSize: 15, padding: 8, borderBottom: '2px solid #000' }}>Threshold</th>
            </tr>
          </thead>
          <tbody>
            {match.ranked.map(entry => {
              const above = entry.score >= 0.72
              const winner = entry.candidate_id === match.winner_id
              return (
                <tr
                  key={entry.candidate_id}
                  style={{ backgroundColor: above ? '#e6f6ec' : '#fdecec', fontWeight: winner ? 700 : 400 }}
                >
                  <td style={{ padding: 8, fontSize: 15 }}>
                    {entry.candidate_id}{winner ? ' (winner)' : ''}
                  </td>
                  <td style={{ padding: 8, fontSize: 15 }}>{entry.score.toFixed(4)}</td>
                  <td style={{ padding: 8, fontSize: 15, fontWeight: 700, color: above ? '#0a7a2f' : '#b00020' }}>
                    {above ? 'Above 0.72' : 'Below 0.72'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}

      {match && !match.ranked && (
        <p style={{ fontSize: 15 }}>Ranked list not available. Re-run match against the updated backend.</p>
      )}

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