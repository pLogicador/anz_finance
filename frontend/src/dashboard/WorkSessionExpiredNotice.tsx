/**
 * PARTE 5.6 state 5 -- shown INSIDE the authenticated app shell, never as a
 * route-level block screen: the ANZ session (JWT) is still valid here,
 * only the PARTE-4 workspace TTL entry (uploaded/classified data) expired.
 * "Retomar sem sair do produto" means re-upload, not re-auth -- there is
 * no Syncron re-validation involved in dismissing this.
 *
 * Not wired to a real trigger yet (no workspace data exists until Fase 3);
 * this component is ready for `apiRequest` calls that surface a
 * `work_session_expired` error_code to render it in place of dashboard
 * content.
 */
export function WorkSessionExpiredNotice({ onReupload }: { onReupload: () => void }) {
  return (
    <div className="mx-auto flex max-w-md flex-col items-center gap-3 rounded-2xl border border-neutral-800 bg-neutral-900/60 p-8 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-neutral-800 text-xl">🗂️</div>
      <h2 className="text-lg font-semibold text-neutral-50">Sua sessão de trabalho expirou</h2>
      <p className="text-sm leading-relaxed text-neutral-400">
        Os extratos processados não ficam salvos por muito tempo. Você continua conectado -- é só enviar os arquivos de novo
        para continuar.
      </p>
      <button
        type="button"
        onClick={onReupload}
        className="mt-2 inline-flex items-center justify-center rounded-lg bg-neutral-50 px-4 py-2 text-sm font-medium text-neutral-900 transition hover:bg-neutral-200"
      >
        Enviar extratos novamente
      </button>
    </div>
  )
}
