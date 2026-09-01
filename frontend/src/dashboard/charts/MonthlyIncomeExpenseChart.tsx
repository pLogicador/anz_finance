import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { formatCurrency } from '@/design-system/format'

import { EmptyState } from '../EmptyState'
import type { MonthlySeriesRow } from '../types'

export function MonthlyIncomeExpenseChart({ data }: { data: MonthlySeriesRow[] }) {
  if (data.length < 2) {
    return <EmptyState icon="📈" title="Dados insuficientes para tendências" subtitle="Envie extratos de pelo menos 2 meses diferentes." />
  }

  const chartData = data.map((row) => ({ ...row, DespesasAbs: Math.abs(row.Despesas) }))

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer>
        <BarChart data={chartData} barGap={4}>
          <CartesianGrid stroke="#232b26" vertical={false} />
          <XAxis dataKey="Mês" tick={{ fill: '#9ca89f', fontSize: 12 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: '#9ca89f', fontSize: 12 }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{ background: 'rgba(18, 22, 19, 0.92)', border: '1px solid rgba(35, 43, 38, 0.9)', borderRadius: 10, fontSize: 12, backdropFilter: 'blur(8px)' }}
            formatter={(value) => formatCurrency(Number(value))}
          />
          <Bar dataKey="Receitas" fill="#34d399" radius={[4, 4, 0, 0]} />
          <Bar dataKey="DespesasAbs" name="Despesas" fill="#f87171" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
