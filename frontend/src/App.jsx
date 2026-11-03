import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import Seeker from './screens/Seeker'
import Respond from './screens/Respond'
import Admin from './screens/Admin'
import GroupSeeker from './screens/GroupSeeker'
import Channel from './screens/Channel'
import './App.css'

export default function App() {
  return (
    <BrowserRouter>
      <nav style={{ padding: '12px 24px', borderBottom: '1px solid #ddd', display: 'flex', gap: 16 }}>
        <Link to="/">Seeker</Link>
        <Link to="/group">Group</Link>
        <Link to="/admin">Admin (demo)</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Seeker />} />
        <Route path="/group" element={<GroupSeeker />} />
        <Route path="/respond/:token" element={<Respond />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/channel/:channelId" element={<Channel />} />
      </Routes>
    </BrowserRouter>
  )
}