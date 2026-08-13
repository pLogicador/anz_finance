import type { ReactNode } from 'react'

export function EmptyState({ icon, title, subtitle, action }: { icon: string; title: string; subtitle: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-surface-border bg-surface-1/40 px-6 py-12 text-center">
      <span className="text-2xl">{icon}</span>
      <h3 className="text-sm font-semibold text-neutral-100">{title}</h3>
      <p className="max-w-sm text-sm text-neutral-500">{subtitle}</p>
      {action}
    </div>
  )
}
