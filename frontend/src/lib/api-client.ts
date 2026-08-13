import { AccessApiError, AccessErrorCode } from '@/auth/access-errors'
import { getAccessToken, useSessionStore } from '@/auth/session-store'
import { env } from '@/lib/env'

interface RequestOptions {
  /** Attach the current ANZ session as `Authorization: Bearer`. Default true. */
  auth?: boolean
  body?: unknown
}

/**
 * Every authenticated call in the app goes through here. On a 401, the
 * session is cleared immediately -- an expired/invalid ANZ session has no
 * self-serve renewal (guardrail #2: no independent re-auth path), so the
 * only correct move is to drop back to the access gate, which will show
 * the institutional block screen since there's no fresh Syncron token to
 * bridge with.
 *
 * `cache: 'no-store'` here is belt-and-suspenders on top of the backend's
 * own `Cache-Control: no-store` middleware (see backend/app/main.py). The
 * backend header is the real fix; this is defense in depth found while
 * debugging a real bug in Fase 4: a GET to `/workspace/months` made once
 * (before the middleware existed) got silently replayed by the browser's
 * own HTTP cache for every later identical-URL GET -- even after a real
 * upload had succeeded server-side -- because nothing told the browser not
 * to keep it. Every response from this API is dynamic/session-scoped and
 * must never be cached.
 */
export async function apiRequest<T>(path: string, method: string, options: RequestOptions = {}): Promise<T> {
  const { auth = true, body } = options
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }

  if (auth) {
    const token = getAccessToken()
    if (token) headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(`${env.apiBaseUrl}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: 'no-store',
  })

  if (response.status === 401 && auth) {
    useSessionStore.getState().clearSession()
  }

  if (!response.ok) {
    throw await readApiError(response)
  }

  return (await response.json()) as T
}

/**
 * Shared error-extraction for both `apiRequest` and `apiUpload`. Every
 * failure still surfaces as an `AccessApiError` (nothing downstream
 * branches on the *type*, only `error_code` when present -- see
 * `isWorkSessionExpired`/`HubBridgeGate`), but the *message* now always
 * prefers whatever the backend actually said (`detail.message`/a bare
 * string `detail`) over the generic HTTP status text. This matters for
 * Fase 5's AI routes, which return `{"detail": {"message": "..."}}` on
 * 400/502 without an `error_code` (there's no distinct screen to route to
 * for "unknown AI provider" or "provider didn't answer" -- those are just
 * shown inline) -- before this, that message was silently discarded in
 * favor of "HTTP 400"/"HTTP 502".
 */
async function readApiError(response: Response): Promise<AccessApiError> {
  const payload = await response.json().catch(() => null)
  const detail = payload?.detail
  if (detail?.error_code) {
    return new AccessApiError(detail.error_code as AccessErrorCode, detail.message ?? response.statusText)
  }
  const message = typeof detail === 'string' ? detail : (detail?.message ?? response.statusText)
  return new AccessApiError(AccessErrorCode.AUTH_SERVICE_UNAVAILABLE, message || `HTTP ${response.status}`)
}

/**
 * General multipart POST (Fase 7) -- unlike `apiUpload` below (fixed
 * "files" field name, matching `/workspace/upload`'s param), this takes a
 * caller-built `FormData` so a route with a different shape (the CSV
 * import routes take a single `file` field plus column-mapping fields)
 * doesn't need its own bespoke fetch wrapper.
 */
export async function apiMultipart<T>(path: string, formData: FormData): Promise<T> {
  const token = getAccessToken()
  const headers: Record<string, string> = {}
  if (token) headers.Authorization = `Bearer ${token}`

  const response = await fetch(`${env.apiBaseUrl}${path}`, { method: 'POST', headers, body: formData, cache: 'no-store' })

  if (response.status === 401) useSessionStore.getState().clearSession()
  if (!response.ok) {
    throw await readApiError(response)
  }

  return (await response.json()) as T
}

/**
 * Multipart upload variant -- the generic apiRequest always JSON-encodes
 * the body. `fields` are extra form fields alongside the files (Fase 5:
 * AI provider/model/own-api-key selection) -- when a field is a user's own
 * API key, it is sent for this one request only, exactly like any other
 * field here; nothing about this function persists it anywhere.
 */
export async function apiUpload<T>(path: string, files: File[], fields: Record<string, string> = {}): Promise<T> {
  const token = getAccessToken()
  const headers: Record<string, string> = {}
  if (token) headers.Authorization = `Bearer ${token}`

  const formData = new FormData()
  for (const file of files) formData.append('files', file)
  for (const [key, value] of Object.entries(fields)) formData.append(key, value)

  const response = await fetch(`${env.apiBaseUrl}${path}`, { method: 'POST', headers, body: formData, cache: 'no-store' })

  if (response.status === 401) useSessionStore.getState().clearSession()

  if (!response.ok) {
    throw await readApiError(response)
  }

  return (await response.json()) as T
}
