import { env } from '@/lib/env'

import { BlockScreen } from './BlockScreen'

/**
 * PARTE 5.6 state 3 -- deliberately different copy/icon from
 * InstitutionalBlockScreen (token invalid) even though both fully block
 * access, per the spec's requirement that these be visibly distinct
 * screens, not the same "sessão expirada" message for two different
 * reasons.
 */
export function PlanExpiredScreen() {
  return (
    <BlockScreen
      icon="⏳"
      title="Seu plano Syncron expirou"
      subtitle="O acesso ao ANZ Finance depende de um plano ativo na Syncron. Renove seu plano no Syncron Hub para voltar a usar o painel."
      action={
        <a
          href={`${env.syncronHubUrl}/company/planos.html`}
          className="inline-flex w-full items-center justify-center rounded-lg bg-neutral-50 px-4 py-2.5 text-sm font-medium text-neutral-900 transition hover:bg-neutral-200"
        >
          Ver planos na Syncron
        </a>
      }
    />
  )
}
