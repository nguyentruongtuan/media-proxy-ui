import { useState } from 'react'
import { createUrl, type UrlRecord } from '../api/client'
import { WatchForm } from '../components/WatchForm'

export function WatchPage() {
  const [watched, setWatched] = useState<UrlRecord | null>(null)

  const handleWatch = async (url: string) => {
    setWatched(await createUrl(url))
  }

  return (
    <>
      <WatchForm onWatch={handleWatch} />
      {watched && (
        <p className="watched">
          Saved: <code>{watched.url}</code>
        </p>
      )}
    </>
  )
}
