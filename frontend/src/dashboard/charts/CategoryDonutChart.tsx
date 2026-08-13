import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'

import { categoryColor } from '@/design-system/category-colors'
import { formatCurrency } from '@/design-system/format'

import { EmptyState } from '../EmptyState'
import type { CategoryBreakdownRow } from '../types'

export function CategoryDonutChart({ data }: { data: CategoryBreakdownRow[] }) {
  if (data.length === 0) {
    return <EmptyState icon="📊" title="Sem gastos classificados" subtitle="Ainda não há despesas suficientes neste período." />
  }

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer>
        <PieChart>
          <Pie data={data} dataKey="Valor" nameKey="Categorias" innerRadius="55%" outerRadius="80%" paddingAngle={2}>
            {data.map((entry, index) => (
              <Cell key={entry.Categorias} fill={categoryColor(entry.Categorias, index)} stroke="none" />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ background: '#121613', border: '1px solid #232b26', borderRadius: 8, fontSize: 12 }}
            formatter={(value) => formatCurrency(Number(value))}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
