/**
 * Persistent, dismiss-proof (by design -- see below) strip shown across the
 * whole dashboard while `isDemo` is active. Always visible, even in
 * presentation mode and print, so a demo screenshot/PDF can never be
 * mistaken for real financial data -- the one place this banner is
 * deliberately NOT `print:hidden` like the rest of the dashboard chrome.
 */
export function DemoModeBanner({ onExit }: { onExit: () => void }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-amber-400/30 bg-amber-400/10 px-4 py-2.5 text-sm">
      <div className="flex items-center gap-2 text-amber-200">
        <span aria-hidden>🧪</span>
        <span>
          Você está explorando com <strong className="font-semibold">dados de exemplo</strong> -- nada aqui é real.
        </span>
      </div>
      <button
        type="button"
        onClick={onExit}
        className="rounded-lg border border-amber-400/40 px-3 py-1 text-xs font-semibold text-amber-100 transition hover:bg-amber-400/20 print:hidden"
      >
        Enviar meus extratos reais
      </button>
    </div>
  )
}
