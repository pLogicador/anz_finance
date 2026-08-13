import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { AccessApiError, AccessErrorCode } from '@/auth/access-errors'

import { fetchMonths, fetchSummary, fetchTransactions, fetchTrend, uploadStatements } from './api'
import type { TypeFilter } from './types'

export function isWorkSessionExpired(error: unknown): boolean {
  return error instanceof AccessApiError && error.errorCode === AccessErrorCode.WORK_SESSION_EXPIRED
}

export function useUploadStatements() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ files, fields }: { files: File[]; fields?: Record<string, string> }) => uploadStatements(files, fields),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['workspace'] })
    },
  })
}

export function useMonths(enabled: boolean) {
  return useQuery({
    queryKey: ['workspace', 'months'],
    queryFn: fetchMonths,
    enabled,
    retry: false,
  })
}

export function useTransactions(month: string, categories: string[], type: TypeFilter, enabled: boolean) {
  return useQuery({
    queryKey: ['workspace', 'transactions', month, categories, type],
    queryFn: () => fetchTransactions(month, categories, type),
    enabled: enabled && Boolean(month),
    retry: false,
  })
}

export function useSummary(month: string, categories: string[], type: TypeFilter, enabled: boolean) {
  return useQuery({
    queryKey: ['workspace', 'summary', month, categories, type],
    queryFn: () => fetchSummary(month, categories, type),
    enabled: enabled && Boolean(month),
    retry: false,
  })
}

/** Category+type filtered, full-history transactions -- same "trend_df" semantics the legacy app kept separate from the period-filtered view. Feeds the heatmap (aggregated client-side, see charts/CategoryMonthHeatmap.tsx). */
export function useTrend(categories: string[], type: TypeFilter, enabled: boolean) {
  return useQuery({
    queryKey: ['workspace', 'trend-raw', categories, type],
    queryFn: () => fetchTrend(categories, type),
    enabled,
    retry: false,
  })
}

/** Unfiltered (all categories, all types) -- used only to derive the category filter's own option list, which must not shrink based on the current category selection. */
export function useAllCategories(enabled: boolean) {
  const query = useQuery({
    queryKey: ['workspace', 'all-categories'],
    queryFn: () => fetchTrend([], 'Todas'),
    enabled,
    retry: false,
  })
  const categories = query.data ? Array.from(new Set(query.data.transactions.map((t) => t.Categorias))).sort() : []
  return { ...query, categories }
}
