const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

// FastAPI puts the error message in `detail`; fall back to the status line.
async function toApiError(method: string, path: string, response: Response): Promise<ApiError> {
  let message = `${method} ${path} failed: ${response.status}`
  try {
    const body = (await response.json()) as { detail?: unknown }
    if (typeof body.detail === 'string') message = body.detail
  } catch {
    // Non-JSON error body; keep the default message.
  }
  return new ApiError(response.status, message)
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE_URL}/api${path}`)
  if (!response.ok) {
    throw await toApiError('GET', path, response)
  }
  return response.json() as Promise<T>
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${BASE_URL}/api${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    throw await toApiError('POST', path, response)
  }
  return response.json() as Promise<T>
}

export type Health = { status: string }

export const getHealth = () => apiGet<Health>('/health')

export type CrawlStatus = 'pending' | 'done' | 'failed'

export type CrawlData = {
  title: string | null
  description: string | null
  images: string[]
  stream_urls: string[]
  embed_urls: string[]
}

export type UrlRecord = {
  id: string
  url: string
  status: CrawlStatus
  crawl: CrawlData | null
  error: string | null
  created_at: string
  updated_at: string
  crawled_at: string | null
}

export const createUrl = (url: string) => apiPost<UrlRecord>('/urls', { url })
