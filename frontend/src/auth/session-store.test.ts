import { beforeEach, describe, expect, it } from 'vitest'

import { getAccessToken, useSessionStore } from './session-store'

describe('session-store', () => {
  beforeEach(() => {
    useSessionStore.setState({ session: null })
    localStorage.clear()
  })

  it('getAccessToken returns null when there is no session', () => {
    expect(getAccessToken()).toBeNull()
  })

  it('getAccessToken returns the token for a session that has not expired', () => {
    useSessionStore.getState().setSession({
      accessToken: 'valid-jwt',
      email: 'user@example.com',
      workspaceId: 'ws-1',
      expiresAt: Date.now() + 60_000,
    })
    expect(getAccessToken()).toBe('valid-jwt')
  })

  it('getAccessToken returns null AND clears the session once expiresAt has passed', () => {
    // Security-relevant: an expired ANZ session must never be sent as a
    // Bearer token (guardrail #2 -- no independent renewal, it should just
    // fall back to the institutional block screen).
    useSessionStore.getState().setSession({
      accessToken: 'stale-jwt',
      email: 'user@example.com',
      workspaceId: 'ws-1',
      expiresAt: Date.now() - 1_000,
    })
    expect(getAccessToken()).toBeNull()
    expect(useSessionStore.getState().session).toBeNull()
  })

  it('clearSession resets to null', () => {
    useSessionStore.getState().setSession({ accessToken: 'x', email: 'a@b.com', workspaceId: 'w', expiresAt: Date.now() + 60_000 })
    useSessionStore.getState().clearSession()
    expect(useSessionStore.getState().session).toBeNull()
  })
})
