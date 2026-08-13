import { formatCurrency, formatPercent } from '@/design-system/format'

import type { PeriodSummary } from './types'

interface KpiCardProps {
  label: string
  value: string
  delta?: number | null
  /** "more is bad" metrics (expenses): a positive delta should read as unfavorable. */
  invert?: boolean
  footnote?: string
}

function KpiCard({ label, value, delta, invert, footnote }: KpiCardProps) {
  const hasDelta = delta !== undefined && delta !== null
  const favorable = hasDelta ? (invert ? delta < 0 : delta > 0) : null

  return (
    <div className="rounded-2xl border border-surface-border bg-surface-1 p-5">
      <p className="text-xs font-medium tracking-wide text-neutral-500 uppercase">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-neutral-50">{value}</p>
      {hasDelta ? (
        <p className={`mt-1 text-xs font-medium ${favorable ? 'text-accent' : 'text-red-400'}`}>
          {formatPercent(delta)} vs. mês anterior
        </p>
      ) : footnote ? (
        <p className="mt-1 text-xs text-neutral-500">{footnote}</p>
      ) : null}
    </div>
  )
}

export function KpiRow({ summary, deltas, month }: { summary: PeriodSummary; deltas: { income: number | null; expense: number | null; net: number | null }; month: string }) {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <KpiCard label="Receitas do período" value={formatCurrency(summary.income)} delta={deltas.income} />
      <KpiCard label="Despesas do período" value={formatCurrency(Math.abs(summary.expense))} delta={deltas.expense} invert />
      <KpiCard label="Saldo do período" value={formatCurrency(summary.net)} delta={deltas.net} />
      <KpiCard
        label="Maior categoria"
        value={summary.top_category ?? '—'}
        footnote={summary.top_category ? `${formatCurrency(summary.top_category_amount)} em ${month}` : 'Sem gastos no período'}
      />
    </div>
  )
}
