import { getAccessToken } from '@/auth/session-store'
import { env } from '@/lib/env'

import type { TypeFilter } from '../types'

function buildQuery(params: Record<string, string | string[] | undefined>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined) continue
    if (Array.isArray(value)) {
      for (const item of value) search.append(key, item)
    } else {
      search.append(key, value)
    }
  }
  const query = search.toString()
  return query ? `?${query}` : ''
}

/**
 * File-download variant of the API client -- unlike `apiRequest`, the
 * response body is a binary blob (CSV/PDF), not JSON, so it can't go
 * through the shared JSON helper. Triggers a real browser download via a
 * throwaway `<a download>` + object URL, same technique any static file
 * download uses.
 */
async function downloadFile(path: string, filename: string): Promise<void> {
  const token = getAccessToken()
  const headers: Record<string, string> = {}
  if (token) headers.Authorization = `Bearer ${token}`

  const response = await fetch(`${env.apiBaseUrl}${path}`, { headers, cache: 'no-store' })
  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    const message = typeof payload?.detail === 'string' ? payload.detail : (payload?.detail?.message ?? 'Não foi possível gerar o arquivo.')
    throw new Error(message)
  }

  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}

export function downloadCsv(month: string, categories: string[], type: TypeFilter) {
  return downloadFile(`/workspace/export/csv${buildQuery({ month, categories, type })}`, `anz-finance-${month}.csv`)
}

export function downloadPdf(month: string, categories: string[], type: TypeFilter) {
  return downloadFile(`/workspace/export/pdf${buildQuery({ month, categories, type })}`, `anz-finance-${month}.pdf`)
}
