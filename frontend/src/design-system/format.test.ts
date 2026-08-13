import { describe, expect, it } from 'vitest'

import { formatCurrency, formatDateBr, formatPercent } from './format'

// Intl.NumberFormat('pt-BR', {style:'currency',...}) inserts a
// NON-BREAKING space (U+00A0) between "R$" and the number, not a regular
// space -- confirmed by a failing first draft of this test that used a
// plain space and got a byte-for-byte-invisible mismatch. Normalizing
// whitespace here makes the assertion robust to that ICU detail instead of
// hardcoding the exact character.
function normalizeSpaces(text: string): string {
  return text.replace(/\s/g, ' ')
}

describe('formatCurrency', () => {
  it('formats a positive value in pt-BR currency', () => {
    expect(normalizeSpaces(formatCurrency(3000))).toBe('R$ 3.000,00')
  })

  it('formats a negative value with the sign preserved', () => {
    expect(normalizeSpaces(formatCurrency(-150.5))).toBe('-R$ 150,50')
  })

  it('formats zero', () => {
    expect(normalizeSpaces(formatCurrency(0))).toBe('R$ 0,00')
  })
})

describe('formatPercent', () => {
  it('returns an em dash for null (no baseline to compare against)', () => {
    expect(formatPercent(null)).toBe('—')
  })

  it('prefixes a positive delta with +', () => {
    expect(formatPercent(12.34)).toBe('+12.3%')
  })

  it('does not double-prefix a negative delta', () => {
    expect(formatPercent(-8)).toBe('-8.0%')
  })
})

describe('formatDateBr', () => {
  it('converts an ISO date to dd/mm/yyyy', () => {
    expect(formatDateBr('2026-03-05')).toBe('05/03/2026')
  })
})
