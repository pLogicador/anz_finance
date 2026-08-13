import { useState } from 'react'

import { AccessApiError } from '@/auth/access-errors'

import type { TypeFilter } from '../types'
import { AiSettingsPanel } from './AiSettingsPanel'
import { currentAiSelection } from './ai-settings-store'
import { useAskAi } from './hooks'
import type { ChatTurn } from './types'

const SUGGESTIONS = ['Qual foi minha maior categoria de gasto?', 'Meu saldo melhorou em relação ao mês anterior?', 'Onde posso economizar?']

/**
 * Grounded Q&A assistant (PARTE 6.4) -- every answer is generated only from
 * this session's currently-filtered data (see backend/app/routes/ai.py's
 * `_build_grounding_context`); nothing here is persisted beyond the
 * component's own React state (session-only, gone on reload, matches
 * guardrail #1 the same way the workspace TTL store does on the backend).
 */
export function AiAssistantPanel({ month, categories, type }: { month: string; categories: string[]; type: TypeFilter }) {
  const [question, setQuestion] = useState('')
  const [turns, setTurns] = useState<ChatTurn[]>([])
  const ask = useAskAi()

  const submit = (text: string) => {
    const trimmed = text.trim()
    if (!trimmed || !month) return
    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`
    setTurns((prev) => [...prev, { id, question: trimmed, answer: null, error: null, pending: true }])
    setQuestion('')

    const selection = currentAiSelection()
    ask
      .mutateAsync({ question: trimmed, month, categories, type, ...selection })
      .then((data) => {
        setTurns((prev) => prev.map((t) => (t.id === id ? { ...t, answer: data.answer, pending: false } : t)))
      })
      .catch((error: unknown) => {
        const message = error instanceof AccessApiError ? error.message : 'Não foi possível obter uma resposta agora.'
        setTurns((prev) => prev.map((t) => (t.id === id ? { ...t, error: message, pending: false } : t)))
      })
  }

  return (
    <div className="space-y-4">
      <AiSettingsPanel compact />

      <div className="rounded-2xl border border-surface-border bg-surface-1 p-4">
        <p className="mb-3 text-xs text-neutral-500">
          Respostas baseadas só nos dados desta sessão ({month || 'nenhum mês selecionado'} · {type}). O assistente não usa nenhum
          conhecimento externo sobre bancos ou mercado financeiro.
        </p>

        {turns.length === 0 ? (
          <div className="flex flex-wrap gap-2 pb-3">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => submit(s)}
                className="rounded-full border border-surface-border px-3 py-1 text-xs text-neutral-400 transition hover:border-accent/50 hover:text-neutral-200"
              >
                {s}
              </button>
            ))}
          </div>
        ) : (
          <div className="mb-3 space-y-3">
            {turns.map((turn) => (
              <div key={turn.id} className="space-y-1.5">
                <p className="text-sm font-medium text-neutral-200">{turn.question}</p>
                {turn.pending ? <p className="text-sm text-neutral-500">Pensando...</p> : null}
                {turn.answer ? <p className="text-sm text-neutral-400">{turn.answer}</p> : null}
                {turn.error ? <p className="text-sm text-red-400">{turn.error}</p> : null}
              </div>
            ))}
          </div>
        )}

        <form
          onSubmit={(e) => {
            e.preventDefault()
            submit(question)
          }}
          className="flex gap-2"
        >
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Pergunte sobre suas finanças neste período..."
            className="min-w-0 flex-1 rounded-lg border border-surface-border bg-surface-2 px-3 py-2 text-sm text-neutral-200"
          />
          <button
            type="submit"
            disabled={!question.trim() || !month}
            className="rounded-lg bg-accent-strong px-4 py-2 text-sm font-semibold text-neutral-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Perguntar
          </button>
        </form>
      </div>
    </div>
  )
}
