import type { TypeFilter } from '../types'
import { useAiInsights } from './hooks'

const KIND_STYLES: Record<string, string> = {
  positive: 'border-accent/30 bg-accent-soft text-accent',
  negative: 'border-red-500/30 bg-red-500/10 text-red-400',
  neutral: 'border-surface-border bg-surface-2 text-neutral-300',
}

const KIND_ICON: Record<string, string> = { positive: '↑', negative: '↓', neutral: '•' }

/** Deterministic, rule-based callouts (see backend/app/pipeline/insights.py
 * for why this isn't an LLM call) shown alongside the KPIs. */
export function AiInsights({ month, categories, type, enabled }: { month: string; categories: string[]; type: TypeFilter; enabled: boolean }) {
  const insightsQuery = useAiInsights(month, categories, type, enabled)
  const insights = insightsQuery.data?.insights ?? []

  if (!enabled || insights.length === 0) return null

  return (
    <div className="flex flex-wrap gap-2">
      {insights.map((insight, i) => (
        <div key={i} className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs ${KIND_STYLES[insight.kind]}`}>
          <span aria-hidden>{KIND_ICON[insight.kind]}</span>
          <span>{insight.text}</span>
        </div>
      ))}
    </div>
  )
}
