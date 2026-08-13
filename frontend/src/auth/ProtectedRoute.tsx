import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'

import { getAccessToken } from '@/auth/session-store'

/**
 * Guards the authenticated tree. No valid ANZ session -> back to `/`,
 * which (per RootRoute.tsx) means the institutional block screen, since by
 * definition there's no fresh `?token=` here either. This is also the path
 * an expired ANZ JWT takes -- see guardrail #2 in the plan: an expired
 * session has no self-serve renewal, only a way back to Syncron.
 */
export function ProtectedRoute({ children }: { children: ReactNode }) {
  if (!getAccessToken()) return <Navigate to="/" replace />
  return <>{children}</>
}
