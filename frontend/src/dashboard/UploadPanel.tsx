import { lazy, Suspense, useRef, useState } from 'react'

import { AccessApiError } from '@/auth/access-errors'

import { AiSettingsPanel } from './ai/AiSettingsPanel'
import { currentAiSelection } from './ai/ai-settings-store'
import { useUploadStatements } from './hooks'

// Fase 9 performance pass: most sessions use the default OFX tab -- the
// CSV import wizard's own preview/mapping state shouldn't be paid for
// unless the user actually clicks "Importar CSV".
const CsvImportPanel = lazy(() => import('./import/CsvImportPanel').then((m) => ({ default: m.CsvImportPanel })))

/**
 * The only ingestion flow in the app -- matches legacy's upload capability
 * (multi-file .ofx, one or more accepted) but surfaces per-file
 * success/failure (a real gap the legacy app had: it only `print()`-ed
 * parse failures server-side, see backend/app/pipeline/ofx_parser.py).
 * Fase 7 adds a second ingestion path (CSV, with column-mapping) as a tab
 * alongside the original OFX flow.
 */
export function UploadPanel({ onUploaded }: { onUploaded: () => void }) {
  const [mode, setMode] = useState<'ofx' | 'csv'>('ofx')
  const inputRef = useRef<HTMLInputElement>(null)
  const [selected, setSelected] = useState<File[]>([])
  const upload = useUploadStatements()

  const handleSubmit = () => {
    if (selected.length === 0) return
    const selection = currentAiSelection()
    const fields: Record<string, string> = { provider: selection.provider }
    if (selection.model) fields.model = selection.model
    if (selection.api_key) fields.api_key = selection.api_key

    // `mutateAsync` + `.then()`, not `.mutate(files, {onSuccess})` -- the
    // callback-on-mutate-call pattern proved unreliable elsewhere in this
    // app under this environment's React setup (see the detailed comment
    // in src/auth/HubBridgeGate.tsx: the async call itself completed
    // correctly, confirmed server-side, but the inline onSuccess callback
    // sometimes silently never ran, leaving the UI stuck showing stale
    // state). Awaiting the promise directly avoids depending on that
    // callback mechanism.
    upload.mutateAsync({ files: selected, fields }).then(onUploaded, () => {
      // swallow -- upload.isError/upload.error (read reactively below) already surfaces this to the user
    })
  }

  return (
    <div className="mx-auto flex max-w-xl flex-col items-center gap-4 rounded-2xl border border-surface-border bg-surface-1 px-8 py-12 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-accent-soft text-2xl">📂</div>
      <h2 className="text-lg font-semibold text-neutral-50">Envie seus extratos</h2>
      <p className="max-w-sm text-sm text-neutral-500">
        Envie extratos do seu banco (.ofx) ou importe uma planilha CSV para gerar o painel financeiro. Nada fica salvo
        permanentemente -- os dados somem quando a sessão termina.
      </p>

      <div className="flex rounded-lg border border-surface-border bg-surface-2 p-0.5">
        <button
          type="button"
          onClick={() => setMode('ofx')}
          className={`rounded-md px-3 py-1 text-xs font-medium transition ${mode === 'ofx' ? 'bg-accent-strong text-neutral-950' : 'text-neutral-400 hover:text-neutral-200'}`}
        >
          Extrato (.ofx)
        </button>
        <button
          type="button"
          onClick={() => setMode('csv')}
          className={`rounded-md px-3 py-1 text-xs font-medium transition ${mode === 'csv' ? 'bg-accent-strong text-neutral-950' : 'text-neutral-400 hover:text-neutral-200'}`}
        >
          Importar CSV
        </button>
      </div>

      {mode === 'ofx' ? (
        <>
          <input
            ref={inputRef}
            type="file"
            accept=".ofx"
            multiple
            className="hidden"
            onChange={(e) => setSelected(Array.from(e.target.files ?? []))}
          />

          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="w-full rounded-lg border border-surface-border bg-surface-2 px-4 py-2.5 text-sm font-medium text-neutral-200 transition hover:border-accent/50"
          >
            {selected.length > 0 ? `${selected.length} arquivo(s) selecionado(s)` : 'Selecionar arquivos .ofx'}
          </button>

          <div className="w-full text-left">
            <AiSettingsPanel compact />
          </div>

          <button
            type="button"
            disabled={selected.length === 0 || upload.isPending}
            onClick={handleSubmit}
            className="w-full rounded-lg bg-accent-strong px-4 py-2.5 text-sm font-semibold text-neutral-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {upload.isPending ? 'Processando extratos...' : 'Gerar painel financeiro'}
          </button>

          {upload.isError ? (
            <p className="text-sm text-red-400">
              {upload.error instanceof AccessApiError ? upload.error.message : 'Não foi possível processar os extratos. Tente novamente.'}
            </p>
          ) : null}

          {upload.isSuccess ? (
            <div className="w-full space-y-1 text-left text-xs text-neutral-500">
              {upload.data.files.map((file) => (
                <div key={file.filename} className="flex items-center justify-between">
                  <span className="truncate">{file.filename}</span>
                  <span className={file.status === 'ok' ? 'text-accent' : 'text-red-400'}>
                    {file.status === 'ok' ? `${file.rows_parsed} transações` : file.error ?? 'Falhou'}
                  </span>
                </div>
              ))}
            </div>
          ) : null}
        </>
      ) : (
        <Suspense fallback={<p className="text-sm text-neutral-500">Carregando...</p>}>
          <CsvImportPanel onImported={onUploaded} />
        </Suspense>
      )}
    </div>
  )
}
