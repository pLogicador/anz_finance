import { useState } from 'react'

import { useAiSettingsStore } from './ai-settings-store'
import { useAiModels, useTestAiConnection } from './hooks'

/**
 * Provider/model picker + "usar minha própria chave" (PARTE 6.2). Used both
 * on the upload screen (decides which model classifies transactions) and
 * inside the assistant panel (decides which model answers questions) --
 * same shared, unpersisted selection (`ai-settings-store.ts`), since both
 * are "which AI backs this session" in the user's mental model.
 */
export function AiSettingsPanel({ compact = false }: { compact?: boolean }) {
  const modelsQuery = useAiModels()
  const testConnection = useTestAiConnection()
  const [testResult, setTestResult] = useState<'ok' | 'fail' | null>(null)

  const provider = useAiSettingsStore((s) => s.provider)
  const model = useAiSettingsStore((s) => s.model)
  const useOwnKey = useAiSettingsStore((s) => s.useOwnKey)
  const ownApiKey = useAiSettingsStore((s) => s.ownApiKey)
  const setProvider = useAiSettingsStore((s) => s.setProvider)
  const setModel = useAiSettingsStore((s) => s.setModel)
  const setUseOwnKey = useAiSettingsStore((s) => s.setUseOwnKey)
  const setOwnApiKey = useAiSettingsStore((s) => s.setOwnApiKey)

  const models = modelsQuery.data?.models ?? []
  const providers = Array.from(new Set(models.map((m) => m.provider)))
  const modelsForProvider = models.filter((m) => m.provider === provider)

  const handleTest = () => {
    setTestResult(null)
    // mutateAsync().then(), not .mutate(vars, {onSuccess}) -- see the
    // detailed rationale in src/auth/HubBridgeGate.tsx; kept consistent
    // across the app rather than re-litigating it per call site.
    testConnection
      .mutateAsync({ provider, model, api_key: useOwnKey && ownApiKey ? ownApiKey : null })
      .then((data) => setTestResult(data.ok ? 'ok' : 'fail'))
      .catch(() => setTestResult('fail'))
  }

  return (
    <div className={`rounded-xl border border-surface-border bg-surface-2 ${compact ? 'p-3' : 'p-4'} space-y-3`}>
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium tracking-wide text-neutral-400 uppercase">Modelo de IA</p>
        {testResult === 'ok' ? <span className="text-xs text-accent">Conexão ok</span> : null}
        {testResult === 'fail' ? <span className="text-xs text-red-400">Falha na conexão</span> : null}
      </div>

      <div className="flex flex-wrap gap-2">
        <select
          value={provider}
          onChange={(e) => setProvider(e.target.value)}
          className="rounded-lg border border-surface-border bg-surface-1 px-3 py-1.5 text-sm text-neutral-200"
        >
          {(providers.length > 0 ? providers : ['groq']).map((p) => (
            <option key={p} value={p}>
              {p === 'groq' ? 'Groq' : p === 'openai' ? 'OpenAI' : p}
            </option>
          ))}
        </select>

        <select
          value={model ?? ''}
          onChange={(e) => setModel(e.target.value || null)}
          className="min-w-0 flex-1 rounded-lg border border-surface-border bg-surface-1 px-3 py-1.5 text-sm text-neutral-200"
        >
          <option value="">Padrão do provedor</option>
          {modelsForProvider.map((m) => (
            <option key={m.model} value={m.model}>
              {m.label}
            </option>
          ))}
        </select>
      </div>

      <label className="flex items-center gap-2 text-xs text-neutral-400">
        <input
          type="checkbox"
          checked={useOwnKey}
          onChange={(e) => setUseOwnKey(e.target.checked)}
          className="h-3.5 w-3.5 rounded border-surface-border"
        />
        Usar minha própria chave de API (não é salva -- vale só para esta sessão)
      </label>

      {useOwnKey ? (
        <input
          type="password"
          autoComplete="off"
          value={ownApiKey}
          onChange={(e) => setOwnApiKey(e.target.value)}
          placeholder={`Chave de API da ${provider === 'openai' ? 'OpenAI' : 'Groq'}`}
          className="w-full rounded-lg border border-surface-border bg-surface-1 px-3 py-1.5 text-sm text-neutral-200"
        />
      ) : null}

      <button
        type="button"
        onClick={handleTest}
        disabled={testConnection.isPending || (useOwnKey && !ownApiKey)}
        className="rounded-lg border border-surface-border px-3 py-1.5 text-xs text-neutral-300 transition hover:border-accent/50 disabled:cursor-not-allowed disabled:opacity-40"
      >
        {testConnection.isPending ? 'Testando...' : 'Testar conexão'}
      </button>
    </div>
  )
}
