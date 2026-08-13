import { create } from 'zustand'
import { persist } from 'zustand/middleware'

/**
 * Holds ANZ's own short-lived session JWT -- never the raw Syncron token
 * (that's sent once to POST /auth/bridge and then discarded, see
 * use-hub-bridge.ts). Persisted to localStorage (not a cookie -- the
 * backend never sets one, see backend/app/access/security.py) so a page
 * reload doesn't force the user back through the Hub while the session is
 * still genuinely valid. There is no refresh token: once `expiresAt`
 * passes, the session is discarded and the user falls back to the
 * institutional block screen (PARTE 5.4) -- ANZ has no login of its own to
 * fall back to (guardrail #2).
 */
export interface AnzSession {
  accessToken: string
  email: string
  workspaceId: string
  expiresAt: number // epoch ms
}

interface SessionStore {
  session: AnzSession | null
  setSession: (session: AnzSession) => void
  clearSession: () => void
}

export const useSessionStore = create<SessionStore>()(
  persist(
    (set) => ({
      session: null,
      setSession: (session) => set({ session }),
      clearSession: () => set({ session: null }),
    }),
    {
      name: 'anz-finance-session',
      partialize: (state) => ({ session: state.session }),
      onRehydrateStorage: () => (state) => {
        if (state?.session && state.session.expiresAt <= Date.now()) {
          state.clearSession()
        }
      },
    },
  ),
)

export function getAccessToken(): string | null {
  const session = useSessionStore.getState().session
  if (!session) return null
  if (session.expiresAt <= Date.now()) {
    useSessionStore.getState().clearSession()
    return null
  }
  return session.accessToken
}
