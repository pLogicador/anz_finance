import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { formatCurrency } from '@/design-system/format'

import { EmptyState } from '../EmptyState'
import type { MonthlySeriesRow } from '../types'

export function CumulativeBalanceChart({ data }: { data: MonthlySeriesRow[] }) {
  if (data.length < 2) {
    return <EmptyState icon="📉" title="Dados insuficientes para tendências" subtitle="Envie extratos de pelo menos 2 meses diferentes." />
  }

  let running = 0
  const chartData = data.map((row) => {
    running += row.Saldo
    return { Mês: row.Mês, SaldoAcumulado: running }
  })

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="balanceFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#34d399" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#34d399" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#232b26" vertical={false} />
          <XAxis dataKey="Mês" tick={{ fill: '#9ca89f', fontSize: 12 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: '#9ca89f', fontSize: 12 }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{ background: 'rgba(18, 22, 19, 0.92)', border: '1px solid rgba(35, 43, 38, 0.9)', borderRadius: 10, fontSize: 12, backdropFilter: 'blur(8px)' }}
            formatter={(value) => formatCurrency(Number(value))}
          />
          <Area type="monotone" dataKey="SaldoAcumulado" stroke="#34d399" strokeWidth={2} fill="url(#balanceFill)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
