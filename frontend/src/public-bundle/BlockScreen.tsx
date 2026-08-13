import type { ReactNode } from 'react'

/** Shared shell for every PARTE 5 non-authorized screen -- kept in `public-bundle/` so it never pulls in dashboard code. */
export function BlockScreen({
  icon,
  title,
  subtitle,
  action,
}: {
  icon: ReactNode
  title: string
  subtitle: string
  action?: ReactNode
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-950 px-6 text-neutral-100">
      <div className="w-full max-w-md rounded-2xl border border-neutral-800 bg-neutral-900/60 p-8 text-center shadow-xl">
        <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-neutral-800 text-2xl">
          {icon}
        </div>
        <h1 className="text-xl font-semibold text-neutral-50">{title}</h1>
        <p className="mt-2 text-sm leading-relaxed text-neutral-400">{subtitle}</p>
        {action ? <div className="mt-6">{action}</div> : null}
      </div>
    </div>
  )
}
