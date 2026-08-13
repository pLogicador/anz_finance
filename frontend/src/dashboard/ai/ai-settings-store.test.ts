import { beforeEach, describe, expect, it } from 'vitest'

import { currentAiSelection, useAiSettingsStore } from './ai-settings-store'

describe('ai-settings-store', () => {
  beforeEach(() => {
    useAiSettingsStore.setState({ provider: 'groq', model: null, useOwnKey: false, ownApiKey: '' })
  })

  it('defaults to groq with no model override and no own key sent', () => {
    expect(currentAiSelection()).toEqual({ provider: 'groq', model: null, api_key: null })
  })

  it('never includes the own key in the selection while useOwnKey is off, even if a key was typed and left behind', () => {
    // Security-relevant: PARTE 6.2 requires the user's own key to be
    // session-only and never sent unless explicitly opted in for THIS
    // request. Toggling the checkbox off must not leave a stale key
    // reachable via currentAiSelection().
    useAiSettingsStore.getState().setOwnApiKey('sk-should-not-be-sent')
    useAiSettingsStore.getState().setUseOwnKey(false)
    expect(currentAiSelection().api_key).toBeNull()
  })

  it('includes the own key only when useOwnKey is on and a key is present', () => {
    useAiSettingsStore.getState().setUseOwnKey(true)
    useAiSettingsStore.getState().setOwnApiKey('sk-real-key')
    expect(currentAiSelection().api_key).toBe('sk-real-key')
  })

  it('setUseOwnKey(true) with no key typed yet still sends null, not an empty string', () => {
    useAiSettingsStore.getState().setUseOwnKey(true)
    expect(currentAiSelection().api_key).toBeNull()
  })

  it('switching provider resets the model override (a model id from the old provider would be invalid for the new one)', () => {
    useAiSettingsStore.getState().setModel('llama-3.3-70b-versatile')
    useAiSettingsStore.getState().setProvider('openai')
    expect(useAiSettingsStore.getState().model).toBeNull()
  })

  it('setUseOwnKey clears any previously-typed key when toggled off', () => {
    useAiSettingsStore.getState().setOwnApiKey('sk-typed')
    useAiSettingsStore.getState().setUseOwnKey(false)
    expect(useAiSettingsStore.getState().ownApiKey).toBe('')
  })
})
