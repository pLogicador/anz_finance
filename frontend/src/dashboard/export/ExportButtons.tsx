import { useState } from 'react'

import type { TypeFilter } from '../types'
import { downloadCsv, downloadPdf } from './api'

/** Both exports respect the dashboard's currently-active filters -- the
 * real gap the legacy app had (its one export button always dumped the
 * whole unfiltered dataset). */
export function ExportButtons({ month, categories, type }: { month: string; categories: string[]; type: TypeFilter }) {
  const [pending, setPending] = useState<'csv' | 'pdf' | null>(null)
  const [error, setError] = useState<string | null>(null)

  const run = (kind: 'csv' | 'pdf', action: () => Promise<void>) => {
    setPending(kind)
    setError(null)
    action()
      .catch((err: unknown) => setError(err instanceof Error ? err.message : 'Falha ao exportar.'))
      .finally(() => setPending(null))
  }

  return (
    <div className="flex items-center gap-2 print:hidden">
      <button
        type="button"
        disabled={!month || pending !== null}
        onClick={() => run('csv', () => downloadCsv(month, categories, type))}
        className="rounded-lg border border-surface-border px-3 py-1.5 text-xs text-neutral-300 transition hover:border-accent/50 disabled:cursor-not-allowed disabled:opacity-40"
      >
        {pending === 'csv' ? 'Gerando CSV...' : 'Baixar CSV'}
      </button>
      <button
        type="button"
        disabled={!month || pending !== null}
        onClick={() => run('pdf', () => downloadPdf(month, categories, type))}
        className="rounded-lg border border-surface-border px-3 py-1.5 text-xs text-neutral-300 transition hover:border-accent/50 disabled:cursor-not-allowed disabled:opacity-40"
      >
        {pending === 'pdf' ? 'Gerando PDF...' : 'Baixar PDF'}
      </button>
      {error ? <span className="text-xs text-red-400">{error}</span> : null}
    </div>
  )
}
