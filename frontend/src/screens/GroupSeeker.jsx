import { useState } from 'react'
import axios from 'axios'

const API = 'http://localhost:8000'

const EMPTY_QUIZ = Array.from({ length: 5 }, () => ({ q: '', a: '' }))

export default function GroupSeeker() {
  const [rawText, setRawText] = useState('')
  const [context, setContext] = useState('')
  const [namesText, setNamesText] = useState('')
  const [quiz, setQuiz] = useState(EMPTY_QUIZ)
  const [photo, setPhoto] = useState(null)
  const [phoneSuffix, setPhoneSuffix] = useState('')
  const [birthYear, setBirthYear] = useState('')
  const [contact, setContact] = useState('')
  const [groupId, setGroupId] = useState(null)
  const [groupStatus, setGroupStatus] = useState(null)
  const [error, setError] = useState(null)

  const setQuizField = (index, field, value) => {
    setQuiz(prev => prev.map((item, i) => i === index ? { ...item, [field]: value } : item))
  }

  const submit = async () => {
    setError(null)
    const names = namesText.split('\n').map(n => n.trim()).filter(Boolean)
    const form = new FormData()
    form.append('raw_text', rawText)
    form.append('context', context)
    form.append('names', JSON.stringify(names))
    form.append('quiz', JSON.stringify(quiz))
    if (photo) form.append('photo', photo)
    if (phoneSuffix.trim()) form.append('phone_suffix', phoneSuffix.trim())
    if (birthYear.trim()) form.append('birth_year', birthYear.trim())
    if (contact.trim()) form.append('contact', contact.trim())
    try {
      const res = await axios.post(`${API}/api/submit-group`, form)
      setGroupId(res.data.group_request_id)
      try {
        await axios.post(`${API}/api/match-group/${res.data.group_request_id}`)
      } catch {
        // Silent auto-match: user only sees the filed confirmation.
      }
    } catch (e) {
      setError(e.response?.data?.detail || 'submit failed')
    }
  }

  const checkGroupStatus = async () => {
    const res = await axios.get(`${API}/api/group-status/${groupId}`)
    setGroupStatus(res.data)
  }

  return (
    <div style={{ maxWidth: 640, margin: '40px auto', padding: 24 }}>
      <h1>Group request</h1>
      <p style={{ color: '#555' }}>
        File a group photo search. Your data is encrypted and never publicly visible.
      </p>

      {!groupId ? (
        <>
          <label>Notes about this group</label>
          <textarea
            rows={3}
            style={{ width: '100%', marginTop: 8, padding: 12 }}
            value={rawText}
            onChange={e => setRawText(e.target.value)}
            placeholder="Class photo search..."
          />

          <label style={{ display: 'block', marginTop: 16 }}>Context</label>
          <input
            style={{ width: '100%', padding: 12 }}
            value={context}
            onChange={e => setContext(e.target.value)}
            placeholder="2005 Methodist High School, Lagos"
          />

          <label style={{ display: 'block', marginTop: 16 }}>Names (one per line)</label>
          <textarea
            rows={4}
            style={{ width: '100%', marginTop: 8, padding: 12 }}
            value={namesText}
            onChange={e => setNamesText(e.target.value)}
            placeholder={'Chidi\nNgozi\nEmeka'}
          />

          <h3 style={{ marginTop: 24 }}>Verification quiz (5 questions)</h3>
          <p style={{ color: '#555', fontSize: 14 }}>
            Recipients must answer at least 4 of these correctly.
          </p>
          {quiz.map((item, i) => (
            <div key={i} style={{ marginTop: 12 }}>
              <label style={{ display: 'block', fontWeight: 700, fontSize: 15 }}>
                {i + 1}. Question
              </label>
              <input
                style={{ width: '100%', padding: 8, marginTop: 4 }}
                value={item.q}
                onChange={e => setQuizField(i, 'q', e.target.value)}
                placeholder={`Question ${i + 1}`}
              />
              <label style={{ display: 'block', marginTop: 8, fontSize: 14 }}>
                Answer {i + 1}
              </label>
              <input
                style={{ width: '100%', padding: 8, marginTop: 4 }}
                value={item.a}
                onChange={e => setQuizField(i, 'a', e.target.value)}
                placeholder={`Answer ${i + 1}`}
              />
            </div>
          ))}

          <label style={{ display: 'block', marginTop: 16 }}>Group photo (optional)</label>
          <input
            type="file"
            accept="image/*"
            onChange={e => setPhoto(e.target.files[0] || null)}
          />

          <label style={{ display: 'block', marginTop: 16 }}>Phone suffix hint (optional)</label>
          <input
            style={{ width: '100%', padding: 12 }}
            value={phoneSuffix}
            onChange={e => setPhoneSuffix(e.target.value)}
            placeholder="4471"
          />

          <label style={{ display: 'block', marginTop: 16 }}>Class year (optional)</label>
          <input
            style={{ width: '100%', padding: 12 }}
            value={birthYear}
            onChange={e => setBirthYear(e.target.value)}
            placeholder="2005"
          />

          <label style={{ display: 'block', marginTop: 16 }}>Your contact (encrypted, optional)</label>
          <input
            style={{ width: '100%', padding: 12 }}
            value={contact}
            onChange={e => setContact(e.target.value)}
            placeholder="phone or email"
          />

          {error && <p style={{ color: '#c62828' }}>{error}</p>}

          <button onClick={submit} style={{ marginTop: 24, padding: '12px 24px' }}>
            File group request
          </button>
        </>
      ) : (
        <div style={{ marginTop: 24, background: '#ffffff' }}>
          <p style={{ color: '#000000', fontSize: 15 }}>Your group request has been filed.</p>
          <p style={{ color: '#000000', fontSize: 15, background: '#f5f5f5', padding: 10, fontFamily: 'monospace', fontWeight: 700, wordBreak: 'break-all' }}>Group request ID: {groupId}</p>
          <p style={{ color: '#000000', fontSize: 15 }}>You will be notified if any group member accepts the request. Do not share this ID publicly.</p>
          <button onClick={checkGroupStatus} style={{ padding: '8px 16px' }}>Refresh status</button>
          {groupStatus && (
            <p style={{ color: '#000000', fontSize: 15, marginTop: 12 }}>
              Confirmed: {groupStatus.confirmed} · Pending: {groupStatus.pending} · Declined: {groupStatus.declined}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
