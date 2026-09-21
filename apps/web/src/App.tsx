import { useEffect, useState } from 'react'
import { getHealth } from './api/client'
import { WatchForm } from './components/WatchForm'
import './App.css'

function App() {
  const [status, setStatus] = useState('checking…')
  const [watchedUrl, setWatchedUrl] = useState<string | null>(null)

  useEffect(() => {
    getHealth()
      .then((health) => setStatus(health.status))
      .catch((error: Error) => setStatus(`unreachable (${error.message})`))
  }, [])

  return (
    <main>
      <h1>Media Proxy</h1>
      <WatchForm onWatch={setWatchedUrl} />
      {watchedUrl && (
        <p className="watched">
          Watching: <code>{watchedUrl}</code>
        </p>
      )}
      <p>
        API status: <code>{status}</code>
      </p>
    </main>
  )
}

export default App
