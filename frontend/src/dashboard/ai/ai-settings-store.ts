import { create } from 'zustand'

/**
 * Fase 5's provider/model/own-key selection. Deliberately a PLAIN zustand
 * store -- no `persist` middleware, unlike `auth/session-store.ts`. A
 * user's own API key (PARTE 6.2) must never reach `localStorage`; keeping
 * it in unpersisted memory means it evaporates on tab close/reload by
 * construction, not by discipline at each call site.
 */
interface AiSettingsState {
  provider: string
  model: string | null
  useOwnKey: boolean
  ownApiKey: string
  setProvider: (provider: string) => void
  setModel: (model: string | null) => void
  setUseOwnKey: (useOwnKey: boolean) => void
  setOwnApiKey: (ownApiKey: string) => void
}

export const useAiSettingsStore = create<AiSettingsState>((set) => ({
  provider: 'groq',
  model: null,
  useOwnKey: false,
  ownApiKey: '',
  setProvider: (provider) => set({ provider, model: null }),
  setModel: (model) => set({ model }),
  setUseOwnKey: (useOwnKey) => set({ useOwnKey, ownApiKey: '' }),
  setOwnApiKey: (ownApiKey) => set({ ownApiKey }),
}))

/** The three fields every AI-touching call (upload/test-connection/ask) needs. */
export function currentAiSelection() {
  const s = useAiSettingsStore.getState()
  return { provider: s.provider, model: s.model, api_key: s.useOwnKey && s.ownApiKey ? s.ownApiKey : null }
}
