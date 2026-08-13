/**
 * A hand-crafted preview of the dashboard for the landing page hero --
 * deliberately NOT a raw screenshot and NOT importing Recharts/any
 * dashboard-internal component. Two reasons: (1) this file is part of the
 * public bundle (pre-auth), and pulling a charting library or real
 * dashboard code in here would defeat the whole point of the public/
 * authenticated bundle split (PARTE 5.7/23 -- nothing dashboard-only
 * should be fetched before the user is authorized); (2) a live screenshot
 * taken in this dev environment (no Groq/OpenAI key configured) would show
 * every transaction as "Erro na classificação" -- true today, but not
 * representative, and confusing on a page whose whole job is to build
 * trust in 5 seconds. A curated mock with realistic category names and
 * numbers is the more honest choice here, not a shortcut.
 */
const CATEGORY_BARS = [
  { label: 'Moradia', pct: 32, color: '#34d399' },
  { label: 'Mercado', pct: 24, color: '#5eead4' },
  { label: 'Transporte', pct: 18, color: '#2dd4bf' },
  { label: 'Lazer', pct: 14, color: '#a7f3d0' },
  { label: 'Outros', pct: 12, color: '#134e3f' },
]

const MONTH_BARS = [38, 52, 44, 61, 49, 72]

export function DashboardPreview({ className }: { className?: string }) {
  const gradientStops = (() => {
    let acc = 0
    return CATEGORY_BARS.map((c) => {
      const start = acc
      acc += c.pct
      return `${c.color} ${start}% ${acc}%`
    }).join(', ')
  })()

  return (
    <div className={`overflow-hidden rounded-2xl border border-surface-border bg-surface-1 shadow-2xl shadow-black/40 ${className ?? ''}`}>
      {/* fake window chrome -- signals "this is a real app", not a generic illustration */}
      <div className="flex items-center gap-1.5 border-b border-surface-border bg-surface-2 px-4 py-2.5">
        <span className="h-2.5 w-2.5 rounded-full bg-red-400/70" />
        <span className="h-2.5 w-2.5 rounded-full bg-yellow-400/70" />
        <span className="h-2.5 w-2.5 rounded-full bg-accent/70" />
        <span className="ml-3 text-[11px] text-neutral-500">ANZ Finance -- Painel financeiro</span>
      </div>

      <div className="space-y-4 p-4 sm:p-5">
        {/* KPI row */}
        <div className="grid grid-cols-3 gap-2 sm:gap-3">
          <div className="rounded-xl border border-surface-border bg-surface-2 p-2.5 sm:p-3">
            <p className="text-[9px] font-medium tracking-wide text-neutral-500 uppercase sm:text-[10px]">Receitas</p>
            <p className="mt-1 text-sm font-semibold text-neutral-50 sm:text-base">R$ 8.450</p>
            <p className="mt-0.5 text-[10px] font-medium text-accent">+6,2%</p>
          </div>
          <div className="rounded-xl border border-surface-border bg-surface-2 p-2.5 sm:p-3">
            <p className="text-[9px] font-medium tracking-wide text-neutral-500 uppercase sm:text-[10px]">Despesas</p>
            <p className="mt-1 text-sm font-semibold text-neutral-50 sm:text-base">R$ 3.120</p>
            <p className="mt-0.5 text-[10px] font-medium text-red-400">+2,8%</p>
          </div>
          <div className="rounded-xl border border-accent/30 bg-accent-soft p-2.5 sm:p-3">
            <p className="text-[9px] font-medium tracking-wide text-neutral-400 uppercase sm:text-[10px]">Saldo</p>
            <p className="mt-1 text-sm font-semibold text-neutral-50 sm:text-base">R$ 5.330</p>
            <p className="mt-0.5 text-[10px] font-medium text-accent">+18,4%</p>
          </div>
        </div>

        {/* donut + category legend, trend bars */}
        <div className="grid grid-cols-2 gap-3 sm:gap-4">
          <div className="flex items-center gap-3 rounded-xl border border-surface-border bg-surface-2 p-3">
            <div
              className="h-14 w-14 shrink-0 rounded-full sm:h-16 sm:w-16"
              style={{ background: `conic-gradient(${gradientStops})`, mask: 'radial-gradient(farthest-side, transparent 62%, black 63%)' }}
              aria-hidden
            />
            <ul className="min-w-0 space-y-1">
              {CATEGORY_BARS.slice(0, 3).map((c) => (
                <li key={c.label} className="flex items-center gap-1.5 text-[10px] text-neutral-400">
                  <span className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ backgroundColor: c.color }} aria-hidden />
                  <span className="truncate">{c.label}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="flex items-end gap-1 rounded-xl border border-surface-border bg-surface-2 p-3">
            {MONTH_BARS.map((h, i) => (
              <div
                key={i}
                className="flex-1 rounded-t-sm bg-gradient-to-t from-accent-strong to-accent"
                style={{ height: `${h}%`, opacity: 0.5 + (i / MONTH_BARS.length) * 0.5 }}
                aria-hidden
              />
            ))}
          </div>
        </div>

        {/* insight callout -- matches the real AiInsights component's visual language */}
        <div className="flex items-center gap-1.5 rounded-lg border border-accent/30 bg-accent-soft px-3 py-2 text-[11px] text-accent">
          <span aria-hidden>↑</span>
          <span>Você guardou 18% da sua renda este mês -- uma taxa de poupança saudável.</span>
        </div>
      </div>
    </div>
  )
}
