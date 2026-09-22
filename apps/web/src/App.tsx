import { useEffect, useState } from 'react'
import { getHealth } from './api/client'
import { UrlListPage } from './pages/UrlListPage'
import { WatchPage } from './pages/WatchPage'
import './App.css'

const PAGES = {
  '#/': { label: 'Watch', component: WatchPage },
  '#/urls': { label: 'URLs', component: UrlListPage },
} as const

type PageHash = keyof typeof PAGES

// Hash routing keeps the UI deployable as static files with no server rewrites.
function currentPage(): PageHash {
  return window.location.hash in PAGES ? (window.location.hash as PageHash) : '#/'
}

function App() {
  const [status, setStatus] = useState('checking…')
  const [page, setPage] = useState<PageHash>(currentPage)

  useEffect(() => {
    getHealth()
      .then((health) => setStatus(health.status))
      .catch((error: Error) => setStatus(`unreachable (${error.message})`))
  }, [])

  useEffect(() => {
    const onHashChange = () => setPage(currentPage())
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  const Page = PAGES[page].component

  return (
    <main>
      <h1>Media Proxy</h1>
      <nav className="nav">
        {(Object.keys(PAGES) as PageHash[]).map((hash) => (
          <a key={hash} href={hash} aria-current={hash === page ? 'page' : undefined}>
            {PAGES[hash].label}
          </a>
        ))}
      </nav>
      <Page />
      <p>
        API status: <code>{status}</code>
      </p>
    </main>
  )
}

export default App
