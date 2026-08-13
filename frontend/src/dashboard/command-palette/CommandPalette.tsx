import { useEffect, useMemo, useRef, useState } from 'react'

export interface Command {
  id: string
  label: string
  section: string
  keywords?: string
  onRun: () => void
}

/**
 * Fase 8: Ctrl/Cmd+K command palette. Deliberately dumb about WHAT the
 * commands do -- `DashboardPage` owns the actual list/actions (tab
 * switches, presentation mode, export, snapshots, help) and passes it in,
 * so this component only knows how to filter/navigate/run a list.
 */
export function CommandPalette({ commands }: { commands: Command[] }) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [activeIndex, setActiveIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const isMod = e.metaKey || e.ctrlKey
      if (isMod && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setOpen((o) => !o)
      } else if (e.key === 'Escape') {
        setOpen(false)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  useEffect(() => {
    if (!open) return
    setQuery('')
    setActiveIndex(0)
    const id = setTimeout(() => inputRef.current?.focus(), 0)
    return () => clearTimeout(id)
  }, [open])

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase()
    if (!term) return commands
    return commands.filter((c) => `${c.label} ${c.section} ${c.keywords ?? ''}`.toLowerCase().includes(term))
  }, [commands, query])

  const run = (command: Command) => {
    command.onRun()
    setOpen(false)
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 pt-24 print:hidden" onClick={() => setOpen(false)}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Paleta de comandos"
        className="w-full max-w-lg overflow-hidden rounded-2xl border border-surface-border bg-surface-1 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <input
          ref={inputRef}
          aria-label="Buscar comandos"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            setActiveIndex(0)
          }}
          onKeyDown={(e) => {
            if (e.key === 'ArrowDown') {
              e.preventDefault()
              setActiveIndex((i) => Math.min(i + 1, filtered.length - 1))
            } else if (e.key === 'ArrowUp') {
              e.preventDefault()
              setActiveIndex((i) => Math.max(i - 1, 0))
            } else if (e.key === 'Enter' && filtered[activeIndex]) {
              run(filtered[activeIndex])
            }
          }}
          placeholder="Digite um comando ou pesquise..."
          className="w-full border-b border-surface-border bg-transparent px-4 py-3 text-sm text-neutral-100 outline-none placeholder:text-neutral-600"
        />
        <div className="max-h-80 overflow-y-auto p-2">
          {filtered.length === 0 ? <p className="p-3 text-sm text-neutral-500">Nenhum comando encontrado.</p> : null}
          {filtered.map((c, i) => (
            <button
              key={c.id}
              type="button"
              onMouseEnter={() => setActiveIndex(i)}
              onClick={() => run(c)}
              className={`flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm transition ${
                i === activeIndex ? 'bg-accent-soft text-accent' : 'text-neutral-300'
              }`}
            >
              <span>{c.label}</span>
              <span className="text-xs text-neutral-600">{c.section}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
