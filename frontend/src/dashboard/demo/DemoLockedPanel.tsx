/**
 * Shown instead of `AnomaliesPanel`/`ComparePanel`/`AiAssistantPanel` while
 * `isDemo` is active. Those three genuinely call the backend (anomaly
 * detection over the real uploaded history, LLM Q&A) -- there is no real
 * workspace behind a demo session, so rendering them as-is would either
 * silently no-op (`enabled={false}`, confusing -- "nenhuma anomalia
 * encontrada" would read as a real finding, not as "not available yet") or
 * hit the backend against a workspace that doesn't exist. A clear, honest
 * locked state that still explains the feature (rather than hiding the tab
 * entirely) is the more useful middle ground for someone deciding whether
 * to upload their real statements.
 */
export function DemoLockedPanel({ title, description, onUpload }: { title: string; description: string; onUpload: () => void }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-surface-border bg-surface-1/40 px-6 py-14 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-surface-2 text-xl" aria-hidden>
        🔒
      </span>
      <h3 className="text-sm font-semibold text-neutral-100">{title}</h3>
      <p className="max-w-sm text-sm text-neutral-500">{description}</p>
      <button
        type="button"
        onClick={onUpload}
        className="mt-1 rounded-lg bg-accent-strong px-4 py-2 text-xs font-semibold text-neutral-950 transition hover:brightness-110"
      >
        Enviar meus extratos
      </button>
    </div>
  )
}
