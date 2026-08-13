import { useState } from 'react'

import { ONBOARDING_STEPS } from './steps'

export function OnboardingTour({ onClose }: { onClose: () => void }) {
  const [index, setIndex] = useState(0)
  const step = ONBOARDING_STEPS[index]
  const isLast = index === ONBOARDING_STEPS.length - 1

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 print:hidden">
      <div role="dialog" aria-modal="true" aria-labelledby="onboarding-tour-title" className="w-full max-w-md rounded-2xl border border-surface-border bg-surface-1 p-6 shadow-2xl">
        <div className="mb-4 flex gap-1">
          {ONBOARDING_STEPS.map((_, i) => (
            <div key={i} className={`h-1 flex-1 rounded-full ${i <= index ? 'bg-accent' : 'bg-surface-border'}`} />
          ))}
        </div>

        <h2 id="onboarding-tour-title" className="text-lg font-semibold text-neutral-50">
          {step.title}
        </h2>
        <p className="mt-2 text-sm text-neutral-400">{step.description}</p>

        <div className="mt-6 flex items-center justify-between">
          <button type="button" onClick={onClose} className="text-xs text-neutral-500 hover:text-neutral-300">
            Pular tour
          </button>
          <div className="flex gap-2">
            {index > 0 ? (
              <button type="button" onClick={() => setIndex((i) => i - 1)} className="rounded-lg border border-surface-border px-3 py-1.5 text-xs text-neutral-300 hover:border-accent/50">
                Voltar
              </button>
            ) : null}
            <button
              type="button"
              onClick={() => (isLast ? onClose() : setIndex((i) => i + 1))}
              className="rounded-lg bg-accent-strong px-3 py-1.5 text-xs font-semibold text-neutral-950 hover:brightness-110"
            >
              {isLast ? 'Concluir' : 'Próximo'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
