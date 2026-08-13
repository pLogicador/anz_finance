import { useState } from 'react'

import { UploadPanel } from './UploadPanel'

const VALUE_POINTS = [
  { icon: '📊', text: 'KPIs, tendências e mapa de gastos gerados automaticamente' },
  { icon: '🤖', text: 'Categorização por IA e um assistente para perguntar sobre seus dados' },
  { icon: '🔒', text: 'Nada fica salvo -- os dados somem quando a sessão termina' },
] as const

/**
 * Fase 13 -- the real first screen an authenticated-but-dataless user sees
 * (replaces `UploadPanel` being rendered bare). Before this, arriving via
 * Syncron with no prior upload dropped straight into a file-picker card
 * with no other option -- someone who just wanted to look around had
 * nothing to look around *at*. This adds an explicit fork: upload real
 * statements (unchanged `UploadPanel`, just one level deeper now) or
 * explore the same dashboard UI populated with example data first.
 * `onEnterDemo` is the only new capability this introduces; everything
 * upload-related is delegated to the existing, untouched `UploadPanel`.
 */
export function WelcomeHub({
  onUploaded,
  onEnterDemo,
  initialPath = 'choose',
}: {
  onUploaded: () => void
  onEnterDemo: () => void
  /** `showUpload` (DashboardPage) already means "user explicitly asked to send new files" (via the header button, command palette, or exiting demo mode) -- when that's how we got here, skip straight past the chooser instead of making them click "Enviar meus extratos" a second time. */
  initialPath?: 'choose' | 'upload'
}) {
  const [path, setPath] = useState<'choose' | 'upload'>(initialPath)

  if (path === 'upload') {
    return (
      <div className="mx-auto flex max-w-xl flex-col items-center gap-3">
        <button type="button" onClick={() => setPath('choose')} className="self-start text-xs text-neutral-500 transition hover:text-neutral-300">
          ← Voltar
        </button>
        <UploadPanel onUploaded={onUploaded} />
      </div>
    )
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col items-center gap-8 text-center">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold text-neutral-50">Bem-vindo ao ANZ Finance</h1>
        <p className="mx-auto max-w-md text-sm text-neutral-500">Envie seus extratos para gerar o seu painel real, ou explore o produto primeiro com dados de exemplo.</p>
      </div>

      <div className="grid w-full gap-4 sm:grid-cols-2">
        <button
          type="button"
          onClick={() => setPath('upload')}
          className="group flex flex-col items-center gap-3 rounded-2xl border border-surface-border bg-surface-1 px-6 py-8 text-center transition hover:border-accent/50 hover:bg-surface-2"
        >
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-accent-soft text-2xl">📂</span>
          <span className="text-sm font-semibold text-neutral-50">Enviar meus extratos</span>
          <span className="text-xs text-neutral-500">Extrato bancário (.ofx) ou planilha CSV -- gera o seu painel real em segundos.</span>
        </button>

        <button
          type="button"
          onClick={onEnterDemo}
          className="group flex flex-col items-center gap-3 rounded-2xl border border-dashed border-surface-border bg-surface-1/60 px-6 py-8 text-center transition hover:border-accent/50 hover:bg-surface-2"
        >
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-surface-2 text-2xl">🧭</span>
          <span className="text-sm font-semibold text-neutral-50">Explorar com dados de exemplo</span>
          <span className="text-xs text-neutral-500">Veja o painel completo populado com dados fictícios, sem enviar nada ainda.</span>
        </button>
      </div>

      <ul className="flex flex-col gap-2 text-left text-xs text-neutral-500 sm:flex-row sm:flex-wrap sm:justify-center sm:gap-x-6 sm:gap-y-2">
        {VALUE_POINTS.map((point) => (
          <li key={point.text} className="flex items-center gap-1.5">
            <span aria-hidden>{point.icon}</span>
            <span>{point.text}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
