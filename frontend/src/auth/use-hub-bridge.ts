import { useMutation } from '@tanstack/react-query'

import { useSessionStore } from '@/auth/session-store'
import { apiRequest } from '@/lib/api-client'

interface BridgeResponse {
  access_token: string
  token_type: string
  expires_at: string
  workspace_id: string
  user: { email: string }
}

/**
 * The one and only call that sends the raw Syncron token anywhere. Called
 * exactly once per token (see HubBridgeGate.tsx), never retried
 * automatically on failure (a failed bridge means one of the 3 real
 * backend states -- token invalid, plan expired, service down -- not a
 * transient blip worth silently retrying against the user's plan status).
 */
export function useHubBridge() {
  const setSession = useSessionStore((s) => s.setSession)

  return useMutation({
    mutationFn: (token: string) => apiRequest<BridgeResponse>('/auth/bridge', 'POST', { auth: false, body: { token } }),
    onSuccess: (data) => {
      setSession({
        accessToken: data.access_token,
        email: data.user.email,
        workspaceId: data.workspace_id,
        expiresAt: new Date(data.expires_at).getTime(),
      })
    },
  })
}
