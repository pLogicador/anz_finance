import { describe, expect, it } from 'vitest'

import { categoryColor } from './category-colors'

describe('categoryColor', () => {
  it('returns a stable color for a known category label', () => {
    const first = categoryColor('Mercado')
    const second = categoryColor('Mercado')
    expect(first).toBe(second)
  })

  it('gives distinct colors to the two classification fallback labels', () => {
    // Must stay in sync with backend/app/pipeline/categorizer/labels.py's
    // NOT_CLASSIFIED/CLASSIFICATION_ERROR -- both are real, common values,
    // not edge cases, so they need to look visually distinct in charts.
    expect(categoryColor('Não classificado')).not.toBe(categoryColor('Erro na classificação'))
  })

  it('falls back to the cycling palette for an unrecognized label without throwing', () => {
    expect(() => categoryColor('Categoria Totalmente Nova')).not.toThrow()
    expect(categoryColor('Categoria Totalmente Nova')).toMatch(/^#[0-9a-f]{6}$/i)
  })

  it('cycles the fallback palette by index for unknown labels', () => {
    const a = categoryColor('Desconhecida A', 0)
    const b = categoryColor('Desconhecida B', 1)
    expect(a).not.toBe(b)
  })
})
