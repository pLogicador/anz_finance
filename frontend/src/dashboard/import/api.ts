import { apiMultipart } from '@/lib/api-client'

export interface CsvPreviewResponse {
  columns: string[]
  sample_rows: Record<string, unknown>[]
  row_count: number
}

export interface CsvCommitResponse {
  total_transactions: number
  imported_rows: number
  months: string[]
}

export function previewCsv(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return apiMultipart<CsvPreviewResponse>('/workspace/import/csv/preview', formData)
}

export interface CommitCsvParams {
  file: File
  dateColumn: string
  valorColumn: string
  descriptionColumn: string
  provider: string
  model: string | null
  api_key: string | null
}

export function commitCsv(params: CommitCsvParams) {
  const formData = new FormData()
  formData.append('file', params.file)
  formData.append('date_column', params.dateColumn)
  formData.append('valor_column', params.valorColumn)
  formData.append('description_column', params.descriptionColumn)
  formData.append('provider', params.provider)
  if (params.model) formData.append('model', params.model)
  if (params.api_key) formData.append('api_key', params.api_key)
  return apiMultipart<CsvCommitResponse>('/workspace/import/csv/commit', formData)
}
