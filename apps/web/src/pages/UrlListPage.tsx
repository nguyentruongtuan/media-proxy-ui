import { useEffect, useState } from 'react'
import { crawlUrl, listUrls, type UrlRecord } from '../api/client'

export function UrlListPage() {
  const [urls, setUrls] = useState<UrlRecord[] | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [extracting, setExtracting] = useState<Set<string>>(new Set())
  // Last extract failure per URL id, shown in that row.
  const [rowErrors, setRowErrors] = useState<Record<string, string>>({})

  const load = () =>
    listUrls()
      .then((records) => {
        setUrls(records)
        setLoadError(null)
      })
      .catch((err: Error) => setLoadError(err.message))

  useEffect(() => {
    void load()
  }, [])

  const setRowError = (id: string, message: string | null) =>
    setRowErrors((prev) => {
      const next = { ...prev }
      if (message) next[id] = message
      else delete next[id]
      return next
    })

  const handleExtract = async (id: string) => {
    setExtracting((prev) => new Set(prev).add(id))
    setRowError(id, null)
    try {
      const updated = await crawlUrl(id)
      setUrls((prev) => prev?.map((record) => (record.id === id ? updated : record)) ?? null)
    } catch (err) {
      setRowError(id, err instanceof Error ? err.message : 'Extract failed.')
      // The API stores the failure on the record, so refresh to show its new status.
      void load()
    } finally {
      setExtracting((prev) => {
        const next = new Set(prev)
        next.delete(id)
        return next
      })
    }
  }

  if (loadError) {
    return (
      <p className="url-list__error" role="alert">
        {loadError}
      </p>
    )
  }
  if (urls === null) return <p>Loading…</p>
  if (urls.length === 0) return <p>No URLs saved yet.</p>

  return (
    <table className="url-list">
      <thead>
        <tr>
          <th>Id</th>
          <th>Title</th>
          <th>URL</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
        {urls.map((record) => (
          <tr key={record.id}>
            <td>
              <code>{record.id}</code>
            </td>
            <td>{record.crawl?.title ?? '—'}</td>
            <td className="url-list__url">
              <a href={record.url} target="_blank" rel="noreferrer">
                {record.url}
              </a>
              {rowErrors[record.id] && (
                <p className="url-list__error" role="alert">
                  {rowErrors[record.id]}
                </p>
              )}
            </td>
            <td>
              <button
                type="button"
                disabled={extracting.has(record.id)}
                onClick={() => void handleExtract(record.id)}
              >
                {extracting.has(record.id) ? 'Extracting…' : 'Extract'}
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
