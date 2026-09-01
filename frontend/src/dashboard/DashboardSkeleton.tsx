/**
 * Shown while `useMonths` resolves for the first time. A skeleton that
 * mirrors the real layout (header/filters/KPI/tab-content) reads as "the
 * product is loading" -- a bare "Carregando..." string reads as "did
 * something break?" for the ~1-2s a cold Render/Railway backend can take.
 * `motion-safe:animate-pulse` respects `prefers-reduced-motion` (see
 * index.css's global rule) automatically.
 */
function Block({ className }: { className?: string }) {
  return <div className={`rounded-2xl bg-surface-1/70 backdrop-blur-xl motion-safe:animate-pulse ${className ?? ''}`} />
}

export function DashboardSkeleton() {
  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6" aria-busy="true" aria-label="Carregando painel financeiro">
      <div className="flex items-center justify-between">
        <Block className="h-8 w-40" />
        <Block className="h-8 w-24" />
      </div>
      <Block className="h-14 w-full" />
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-[1.4fr_1fr_1fr]">
        <Block className="h-28 lg:col-span-1" />
        <Block className="h-28" />
        <Block className="h-28" />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Block className="h-64" />
        <Block className="h-64" />
      </div>
    </div>
  )
}
