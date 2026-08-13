import { ONBOARDING_STEPS } from '../onboarding/steps'

const SHORTCUTS: { keys: string; description: string }[] = [
  { keys: 'Ctrl/Cmd + K', description: 'Abrir a paleta de comandos' },
  { keys: 'Esc', description: 'Fechar a paleta de comandos' },
  { keys: '↑ / ↓', description: 'Navegar pelos comandos' },
  { keys: 'Enter', description: 'Executar o comando selecionado' },
]

/** Authenticated-only help panel -- lives under src/dashboard/, part of
 * the lazy-loaded AppShell chunk, never src/public-bundle/ (confirmed
 * structurally the same way Fase 2 validated the auth/public split). */
export function HelpCenter({ onClose, onRestartTour }: { onClose: () => void; onRestartTour: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/60 p-4 py-12 print:hidden" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="help-center-title"
        className="w-full max-w-lg rounded-2xl border border-surface-border bg-surface-1 p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 id="help-center-title" className="text-lg font-semibold text-neutral-50">
            Central de ajuda
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Fechar"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-neutral-500 hover:bg-surface-2 hover:text-neutral-300"
          >
            ✕
          </button>
        </div>

        <section className="mb-6">
          <h3 className="mb-2 text-xs font-medium tracking-wide text-neutral-500 uppercase">Atalhos de teclado</h3>
          <ul className="space-y-1">
            {SHORTCUTS.map((s) => (
              <li key={s.keys} className="flex items-center justify-between text-sm">
                <span className="text-neutral-400">{s.description}</span>
                <kbd className="rounded border border-surface-border bg-surface-2 px-2 py-0.5 text-xs text-neutral-300">{s.keys}</kbd>
              </li>
            ))}
          </ul>
        </section>

        <section className="mb-6">
          <h3 className="mb-2 text-xs font-medium tracking-wide text-neutral-500 uppercase">O que dá para fazer aqui</h3>
          <ul className="space-y-2">
            {ONBOARDING_STEPS.map((s) => (
              <li key={s.title} className="text-sm">
                <p className="font-medium text-neutral-200">{s.title}</p>
                <p className="text-neutral-500">{s.description}</p>
              </li>
            ))}
          </ul>
        </section>

        <button
          type="button"
          onClick={onRestartTour}
          className="w-full rounded-lg border border-surface-border px-3 py-2 text-sm text-neutral-300 transition hover:border-accent/50"
        >
          Ver o tour de boas-vindas novamente
        </button>
      </div>
    </div>
  )
}
