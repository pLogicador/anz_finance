import { useRef, useState } from 'react'

import { AiSettingsPanel } from '../ai/AiSettingsPanel'
import { currentAiSelection } from '../ai/ai-settings-store'
import { usePreviewCsv, useCommitCsv } from './hooks'

/**
 * CSV import with preview + column mapping (Fase 7, PARTE 6.7). Unlike OFX
 * (a fixed, known format), a CSV's columns can be named anything -- so the
 * flow is: pick a file -> see its real headers + a few sample rows -> map
 * "which column is the date/value/description" -> commit. The backend
 * appends the result to whatever's already in the session rather than
 * replacing it (see backend/app/routes/import_csv.py's docstring).
 */
export function CsvImportPanel({ onImported }: { onImported: () => void }) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [dateColumn, setDateColumn] = useState('')
  const [valorColumn, setValorColumn] = useState('')
  const [descriptionColumn, setDescriptionColumn] = useState('')

  const preview = usePreviewCsv()
  const commit = useCommitCsv()

  const handleFileSelected = (selected: File) => {
    setFile(selected)
    preview.mutateAsync(selected).then((data) => {
      setDateColumn(data.columns[0] ?? '')
      setValorColumn(data.columns[1] ?? data.columns[0] ?? '')
      setDescriptionColumn(data.columns[2] ?? data.columns[0] ?? '')
    })
  }

  const handleCommit = () => {
    if (!file) return
    const selection = currentAiSelection()
    commit
      .mutateAsync({
        file,
        dateColumn,
        valorColumn,
        descriptionColumn,
        provider: selection.provider,
        model: selection.model,
        api_key: selection.api_key,
      })
      .then(onImported, () => {
        // swallow -- commit.isError/commit.error (read reactively below) already surfaces this
      })
  }

  const columns = preview.data?.columns ?? []

  return (
    <div className="w-full space-y-4 text-left">
      <input
        ref={inputRef}
        type="file"
        accept=".csv"
        className="hidden"
        onChange={(e) => {
          const selected = e.target.files?.[0]
          if (selected) handleFileSelected(selected)
        }}
      />

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="w-full rounded-lg border border-surface-border bg-surface-2 px-4 py-2.5 text-center text-sm font-medium text-neutral-200 transition hover:border-accent/50"
      >
        {file ? file.name : 'Selecionar arquivo .csv'}
      </button>

      {preview.isPending ? <p className="text-sm text-neutral-500">Lendo arquivo...</p> : null}
      {preview.isError ? <p className="text-sm text-red-400">{preview.error instanceof Error ? preview.error.message : 'Não foi possível ler o CSV.'}</p> : null}

      {preview.data ? (
        <div className="space-y-3 rounded-xl border border-surface-border bg-surface-2 p-3">
          <p className="text-xs text-neutral-500">
            {preview.data.row_count} linha(s) encontradas. Selecione qual coluna corresponde a cada campo:
          </p>

          <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
            <label className="text-xs text-neutral-400">
              Data
              <select value={dateColumn} onChange={(e) => setDateColumn(e.target.value)} className="mt-1 w-full rounded-lg border border-surface-border bg-surface-1 px-2 py-1.5 text-sm text-neutral-200">
                {columns.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-xs text-neutral-400">
              Valor
              <select value={valorColumn} onChange={(e) => setValorColumn(e.target.value)} className="mt-1 w-full rounded-lg border border-surface-border bg-surface-1 px-2 py-1.5 text-sm text-neutral-200">
                {columns.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-xs text-neutral-400">
              Descrição
              <select value={descriptionColumn} onChange={(e) => setDescriptionColumn(e.target.value)} className="mt-1 w-full rounded-lg border border-surface-border bg-surface-1 px-2 py-1.5 text-sm text-neutral-200">
                {columns.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {preview.data.sample_rows.length > 0 ? (
            <div className="overflow-x-auto rounded-lg border border-surface-border">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="text-neutral-500">
                    {columns.map((c) => (
                      <th key={c} className="px-2 py-1 font-medium">
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.data.sample_rows.map((row, i) => (
                    <tr key={i} className="border-t border-surface-border/60 text-neutral-400">
                      {columns.map((c) => (
                        <td key={c} className="px-2 py-1">
                          {String(row[c] ?? '')}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}

          <AiSettingsPanel compact />

          <button
            type="button"
            disabled={commit.isPending || !dateColumn || !valorColumn || !descriptionColumn}
            onClick={handleCommit}
            className="w-full rounded-lg bg-accent-strong px-4 py-2.5 text-sm font-semibold text-neutral-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {commit.isPending ? 'Importando...' : 'Importar transações'}
          </button>

          {commit.isError ? <p className="text-sm text-red-400">{commit.error instanceof Error ? commit.error.message : 'Falha ao importar.'}</p> : null}
        </div>
      ) : null}
    </div>
  )
}
