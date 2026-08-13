import { Navigate, useSearchParams } from 'react-router-dom'

import { HubBridgeGate } from '@/auth/HubBridgeGate'
import { getAccessToken } from '@/auth/session-store'
import { LandingPage } from '@/public-bundle/landing/LandingPage'

/**
 * The 3 real cases at `/`, per the entry-experience redesign:
 *
 * 1. `?token=...` present -> bridge it (HubBridgeGate). A REJECTED token
 *    (invalid/expired -- a genuine error, the person thought they had a
 *    working link) still lands on `/blocked/token`, from HubBridgeGate's
 *    own error handling -- that terse screen is now reserved for that one
 *    real error case, not for "never been here before".
 * 2. No token, but a still-valid persisted ANZ session -> straight to
 *    `/app`, no landing page in the way (a returning user should never
 *    see marketing copy again).
 * 3. No token, no session -> the real front door: LandingPage. Both "this
 *    is my first time" and "I'm not authenticated right now" collapse
 *    into this one case -- either way, the single correct next action is
 *    the same "Entrar com Syncron" CTA.
 */
export function RootRoute() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')

  if (token) return <HubBridgeGate token={token} />

  if (getAccessToken()) return <Navigate to="/app" replace />

  return <LandingPage />
}
