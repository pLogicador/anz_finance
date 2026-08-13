export interface AiModelOption {
  provider: string
  model: string
  label: string
}

export interface AiModelsResponse {
  models: AiModelOption[]
}

export interface AiTestConnectionResponse {
  ok: boolean
}

export type InsightKind = 'positive' | 'negative' | 'neutral'

export interface AiInsight {
  kind: InsightKind
  text: string
}

export interface AiInsightsResponse {
  insights: AiInsight[]
}

export interface AiAskResponse {
  answer: string
}

export interface ChatTurn {
  id: string
  question: string
  answer: string | null
  error: string | null
  pending: boolean
}
