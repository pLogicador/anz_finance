import { apiRequest } from '@/lib/api-client'

import type { AiAskResponse, AiInsightsResponse, AiModelsResponse, AiTestConnectionResponse } from './types'
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

export function fetchAiModels() {
  return apiRequest<AiModelsResponse>('/ai/models', 'GET')
}

export function testAiConnection(body: { provider: string; model: string | null; api_key: string | null }) {
  return apiRequest<AiTestConnectionResponse>('/ai/settings/test-connection', 'POST', { body })
}

export function fetchAiInsights(month: string, categories: string[], type: TypeFilter) {
  return apiRequest<AiInsightsResponse>(`/ai/insights${buildQuery({ month, categories, type })}`, 'GET')
}

export function askAi(body: {
  question: string
  month: string
  categories: string[]
  type: TypeFilter
  provider: string
  model: string | null
  api_key: string | null
}) {
  return apiRequest<AiAskResponse>('/ai/ask', 'POST', { body })
}
