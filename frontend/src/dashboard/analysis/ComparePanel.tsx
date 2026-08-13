import { useState } from 'react'

import { formatCurrency, formatPercent } from '@/design-system/format'

import type { TypeFilter } from '../types'
import { useCompare } from './hooks'

/** Arbitrary two-period comparison -- beyond the single "vs. previous
 * month" delta the KPI row already shows (e.g. same month a year apart). */
export function ComparePanel({ months, categories, type }: { months: string[]; categories: string[]; type: TypeFilter }) {
  const [monthA, setMonthA] = useState(months[1] ?? months[0] ?? '')
  const [monthB, setMonthB] = useState(months[0] ?? '')
  const enabled = months.length >= 2
  const compareQuery = useCompare(monthA, monthB, categories, type, enabled)
  const data = compareQuery.data

  return (
    <div className="rounded-2xl border border-surface-border bg-surface-1 p-4">
      <h3 className="mb-3 text-sm font-medium text-neutral-300">Comparar dois períodos</h3>

      {months.length < 2 ? (
        <p className="text-sm text-neutral-500">Envie extratos de pelo menos 2 meses para comparar períodos.</p>
      ) : (
        <>
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <select value={monthA} onChange={(e) => setMonthA(e.target.value)} className="rounded-lg border border-surface-border bg-surface-2 px-3 py-1.5 text-sm text-neutral-200">
              {months.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
            <span className="text-xs text-neutral-500">vs.</span>
            <select value={monthB} onChange={(e) => setMonthB(e.target.value)} className="rounded-lg border border-surface-border bg-surface-2 px-3 py-1.5 text-sm text-neutral-200">
              {months.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>

          {monthA === monthB ? <p className="text-sm text-neutral-500">Selecione dois meses diferentes.</p> : null}
          {compareQuery.isLoading && monthA !== monthB ? <p className="text-sm text-neutral-500">Comparando...</p> : null}
          {compareQuery.isError ? <p className="text-sm text-red-400">Não foi possível comparar esses períodos.</p> : null}

          {data ? (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-3 text-sm">
                <div />
                <div className="text-center text-xs font-medium text-neutral-500 uppercase">{data.month_a}</div>
                <div className="text-center text-xs font-medium text-neutral-500 uppercase">{data.month_b}</div>

                <div className="text-neutral-400">Receitas</div>
                <div className="text-center text-neutral-200">{formatCurrency(data.summary_a.income)}</div>
                <div className="text-center text-neutral-200">{formatCurrency(data.summary_b.income)}</div>

                <div className="text-neutral-400">Despesas</div>
                <div className="text-center text-neutral-200">{formatCurrency(Math.abs(data.summary_a.expense))}</div>
                <div className="text-center text-neutral-200">{formatCurrency(Math.abs(data.summary_b.expense))}</div>

                <div className="text-neutral-400">Saldo</div>
                <div className="text-center text-neutral-200">{formatCurrency(data.summary_a.net)}</div>
                <div className="text-center text-neutral-200">{formatCurrency(data.summary_b.net)}</div>
              </div>

              <div className="flex flex-wrap gap-3 text-xs">
                <span className="text-neutral-500">Variação de receitas: {formatPercent(data.income_change_pct)}</span>
                <span className="text-neutral-500">Variação de despesas: {formatPercent(data.expense_change_pct)}</span>
                <span className="text-neutral-500">Variação de saldo: {formatPercent(data.net_change_pct)}</span>
              </div>

              {data.category_deltas.length > 0 ? (
                <div>
                  <p className="mb-2 text-xs font-medium tracking-wide text-neutral-500 uppercase">Maiores variações por categoria</p>
                  <ul className="space-y-1">
                    {[...data.category_deltas]
                      .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
                      .slice(0, 6)
                      .map((d) => (
                        <li key={d.category} className="flex items-center justify-between text-sm">
                          <span className="text-neutral-300">{d.category}</span>
                          <span className={d.delta > 0 ? 'text-red-400' : 'text-accent'}>
                            {d.delta > 0 ? '+' : ''}
                            {formatCurrency(d.delta)}
                          </span>
                        </li>
                      ))}
                  </ul>
                </div>
              ) : null}
            </div>
          ) : null}
        </>
      )}
    </div>
  )
}
