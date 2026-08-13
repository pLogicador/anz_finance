import { formatCurrency, formatDateBr } from '@/design-system/format'

import type { TypeFilter } from '../types'
import { useAnomalies } from './hooks'

/** Statistical outlier detection (see backend/app/pipeline/analysis.py) --
 * expense transactions at least 2.5x their own category's average. */
export function AnomaliesPanel({ categories, type, enabled }: { categories: string[]; type: TypeFilter; enabled: boolean }) {
  const query = useAnomalies(categories, type, enabled)
  const anomalies = query.data?.anomalies ?? []

  return (
    <div className="rounded-2xl border border-surface-border bg-surface-1 p-4">
      <h3 className="mb-1 text-sm font-medium text-neutral-300">Gastos fora do padrão</h3>
      <p className="mb-3 text-xs text-neutral-500">
        Transações de despesa bem acima da média da própria categoria (todo o histórico enviado, não só o mês selecionado).
      </p>

      {query.isLoading ? <p className="text-sm text-neutral-500">Analisando...</p> : null}

      {!query.isLoading && anomalies.length === 0 ? (
        <p className="text-sm text-neutral-500">Nenhum gasto fora do padrão encontrado nos dados enviados.</p>
      ) : null}

      <ul className="space-y-2">
        {anomalies.map((a, i) => (
          <li key={i} className="flex items-center justify-between gap-3 rounded-lg border border-surface-border bg-surface-2 px-3 py-2">
            <div className="min-w-0">
              <p className="truncate text-sm text-neutral-200">{a.description}</p>
              <p className="text-xs text-neutral-500">
                {formatDateBr(a.date)} · {a.category} · média da categoria: {formatCurrency(a.category_average)}
              </p>
            </div>
            <div className="flex shrink-0 flex-col items-end">
              <span className="text-sm font-semibold text-red-400">{formatCurrency(Math.abs(a.valor))}</span>
              <span className="text-xs text-red-400/80">{a.ratio.toFixed(1)}x a média</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
