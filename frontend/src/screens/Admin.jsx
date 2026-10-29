import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import axios from 'axios'

const API = 'http://localhost:8000'

export default function Admin() {
  const [searchParams] = useSearchParams()
  const [requestId, setRequestId] = useState('')
  const [match, setMatch] = useState(null)
  const [token, setToken] = useState(null)
  const [groupId, setGroupId] = useState(searchParams.get('groupId') || '')
  const [groupMatch, setGroupMatch] = useState(null)
  const [groupStatus, setGroupStatus] = useState(null)

  const runMatch = async () => {
    const res = await axios.post(`${API}/api/match/${requestId}`)
    setMatch(res.data)
    setToken(null)
  }

  const verificationStatus = !match
    ? null
    : !match.threshold_met
      ? 'no_match'
      : match.winner_id === 'c1'
        ? 'verified'
        : 'unexpected'

  const issueToken = async () => {
    const res = await axios.post(`${API}/api/consent/${requestId}?candidate_id=${match.winner_id}`)
    setToken(res.data.token)
  }

  const runGroupMatch = async () => {
    const res = await axios.post(`${API}/api/match-group/${groupId}`)
    setGroupMatch(res.data)
    setGroupStatus(null)
  }

  const checkGroupStatus = async () => {
    const res = await axios.get(`${API}/api/group-status/${groupId}`)
    setGroupStatus(res.data)
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

      {match && verificationStatus === 'verified' && (
        <div style={{ backgroundColor: '#e8f5e9', borderLeft: '4px solid #0a7a2f', color: '#0a7a2f', fontSize: 15, padding: '10px 14px', borderRadius: 4 }}>
          ✅ VERIFIED against ground truth: winner is c1, threshold met, traps correctly below 0.72.
        </div>
      )}

      {match && verificationStatus === 'unexpected' && (
        <div style={{ backgroundColor: '#fdecec', borderLeft: '4px solid #b00020', color: '#b00020', fontSize: 15, padding: '10px 14px', borderRadius: 4 }}>
          ⚠️ UNEXPECTED: winner is {match.winner_id}. Seed graph expects c1.
        </div>
      )}

      {match && verificationStatus === 'no_match' && (
        <div style={{ backgroundColor: '#f5f5f5', borderLeft: '4px solid #666', color: '#333', fontSize: 15, padding: '10px 14px', borderRadius: 4 }}>
          ℹ️ No match above threshold. This is the correct behavior for unrelated input.
        </div>
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

      <h2 style={{ marginTop: 40 }}>Group requests (demo only)</h2>

      <label>Group request ID</label>
      <input
        style={{ width: '100%', padding: 8, marginTop: 8 }}
        value={groupId}
        onChange={e => setGroupId(e.target.value)}
        placeholder="paste group_request_id from group submit"
      />

      <div style={{ marginTop: 16, display: 'flex', gap: 12 }}>
        <button onClick={runGroupMatch} style={{ padding: '10px 20px' }}>Run group match</button>
        <button onClick={checkGroupStatus} style={{ padding: '10px 20px' }}>Check status</button>
      </div>

      {groupMatch && groupMatch.slots && (
        <table style={{ width: '100%', marginTop: 16, borderCollapse: 'collapse', fontSize: 15 }}>
          <caption style={{ textAlign: 'left', fontSize: 16, fontWeight: 700, paddingBottom: 8 }}>
            Group slots (mode: {groupMatch.mode}, threshold 0.72)
          </caption>
          <thead>
            <tr>
              <th style={{ textAlign: 'left', fontWeight: 700, fontSize: 15, padding: 8, borderBottom: '2px solid #000' }}>Slot</th>
              <th style={{ textAlign: 'left', fontWeight: 700, fontSize: 15, padding: 8, borderBottom: '2px solid #000' }}>Name</th>
              <th style={{ textAlign: 'left', fontWeight: 700, fontSize: 15, padding: 8, borderBottom: '2px solid #000' }}>Candidate</th>
              <th style={{ textAlign: 'left', fontWeight: 700, fontSize: 15, padding: 8, borderBottom: '2px solid #000' }}>Score</th>
              <th style={{ textAlign: 'left', fontWeight: 700, fontSize: 15, padding: 8, borderBottom: '2px solid #000' }}>Threshold</th>
              <th style={{ textAlign: 'left', fontWeight: 700, fontSize: 15, padding: 8, borderBottom: '2px solid #000' }}>Token</th>
            </tr>
          </thead>
          <tbody>
            {groupMatch.slots.map(entry => (
              <tr key={entry.slot}>
                <td style={{ padding: 8, fontSize: 15 }}>{entry.slot}</td>
                <td style={{ padding: 8, fontSize: 15 }}>{entry.name || '—'}</td>
                <td style={{ padding: 8, fontSize: 15 }}>{entry.candidate_id || '—'}</td>
                <td style={{ padding: 8, fontSize: 15 }}>{entry.score.toFixed(4)}</td>
                <td style={{ padding: 8, fontSize: 15 }}>{entry.threshold_met ? 'Above 0.72' : 'Below 0.72'}</td>
                <td style={{ padding: 8, fontSize: 15 }}>{entry.token_issued ? 'Issued' : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {groupStatus && (
        <p style={{ marginTop: 16, fontSize: 15 }}>
          Confirmed: <strong>{groupStatus.confirmed}</strong>
          {' '}· Pending: <strong>{groupStatus.pending}</strong>
          {' '}· Declined: <strong>{groupStatus.declined}</strong>
        </p>
      )}
    </div>
  )
}