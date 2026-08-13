import { useState } from 'react'

import type { TypeFilter } from '../types'
import { useCreateSnapshot, useDeleteSnapshot, useSnapshots } from './hooks'

/**
 * Filter-combination bookmarks (PARTE 6.6) -- saved on the backend's
 * workspace TTL entry (see backend/app/routes/snapshots.py), so they
 * survive tab switches/reloads for the rest of this session but vanish
 * with the rest of the workspace data, same as everything else here.
 */
export function SnapshotsBar({
  month,
  categories,
  type,
  onApply,
}: {
  month: string
  categories: string[]
  type: TypeFilter
  onApply: (snapshot: { month: string; categories: string[]; type: TypeFilter }) => void
}) {
  const snapshotsQuery = useSnapshots(true)
  const createSnapshot = useCreateSnapshot()
  const deleteSnapshot = useDeleteSnapshot()
  const [label, setLabel] = useState('')
  const [showForm, setShowForm] = useState(false)

  const snapshots = snapshotsQuery.data?.snapshots ?? []

  const handleSave = () => {
    createSnapshot.mutateAsync({ label, month, categories, type }).then(() => {
      setLabel('')
      setShowForm(false)
    })
  }

  return (
    <div className="flex flex-wrap items-center gap-2 print:hidden">
      {snapshots.map((s) => (
        <span key={s.id} className="flex items-center gap-1 rounded-full border border-surface-border bg-surface-2 py-1 pr-1 pl-2.5 text-xs">
          <button type="button" onClick={() => onApply({ month: s.month, categories: s.categories, type: s.type as TypeFilter })} className="text-neutral-300 hover:text-accent">
            {s.label}
          </button>
          <button
            type="button"
            aria-label={`Remover snapshot ${s.label}`}
            onClick={() => deleteSnapshot.mutate(s.id)}
            className="flex h-6 w-6 items-center justify-center rounded-full text-neutral-600 hover:text-red-400"
          >
            ×
          </button>
        </span>
      ))}

      {showForm ? (
        <div className="flex items-center gap-1">
          <input
            autoFocus
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSave()}
            placeholder="Nome do snapshot"
            className="rounded-lg border border-surface-border bg-surface-2 px-2 py-1 text-xs text-neutral-200"
          />
          <button type="button" onClick={handleSave} disabled={createSnapshot.isPending} className="text-xs text-accent">
            Salvar
          </button>
          <button type="button" onClick={() => setShowForm(false)} className="text-xs text-neutral-500">
            Cancelar
          </button>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setShowForm(true)}
          disabled={!month}
          className="rounded-full border border-dashed border-surface-border px-2.5 py-1 text-xs text-neutral-500 transition hover:border-accent/50 hover:text-neutral-300 disabled:opacity-40"
        >
          + Salvar view atual
        </button>
      )}
    </div>
  )
}
