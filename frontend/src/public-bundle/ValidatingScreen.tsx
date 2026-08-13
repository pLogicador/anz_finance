/** PARTE 5.6 state 1 -- pure transient UI, no backend counterpart. */
export function ValidatingScreen() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-950 text-neutral-100">
      <div className="flex flex-col items-center gap-4">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-neutral-700 border-t-neutral-100" />
        <p className="text-sm text-neutral-400">Validando acesso...</p>
      </div>
    </div>
  )
}
