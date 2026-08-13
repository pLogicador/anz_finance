import { apiRequest, apiUpload } from '@/lib/api-client'

import type { MonthsResponse, SummaryResponse, TransactionsResponse, TypeFilter, UploadResponse } from './types'

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

/** `fields` carries Fase 5's AI provider/model/own-key selection -- see src/dashboard/ai/ai-settings-store.ts. */
export function uploadStatements(files: File[], fields: Record<string, string> = {}) {
  return apiUpload<UploadResponse>('/workspace/upload', files, fields)
}

export function fetchMonths() {
  return apiRequest<MonthsResponse>('/workspace/months', 'GET')
}

export function fetchTransactions(month: string, categories: string[], type: TypeFilter) {
  return apiRequest<TransactionsResponse>(`/workspace/transactions${buildQuery({ month, categories, type })}`, 'GET')
}

export function fetchTrend(categories: string[], type: TypeFilter) {
  return apiRequest<TransactionsResponse>(`/workspace/trend${buildQuery({ categories, type })}`, 'GET')
}

export function fetchSummary(month: string, categories: string[], type: TypeFilter) {
  return apiRequest<SummaryResponse>(`/workspace/summary${buildQuery({ month, categories, type })}`, 'GET')
}
