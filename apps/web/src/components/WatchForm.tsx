import { useState, type FormEvent } from 'react'
import { isValidUrl } from '../lib/url'

type WatchFormProps = {
  // Rejecting shows the error's message under the input.
  onWatch: (url: string) => Promise<void>
}

export function WatchForm({ onWatch }: WatchFormProps) {
  const [value, setValue] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (submitting) return
    const url = value.trim()
    if (!isValidUrl(url)) {
      setError('Please enter a valid URL (starting with http:// or https://).')
      return
    }
    setError(null)
    setSubmitting(true)
    try {
      await onWatch(url)
      setValue('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save the URL.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="watch-form" onSubmit={handleSubmit} noValidate>
      <div className="watch-form__row">
        <input
          type="url"
          name="url"
          placeholder="https://example.com/video.mp4"
          aria-label="Media URL"
          aria-invalid={error !== null}
          aria-describedby={error ? 'watch-form-error' : undefined}
          value={value}
          onChange={(event) => {
            setValue(event.target.value)
            if (error) setError(null)
          }}
        />
        <button type="submit" disabled={submitting}>
          {submitting ? 'Saving…' : 'Watch'}
        </button>
      </div>
      {error && (
        <p id="watch-form-error" className="watch-form__error" role="alert">
          {error}
        </p>
      )}
    </form>
  )
}
