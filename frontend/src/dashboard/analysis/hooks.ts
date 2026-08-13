import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import type { TypeFilter } from '../types'
import { createSnapshot, deleteSnapshot, fetchAnomalies, fetchCategoryCounts, fetchCompare, fetchSnapshots, searchTransactions } from './api'

export function useAnomalies(categories: string[], type: TypeFilter, enabled: boolean) {
  return useQuery({ queryKey: ['analysis', 'anomalies', categories, type], queryFn: () => fetchAnomalies(categories, type), enabled, retry: false })
}

export function useCompare(monthA: string, monthB: string, categories: string[], type: TypeFilter, enabled: boolean) {
  return useQuery({
    queryKey: ['analysis', 'compare', monthA, monthB, categories, type],
    queryFn: () => fetchCompare(monthA, monthB, categories, type),
    enabled: enabled && Boolean(monthA) && Boolean(monthB) && monthA !== monthB,
    retry: false,
  })
}

export function useCategoryCounts(month: string, enabled: boolean) {
  return useQuery({ queryKey: ['workspace', 'category-counts', month], queryFn: () => fetchCategoryCounts(month), enabled: enabled && Boolean(month), retry: false })
}

export function useSearch() {
  return useMutation({ mutationFn: ({ q, categories, type }: { q: string; categories: string[]; type: TypeFilter }) => searchTransactions(q, categories, type) })
}

export function useSnapshots(enabled: boolean) {
  return useQuery({ queryKey: ['workspace', 'snapshots'], queryFn: fetchSnapshots, enabled, retry: false })
}

export function useCreateSnapshot() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createSnapshot,
    onSuccess: (data) => queryClient.setQueryData(['workspace', 'snapshots'], data),
  })
}

export function useDeleteSnapshot() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteSnapshot,
    onSuccess: (data) => queryClient.setQueryData(['workspace', 'snapshots'], data),
  })
}
