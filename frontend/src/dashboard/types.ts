export interface Transaction {
  Data: string
  Valor: number
  Descrição: string
  Mês: string
  Categorias: string
}

export interface FileUploadResult {
  filename: string
  status: 'ok' | 'failed'
  rows_parsed: number
  error: string | null
}

export interface UploadResponse {
  files: FileUploadResult[]
  total_transactions: number
  months: string[]
}

export interface MonthsResponse {
  months: string[]
  years: string[]
}

export interface TransactionsResponse {
  transactions: Transaction[]
  count: number
}

export interface PeriodSummary {
  income: number
  expense: number
  net: number
  transaction_count: number
  top_category: string | null
  top_category_amount: number
}

export interface MonthlySeriesRow {
  Mês: string
  Receitas: number
  Despesas: number
  Saldo: number
}

export interface CategoryBreakdownRow {
  Categorias: string
  Valor: number
}

export interface SummaryResponse {
  summary: PeriodSummary
  deltas: { income: number | null; expense: number | null; net: number | null }
  monthly_series: MonthlySeriesRow[]
  category_breakdown: CategoryBreakdownRow[]
}

export type TypeFilter = 'Todas' | 'Receitas' | 'Despesas'
