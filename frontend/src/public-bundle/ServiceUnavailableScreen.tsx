import { BlockScreen } from './BlockScreen'

export function ServiceUnavailableScreen({ onRetry }: { onRetry: () => void }) {
  return (
    <BlockScreen
      icon="⚠️"
      title="Não foi possível confirmar seu acesso"
      subtitle="O serviço de autenticação da Syncron está indisponível no momento. Isso costuma se resolver sozinho em instantes."
      action={
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex w-full items-center justify-center rounded-lg bg-neutral-50 px-4 py-2.5 text-sm font-medium text-neutral-900 transition hover:bg-neutral-200"
        >
          Tentar novamente
        </button>
      }
    />
  )
}
