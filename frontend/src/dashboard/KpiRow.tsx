import { InfoTooltip } from '@/design-system/InfoTooltip'
import { formatCurrency, formatPercent } from '@/design-system/format'

import type { PeriodSummary } from './types'

interface DeltaProps {
  delta?: number | null
  /** "more is bad" metrics (expenses): a positive delta should read as unfavorable. */
  invert?: boolean
}

function Delta({ delta, invert }: DeltaProps) {
  if (delta === undefined || delta === null) return null
  const favorable = invert ? delta < 0 : delta > 0
  return <span className={`text-xs font-medium ${favorable ? 'text-accent' : 'text-red-400'}`}>{formatPercent(delta)} vs. mês anterior</span>
}

/**
 * Hierarchy redesign (was: 4 identical cards -- "parede de cards", no
 * signal of which number matters most). Saldo (net) is the one number
 * that answers "how am I actually doing this period" -- it's now the
 * visually dominant hero card, with Receitas/Despesas as smaller
 * secondary stats beside it, and "maior categoria" folded into the hero
 * card as a footnote instead of competing for its own full card.
 */
export function KpiRow({ summary, deltas, month }: { summary: PeriodSummary; deltas: { income: number | null; expense: number | null; net: number | null }; month: string }) {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-[1.4fr_1fr_1fr]">
      <div className="glass-panel-hero col-span-2 p-5 lg:col-span-1">
        <div className="flex items-center gap-1.5">
          <p className="text-xs font-medium tracking-wide text-neutral-400 uppercase">Saldo do período</p>
          <InfoTooltip>
            Receitas menos despesas em {month}, considerando apenas as categorias e o tipo de transação que você tem
            selecionados nos filtros.
          </InfoTooltip>
        </div>
        <p className="font-display mt-2 text-4xl font-bold tabular-nums text-neutral-50 sm:text-5xl">{formatCurrency(summary.net)}</p>
        <Delta delta={deltas.net} />
        <div className="mt-4 border-t border-accent/20 pt-3 text-xs text-neutral-400">
          {summary.top_category ? (
            <>
              Maior categoria: <span className="font-medium text-neutral-200">{summary.top_category}</span> ({formatCurrency(summary.top_category_amount)})
            </>
          ) : (
            'Sem gastos categorizados no período.'
          )}
        </div>
      </div>

      <div className="glass-panel p-4">
        <p className="text-xs font-medium tracking-wide text-neutral-500 uppercase">Receitas</p>
        <p className="font-display mt-1.5 text-xl font-semibold tabular-nums text-neutral-50">{formatCurrency(summary.income)}</p>
        <Delta delta={deltas.income} />
      </div>

      <div className="glass-panel p-4">
        <p className="text-xs font-medium tracking-wide text-neutral-500 uppercase">Despesas</p>
        <p className="font-display mt-1.5 text-xl font-semibold tabular-nums text-neutral-50">{formatCurrency(Math.abs(summary.expense))}</p>
        <Delta delta={deltas.expense} invert />
      </div>
    </div>
  )
}
