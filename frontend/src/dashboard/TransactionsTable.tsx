import { useMemo, useState } from 'react'

import { formatCurrency, formatDateBr } from '@/design-system/format'

import { EmptyState } from './EmptyState'
import type { Transaction } from './types'

const PAGE_SIZE = 25

export function TransactionsTable({ transactions }: { transactions: Transaction[] }) {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(0)

  const filtered = useMemo(() => {
    const sorted = [...transactions].sort((a, b) => b.Data.localeCompare(a.Data))
    if (!search.trim()) return sorted
    const term = search.toLowerCase()
    return sorted.filter((t) => t.Descrição.toLowerCase().includes(term) || t.Categorias.toLowerCase().includes(term))
  }, [transactions, search])

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const currentPage = Math.min(page, totalPages - 1)
  const pageItems = filtered.slice(currentPage * PAGE_SIZE, (currentPage + 1) * PAGE_SIZE)

  if (transactions.length === 0) {
    return <EmptyState icon="🔍" title="Nenhuma transação para exibir" subtitle="Ajuste os filtros ou envie novos extratos." />
  }

  return (
    <div className="rounded-2xl border border-surface-border bg-surface-1">
      <div className="flex items-center gap-3 border-b border-surface-border p-3">
        <input
          value={search}
          onChange={(e) => {
            setSearch(e.target.value)
            setPage(0)
          }}
          placeholder="Pesquisar transações..."
          className="w-full rounded-lg border border-surface-border bg-surface-2 px-3 py-1.5 text-sm text-neutral-200 placeholder:text-neutral-600"
        />
      </div>

      {filtered.length === 0 ? (
        <div className="p-6">
          <EmptyState icon="🔍" title="Nenhum resultado para essa busca" subtitle={`Nenhuma transação corresponde a "${search}". Tente outro termo.`} />
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-xs tracking-wide text-neutral-500 uppercase">
                  <th className="px-4 py-2 font-medium">Data</th>
                  <th className="px-4 py-2 font-medium">Descrição</th>
                  <th className="px-4 py-2 font-medium">Categoria</th>
                  <th className="px-4 py-2 font-medium">Tipo</th>
                  <th className="px-4 py-2 text-right font-medium">Valor</th>
                </tr>
              </thead>
              <tbody>
                {pageItems.map((t, i) => (
                  <tr key={`${t.Data}-${i}`} className="border-t border-surface-border/60">
                    <td className="px-4 py-2 whitespace-nowrap text-neutral-400">{formatDateBr(t.Data)}</td>
                    <td className="px-4 py-2 text-neutral-200">{t.Descrição}</td>
                    <td className="px-4 py-2 text-neutral-400">{t.Categorias}</td>
                    <td className="px-4 py-2 text-neutral-400">{t.Valor >= 0 ? 'Receita' : 'Despesa'}</td>
                    <td className={`px-4 py-2 text-right font-medium whitespace-nowrap ${t.Valor >= 0 ? 'text-accent' : 'text-red-400'}`}>
                      {formatCurrency(t.Valor)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between border-t border-surface-border p-3 text-xs text-neutral-500">
            <button type="button" disabled={currentPage === 0} onClick={() => setPage((p) => p - 1)} className="disabled:opacity-30">
              ← Anterior
            </button>
            <span>
              Página {currentPage + 1} de {totalPages} · {filtered.length} transações
            </span>
            <button type="button" disabled={currentPage >= totalPages - 1} onClick={() => setPage((p) => p + 1)} className="disabled:opacity-30">
              Próxima →
            </button>
          </div>
        </>
      )}
    </div>
  )
}
