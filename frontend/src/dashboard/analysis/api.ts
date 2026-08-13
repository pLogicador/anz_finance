import { apiRequest } from '@/lib/api-client'

import type { TypeFilter } from '../types'
import type { AnomaliesResponse, CategoryCountsResponse, CompareResponse, SearchResponse, SnapshotsResponse } from './types'

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

export function fetchAnomalies(categories: string[], type: TypeFilter) {
  return apiRequest<AnomaliesResponse>(`/analysis/anomalies${buildQuery({ categories, type })}`, 'GET')
}

export function fetchCompare(monthA: string, monthB: string, categories: string[], type: TypeFilter) {
  return apiRequest<CompareResponse>(`/analysis/compare${buildQuery({ month_a: monthA, month_b: monthB, categories, type })}`, 'GET')
}

export function fetchCategoryCounts(month: string) {
  return apiRequest<CategoryCountsResponse>(`/workspace/category-counts${buildQuery({ month })}`, 'GET')
}

export function searchTransactions(q: string, categories: string[], type: TypeFilter) {
  return apiRequest<SearchResponse>(`/workspace/search${buildQuery({ q, categories, type })}`, 'GET')
}

export function fetchSnapshots() {
  return apiRequest<SnapshotsResponse>('/workspace/snapshots', 'GET')
}

export function createSnapshot(body: { label: string; month: string; categories: string[]; type: TypeFilter }) {
  return apiRequest<SnapshotsResponse>('/workspace/snapshots', 'POST', { body })
}

export function deleteSnapshot(id: string) {
  return apiRequest<SnapshotsResponse>(`/workspace/snapshots/${id}`, 'DELETE')
}
