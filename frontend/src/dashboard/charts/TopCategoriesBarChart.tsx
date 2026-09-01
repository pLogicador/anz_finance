import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { categoryColor } from '@/design-system/category-colors'
import { formatCurrency } from '@/design-system/format'

import { EmptyState } from '../EmptyState'
import type { CategoryBreakdownRow } from '../types'

export function TopCategoriesBarChart({ data }: { data: CategoryBreakdownRow[] }) {
  const top = [...data].sort((a, b) => b.Valor - a.Valor).slice(0, 8).reverse()

  if (top.length === 0) {
    return <EmptyState icon="📈" title="Sem gastos classificados" subtitle="Ainda não há despesas suficientes neste período." />
  }

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer>
        <BarChart data={top} layout="vertical" margin={{ left: 24, right: 24 }}>
          <XAxis type="number" hide />
          <YAxis type="category" dataKey="Categorias" width={140} tick={{ fill: '#9ca89f', fontSize: 12 }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{ background: 'rgba(18, 22, 19, 0.92)', border: '1px solid rgba(35, 43, 38, 0.9)', borderRadius: 10, fontSize: 12, backdropFilter: 'blur(8px)' }}
            formatter={(value) => formatCurrency(Number(value))}
            cursor={{ fill: '#ffffff08' }}
          />
          <Bar dataKey="Valor" radius={[0, 6, 6, 0]}>
            {top.map((entry, index) => (
              <Cell key={entry.Categorias} fill={categoryColor(entry.Categorias, index)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
