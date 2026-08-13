import { env } from '@/lib/env'

import { BlockScreen } from './BlockScreen'

/**
 * Narrowed scope (entry-experience redesign): this used to be the catch-all
 * for "not authenticated, for any reason" -- now it's reserved for one
 * specific real error, a `?token=` that WAS present but got rejected
 * (invalid/expired). A brand-new visitor with no token at all sees
 * `LandingPage` instead (see RootRoute.tsx) -- showing this terse,
 * marketing-free screen to someone who's never even heard of the product
 * would fail the "understand it in 5 seconds" goal the landing page exists
 * for.
 */
export function InstitutionalBlockScreen() {
  return (
    <BlockScreen
      icon="🔒"
      title="Acesso pelo Syncron Hub"
      subtitle="O ANZ Finance é um serviço do ecossistema Syncron. Acesse pelo Syncron Hub para continuar."
      action={
        <a
          href={env.syncronHubUrl}
          className="inline-flex w-full items-center justify-center rounded-lg bg-neutral-50 px-4 py-2.5 text-sm font-medium text-neutral-900 transition hover:bg-neutral-200"
        >
          Ir para o Syncron Hub
        </a>
      }
    />
  )
}
