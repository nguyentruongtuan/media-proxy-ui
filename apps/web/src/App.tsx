import { useEffect, useState } from 'react'
import { getHealth } from './api/client'
import './App.css'

function App() {
  const [status, setStatus] = useState('checking…')

  useEffect(() => {
    getHealth()
      .then((health) => setStatus(health.status))
      .catch((error: Error) => setStatus(`unreachable (${error.message})`))
  }, [])

  return (
    <main>
      <h1>Media Proxy</h1>
      <p>
        API status: <code>{status}</code>
      </p>
    </main>
  )
}

export default App
