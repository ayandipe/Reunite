import { useEffect, useState } from 'react'
import axios from 'axios'
import './App.css'

export default function App() {
  const [status, setStatus] = useState('checking...')

  useEffect(() => {
    axios.get('http://localhost:8000/api/health')
      .then(res => setStatus(res.data.ok ? 'backend reachable' : 'backend responded but not ok'))
      .catch(() => setStatus('backend unreachable'))
  }, [])

  return (
    <main style={{ padding: 40, fontFamily: 'system-ui' }}>
      <h1>Reunite</h1>
      <p>Privacy-first family reconnection bridge.</p>
      <p>Backend status: <strong>{status}</strong></p>
    </main>
  )
}