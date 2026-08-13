import type { ReactNode } from 'react'
import { useState } from 'react'

/**
 * "O que estou vendo?" -- contextual, plain-language explanation attached
 * to a metric/chart, instead of a separate help page. Click-to-reveal
 * (not hover-only) so it works on touch devices too; closes on a second
 * click or on blur.
 */
export function InfoTooltip({ label = 'O que estou vendo?', children }: { label?: string; children: ReactNode }) {
  const [open, setOpen] = useState(false)

  return (
    <span className="relative inline-block">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        onBlur={() => setOpen(false)}
        aria-label={label}
        aria-expanded={open}
        className="flex h-4 w-4 items-center justify-center rounded-full border border-surface-border text-[10px] text-neutral-500 transition hover:border-accent/50 hover:text-accent"
      >
        ?
      </button>
      {open ? (
        <span
          role="tooltip"
          className="absolute top-full left-1/2 z-10 mt-2 w-56 -translate-x-1/2 rounded-lg border border-surface-border bg-surface-2 p-3 text-left text-xs leading-relaxed text-neutral-300 shadow-xl"
        >
          {children}
        </span>
      ) : null}
    </span>
  )
}
