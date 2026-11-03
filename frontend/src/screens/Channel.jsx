import { useCallback, useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import axios from 'axios'

const API = 'http://localhost:8000'

export default function Channel() {
  const { channelId } = useParams()
  const [search] = useSearchParams()
  const viewer = search.get('viewer') === 'recipient' ? 'recipient' : 'seeker'
  const [channel, setChannel] = useState(null)
  const [messages, setMessages] = useState([])
  const [text, setText] = useState('')
  const [sendError, setSendError] = useState(null)
  const [showPay1, setShowPay1] = useState(false)
  const [showPay2, setShowPay2] = useState(false)
  const [paymentComplete, setPaymentComplete] = useState(false)
  const [shareChecked, setShareChecked] = useState(false)
  const [shareDone, setShareDone] = useState(null)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    try {
      const [c, m] = await Promise.all([
        axios.get(`${API}/api/channel/${channelId}?viewer=${viewer}`),
        axios.get(`${API}/api/channel/${channelId}/messages`),
      ])
      setChannel(c.data)
      setMessages(m.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'not found')
    }
  }, [channelId, viewer])

  useEffect(() => {
    load()
    const t = setInterval(load, 3000)
    return () => clearInterval(t)
  }, [load])

  const send = async () => {
    setSendError(null)
    try {
      await axios.post(`${API}/api/channel/${channelId}/message`, { sender: viewer, text })
      setText('')
      load()
    } catch (e) {
      if (e.response?.data?.detail === 'contact_blocked') {
        setSendError(e.response.data.reason || 'Contact details cannot be shared in chat. Use the confirm flow to reveal a verified contact.')
        setText('')
      } else {
        setSendError(e.response?.data?.detail || 'Send failed.')
      }
    }
  }

  const confirmSeeker = async () => {
    const res = await axios.post(`${API}/api/channel/${channelId}/confirm-seeker`)
    setPaymentComplete(true)
    setShowPay2(false)
    setShowPay1(false)
    load()
    return res
  }

  const shareContact = async () => {
    await axios.post(`${API}/api/channel/${channelId}/share-contact`, {
      recipient_contact: 'layla@example.com',
      share_contact: true,
    })
    setShareDone('shared')
    load()
  }

  const keepPrivate = async () => {
    await axios.post(`${API}/api/channel/${channelId}/share-contact`, {
      recipient_contact: null,
      share_contact: false,
    })
    setShareDone('private')
    load()
  }

  if (error) return <div style={{ padding: 40 }}><h2>Channel unavailable</h2><p>{error}</p></div>
  if (!channel) return <div style={{ padding: 40 }}>Loading...</div>

  return (
    <div style={{ maxWidth: 640, margin: '40px auto', padding: 24 }}>
      <h1 style={{ color: '#000000' }}>Secure channel</h1>
      <p style={{ fontSize: 13, color: '#333' }}>
        {channel.seeker_handle} ↔ {channel.recipient_handle}
      </p>

      {viewer === 'seeker' && !paymentComplete && (
        <button onClick={() => setShowPay1(true)} style={{ padding: '12px 24px', marginTop: 12 }}>
          I confirm this is the person I was looking for
        </button>
      )}

      {viewer === 'seeker' && paymentComplete && (
        <div style={{ marginTop: 16, padding: 16, background: '#e8f5e9', borderRadius: 4 }}>
          {channel.recipient_contact ? (
            <p style={{ margin: 0, fontSize: 15, color: '#000000' }}>Connection confirmed. Recipient contact: <strong style={{ color: '#000000' }}>{channel.recipient_contact}</strong></p>
          ) : (
            <div>
              <p style={{ margin: 0, fontSize: 15, color: '#000000' }}>Connection confirmed. The recipient has not shared a contact yet.</p>
              <p style={{ margin: '8px 0 0', fontSize: 15, color: '#000000' }}>You can still message them here. If they choose to share, you&apos;ll see it below.</p>
            </div>
          )}
          <div style={{ marginTop: 12 }}>
            <p style={{ margin: '0 0 8px', fontSize: 14, fontWeight: 700, color: '#000000' }}>Continue on</p>
            <p style={{ margin: 0, fontSize: 14, color: '#333' }}>WhatsApp · Messenger · Instagram</p>
          </div>
        </div>
      )}

      {viewer === 'recipient' && channel.seeker_confirmed && !channel.contact_revealed && shareDone !== 'private' && shareDone !== 'shared' && (
        <div style={{ marginTop: 16, padding: 16, background: '#fff8e1', borderLeft: '4px solid #f9a825', borderRadius: 4 }}>
          <p style={{ margin: 0, fontSize: 15, color: '#000000' }}>The seeker has paid the connection fee and confirmed they are looking for you. Share your contact?</p>
          <label style={{ display: 'block', marginTop: 12, fontSize: 15, color: '#000000' }}>
            <input
              type="checkbox"
              checked={shareChecked}
              onChange={e => setShareChecked(e.target.checked)}
              style={{ marginRight: 8 }}
            />
            Share my WhatsApp number
          </label>
          <p style={{ margin: '4px 0 0 26px', fontSize: 15, color: '#000000' }}>+234 ••• ••• 4471 (from your Meta account)</p>
          <div style={{ display: 'flex', gap: 12, marginTop: 12 }}>
            <button onClick={shareContact} style={{ padding: '8px 16px' }}>Share contact</button>
            <button onClick={keepPrivate} style={{ padding: '8px 16px' }}>Keep private</button>
          </div>
        </div>
      )}

      {showPay1 && (
        <div style={{ marginTop: 16, padding: 16, border: '1px solid #ddd', borderRadius: 4, background: '#ffffff' }}>
          <p style={{ margin: 0, fontWeight: 700, fontSize: 15, color: '#000000' }}>Confirm connection</p>
          <p style={{ fontSize: 15, color: '#000000' }}>To reveal this person&apos;s contact and continue the conversation outside Reunite, a one-time connection fee of $5.99 applies.</p>
          <div style={{ display: 'flex', gap: 12 }}>
            <button onClick={() => { setShowPay1(false); setShowPay2(true) }} style={{ padding: '8px 16px' }}>Continue — $5.99</button>
            <button onClick={() => setShowPay1(false)} style={{ padding: '8px 16px' }}>Cancel</button>
          </div>
        </div>
      )}

      {showPay2 && (
        <div style={{ marginTop: 16, padding: 16, border: '1px solid #ddd', borderRadius: 4, background: '#ffffff' }}>
          <p style={{ margin: 0, fontWeight: 700, fontSize: 15, color: '#000000' }}>Payment coming soon</p>
          <p style={{ fontSize: 15, color: '#333' }}>In production, this is where Stripe or Meta Pay would process the $5.99 payment. For the hackathon demo, this step is simulated.</p>
          <div style={{ display: 'flex', gap: 12 }}>
            <button onClick={confirmSeeker} style={{ padding: '8px 16px' }}>Simulate payment success</button>
            <button onClick={() => setShowPay2(false)} style={{ padding: '8px 16px' }}>Cancel</button>
          </div>
        </div>
      )}

      <h3 style={{ marginTop: 24, color: '#000000' }}>Messages</h3>
      <div>
        {messages.map((m, i) => {
          const isSeeker = m.sender === 'seeker'
          return (
            <div key={i} style={{ marginTop: 8, display: 'flex', justifyContent: isSeeker ? 'flex-start' : 'flex-end' }}>
              <div style={{ maxWidth: '80%' }}>
                <span style={{ fontSize: 13, fontWeight: 700, color: isSeeker ? '#1565c0' : '#2e7d32' }}>
                  {isSeeker ? 'Seeker' : 'Recipient'}
                </span>
                <p style={{ margin: '4px 0', color: '#000000', background: '#f5f5f5', border: '1px solid #e0e0e0', fontSize: 15, padding: '8px 12px', borderRadius: 4 }}>
                  {m.text}
                </p>
              </div>
            </div>
          )
        })}
      </div>

      <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
        <input
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="Write a message"
          disabled={viewer === 'seeker' && !paymentComplete}
          style={{ flex: 1, padding: 12, color: '#000000', background: '#ffffff', fontSize: 15 }}
        />
        <button onClick={send} disabled={viewer === 'seeker' && !paymentComplete} style={{ padding: '12px 24px' }}>Send</button>
      </div>
      {viewer === 'seeker' && !paymentComplete && (
        <p style={{ fontSize: 13, color: '#333', marginTop: 8 }}>Pay the $5.99 connection fee to send messages.</p>
      )}
      {sendError && (
        <p style={{ color: '#b00020', fontSize: 15, marginTop: 8 }}>⚠ {sendError}</p>
      )}
    </div>
  )
}
