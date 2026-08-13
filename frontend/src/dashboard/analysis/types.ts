import type { Transaction } from '../types'

export interface Anomaly {
  date: string
  description: string
  category: string
  valor: number
  category_average: number
  ratio: number
}

export interface AnomaliesResponse {
  anomalies: Anomaly[]
}

export interface PeriodSummaryLite {
  income: number
  expense: number
  net: number
  transaction_count: number
  top_category: string | null
  top_category_amount: number
}

export interface CategoryDelta {
  category: string
  valor_a: number
  valor_b: number
  delta: number
}

export interface CompareResponse {
  month_a: string
  month_b: string
  summary_a: PeriodSummaryLite
  summary_b: PeriodSummaryLite
  income_change_pct: number | null
  expense_change_pct: number | null
  net_change_pct: number | null
  category_deltas: CategoryDelta[]
}

export interface CategoryCountsResponse {
  counts: Record<string, number>
}

export interface SearchResponse {
  transactions: Transaction[]
  count: number
}

export interface Snapshot {
  id: string
  label: string
  month: string
  categories: string[]
  type: string
  created_at: number
}

export interface SnapshotsResponse {
  snapshots: Snapshot[]
}
