import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

import { AccessApiError, AccessErrorCode } from '@/auth/access-errors'
import { useHubBridge } from '@/auth/use-hub-bridge'
import { ValidatingScreen } from '@/public-bundle/ValidatingScreen'

const ERROR_ROUTES: Record<AccessErrorCode, string> = {
  [AccessErrorCode.PLAN_EXPIRED]: '/blocked/plan-expired',
  [AccessErrorCode.TOKEN_INVALID_OR_MISSING]: '/blocked/token',
  [AccessErrorCode.AUTH_SERVICE_UNAVAILABLE]: '/blocked/service-unavailable',
  [AccessErrorCode.WORK_SESSION_EXPIRED]: '/blocked/token', // never produced by the bridge itself
}

/**
 * Reads the raw Syncron token (passed in, already pulled off `?token=` by
 * the caller) and exchanges it exactly once. `replace: true` on every
 * navigation out of here is what removes `?token=...` from the address bar
 * (PARTE 5.5) -- there is no separate `history.replaceState` call needed,
 * the SPA route change accomplishes it.
 *
 * `dispatchedTokenRef` guards against React StrictMode's deliberate
 * mount->cleanup->mount double-invocation of effects in development: an
 * earlier version of this file fired the bridge exchange TWICE for the
 * same token, minting two independent sessions (two different
 * workspace_ids -- see backend/app/access/security.py's
 * `create_session_token`). Confirmed via backend logs showing two
 * `POST /auth/bridge` calls from a single navigation.
 *
 * Uses `mutateAsync`'s own promise (`.then`/`.catch`) to drive navigation,
 * instead of a second effect watching `useMutation`'s reactive
 * `isSuccess`/`isError` state. That reactive-state approach was tried
 * first and proved unreliable here under StrictMode's dev-mode
 * double-render: the session was correctly established (confirmed via
 * localStorage) but the component never observed `isSuccess` flip to true
 * in a later render, so navigate() never fired and the screen stayed stuck
 * on "Validando acesso...". A similar attempt with a `cancelled` flag set
 * from an effect cleanup function had the same failure mode -- StrictMode
 * runs that cleanup immediately after the first (simulated) mount, so by
 * the time the real request resolved, `cancelled` was already `true` and
 * the result was silently discarded. Acting directly off the promise
 * continuation avoids depending on a later render or a cleanup-derived
 * flag to learn the outcome at all.
 */
export function HubBridgeGate({ token }: { token: string }) {
  const navigate = useNavigate()
  const bridge = useHubBridge()
  const dispatchedTokenRef = useRef<string | null>(null)

  useEffect(() => {
    if (dispatchedTokenRef.current === token) return
    dispatchedTokenRef.current = token

    bridge
      .mutateAsync(token)
      .then(() => {
        navigate('/app', { replace: true })
      })
      .catch((error: unknown) => {
        const route =
          error instanceof AccessApiError ? ERROR_ROUTES[error.errorCode] : ERROR_ROUTES[AccessErrorCode.AUTH_SERVICE_UNAVAILABLE]
        navigate(route, { replace: true, state: { token } })
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  return <ValidatingScreen />
}
