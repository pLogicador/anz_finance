import type { TypeFilter } from '../types'
import { demoInsights } from './demo-data'

// Mirrors `ai/AiInsights.tsx`'s visual language exactly (same style/icon
// maps) but sources from the local, synchronous `demoInsights()` instead of
// a network query -- kept as its own small component rather than reaching
// into `AiInsights`'s internals, since the two have genuinely different
// data sources (one is a react-query hook hitting the backend, the other is
// pure local computation) even though they should look identical to the user.
const KIND_STYLES: Record<string, string> = {
  positive: 'border-accent/30 bg-accent-soft text-accent',
  negative: 'border-red-500/30 bg-red-500/10 text-red-400',
  neutral: 'border-surface-border bg-surface-2 text-neutral-300',
}

const KIND_ICON: Record<string, string> = { positive: '↑', negative: '↓', neutral: '•' }

export function DemoInsights({ month, categories, type }: { month: string; categories: string[]; type: TypeFilter }) {
  const insights = demoInsights(month, categories, type)
  if (insights.length === 0) return null

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
