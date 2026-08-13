import { useRef, useState } from 'react'

import { formatCurrency, formatDateBr } from '@/design-system/format'

import type { Transaction, TypeFilter } from '../types'
import { useSearch } from './hooks'

/**
 * Global search (Fase 6) -- distinct from `TransactionsTable`'s own search
 * box, which only filters the currently-selected month. This searches the
 * FULL uploaded history so a transaction can be found without knowing
 * which month it's in first; picking a result jumps the dashboard to that
 * transaction's month.
 *
 * `demoSource` (Fase 13): when provided, search runs entirely against this
 * local array instead of calling the real `/workspace/search` endpoint --
 * used in explore/demo mode, where there is no real backend workspace to
 * query. Real (non-demo) usage is unaffected: the prop is simply omitted.
 */
export function GlobalSearch({
  categories,
  type,
  onJumpToMonth,
  demoSource,
}: {
  categories: string[]
  type: TypeFilter
  onJumpToMonth: (month: string) => void
  demoSource?: (query: string, categories: string[], type: TypeFilter) => Transaction[]
}) {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [demoResults, setDemoResults] = useState<Transaction[]>([])
  const search = useSearch()
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const runSearch = (value: string) => {
    setQuery(value)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (!value.trim()) {
      setOpen(false)
      return
    }
    debounceRef.current = setTimeout(() => {
      if (demoSource) {
        setDemoResults(demoSource(value.trim(), categories, type))
      } else {
        search.mutate({ q: value.trim(), categories, type })
      }
      setOpen(true)
    }, 250)
  }

  const isPending = demoSource ? false : search.isPending
  const results = (demoSource ? demoResults : (search.data?.transactions ?? [])).slice(0, 8)

  return (
    <div className="relative w-full max-w-[180px] sm:max-w-xs">
      <input
        value={query}
        onChange={(e) => runSearch(e.target.value)}
        onFocus={() => query.trim() && setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        placeholder="Buscar em todo o histórico..."
        aria-label="Buscar transações em todo o histórico"
        className="w-full rounded-lg border border-surface-border bg-surface-2 px-3 py-1.5 text-sm text-neutral-200 placeholder:text-neutral-600"
      />

      {open ? (
        <div className="absolute top-full right-0 left-0 z-10 mt-1 max-h-80 overflow-y-auto rounded-lg border border-surface-border bg-surface-1 shadow-lg">
          {isPending ? <p className="p-3 text-xs text-neutral-500">Buscando...</p> : null}
          {!isPending && results.length === 0 ? <p className="p-3 text-xs text-neutral-500">Nenhum resultado.</p> : null}
          {results.map((t, i) => (
            <button
              key={i}
              type="button"
              onMouseDown={() => {
                onJumpToMonth(t.Mês)
                setOpen(false)
              }}
              className="flex w-full items-center justify-between gap-2 border-b border-surface-border/60 px-3 py-2 text-left text-xs hover:bg-surface-2"
            >
              <span className="min-w-0 truncate text-neutral-300">
                {formatDateBr(t.Data)} · {t.Descrição}
              </span>
              <span className={`shrink-0 font-medium ${t.Valor >= 0 ? 'text-accent' : 'text-red-400'}`}>{formatCurrency(t.Valor)}</span>
            </button>
          ))}
        </div>
      ) : null}
    </div>
  )
}
