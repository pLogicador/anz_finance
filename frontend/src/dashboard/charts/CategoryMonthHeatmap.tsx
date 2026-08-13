import { useMemo } from 'react'

import { formatCurrency } from '@/design-system/format'

import { EmptyState } from '../EmptyState'
import type { Transaction } from '../types'

/** Client-side aggregation: category x month expense totals. Filters to
 * `Valor < 0` internally -- same as the legacy chart builder
 * (modules/ui/charts.py::category_month_heatmap), so viewing this under
 * the "Receitas" type filter correctly renders empty rather than showing
 * income data in an expense-shaped chart. */
function aggregate(transactions: Transaction[]) {
  const expenses = transactions.filter((t) => t.Valor < 0)
  const months = Array.from(new Set(expenses.map((t) => t.Mês))).sort()
  const categories = Array.from(new Set(expenses.map((t) => t.Categorias))).sort()

  const totals = new Map<string, number>()
  let max = 0
  for (const t of expenses) {
    const key = `${t.Categorias}::${t.Mês}`
    const value = (totals.get(key) ?? 0) + Math.abs(t.Valor)
    totals.set(key, value)
    if (value > max) max = value
  }

  return { months, categories, totals, max }
}

export function CategoryMonthHeatmap({ transactions }: { transactions: Transaction[] }) {
  const { months, categories, totals, max } = useMemo(() => aggregate(transactions), [transactions])

  if (months.length < 2) {
    return <EmptyState icon="🗓️" title="Dados insuficientes para o mapa de gastos" subtitle="Envie extratos de pelo menos 2 meses diferentes." />
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-separate border-spacing-1 text-xs">
        <thead>
          <tr>
            <th className="text-left text-neutral-500"></th>
            {months.map((month) => (
              <th key={month} className="px-2 py-1 font-medium text-neutral-500">
                {month}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {categories.map((category) => (
            <tr key={category}>
              <td className="pr-2 text-right whitespace-nowrap text-neutral-400">{category}</td>
              {months.map((month) => {
                const value = totals.get(`${category}::${month}`) ?? 0
                const intensity = max > 0 ? value / max : 0
                return (
                  <td key={month} className="p-0">
                    <div
                      className="flex h-10 w-20 items-center justify-center rounded-md text-[11px] text-neutral-200"
                      style={{ backgroundColor: `rgba(52, 211, 153, ${0.08 + intensity * 0.55})` }}
                      title={formatCurrency(value)}
                    >
                      {value > 0 ? formatCurrency(value).replace('R$', '').trim() : ''}
                    </div>
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
