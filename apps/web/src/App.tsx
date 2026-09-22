import { useEffect, useState } from 'react'
import { createUrl, getHealth, type UrlRecord } from './api/client'
import { WatchForm } from './components/WatchForm'
import './App.css'

function App() {
  const [status, setStatus] = useState('checking…')
  const [watched, setWatched] = useState<UrlRecord | null>(null)

  useEffect(() => {
    getHealth()
      .then((health) => setStatus(health.status))
      .catch((error: Error) => setStatus(`unreachable (${error.message})`))
  }, [])

  const handleWatch = async (url: string) => {
    setWatched(await createUrl(url))
  }

  return (
    <main>
      <h1>Media Proxy</h1>
      <WatchForm onWatch={handleWatch} />
      {watched && (
        <p className="watched">
          Saved: <code>{watched.url}</code>
        </p>
      )}
      <p>
        API status: <code>{status}</code>
      </p>
    </main>
  )
}

export default App
