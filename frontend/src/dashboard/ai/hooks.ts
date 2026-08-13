import { useMutation, useQuery } from '@tanstack/react-query'

import { askAi, fetchAiInsights, fetchAiModels, testAiConnection } from './api'
import type { TypeFilter } from '../types'

export function useAiModels() {
  return useQuery({ queryKey: ['ai', 'models'], queryFn: fetchAiModels, staleTime: Infinity, retry: false })
}

export function useTestAiConnection() {
  return useMutation({ mutationFn: testAiConnection })
}

export function useAiInsights(month: string, categories: string[], type: TypeFilter, enabled: boolean) {
  return useQuery({
    queryKey: ['ai', 'insights', month, categories, type],
    queryFn: () => fetchAiInsights(month, categories, type),
    enabled: enabled && Boolean(month),
    retry: false,
  })
}

export function useAskAi() {
  return useMutation({ mutationFn: askAi })
}
