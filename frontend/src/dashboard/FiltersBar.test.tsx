import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { FiltersBar } from './FiltersBar'

const baseProps = {
  years: ['2026'],
  months: ['2026-02', '2026-01'],
  selectedYear: 'Todos',
  onYearChange: vi.fn(),
  selectedMonth: '2026-01',
  onMonthChange: vi.fn(),
  allCategories: ['Mercado', 'Receitas'],
  selectedCategories: ['Mercado'],
  onCategoriesChange: vi.fn(),
  selectedType: 'Todas' as const,
  onTypeChange: vi.fn(),
}

describe('FiltersBar', () => {
  it('adds a category to the selection when an unselected chip is clicked', () => {
    const onCategoriesChange = vi.fn()
    render(<FiltersBar {...baseProps} onCategoriesChange={onCategoriesChange} />)
    // "Receitas" is ambiguous by name alone -- it's both a category chip
    // AND a type-filter button (Todas/Receitas/Despesas). Category chips
    // render first in the DOM (before the type-filter group), so index 0
    // is always the chip.
    screen.getAllByRole('button', { name: 'Receitas' })[0].click()
    expect(onCategoriesChange).toHaveBeenCalledWith(['Mercado', 'Receitas'])
  })

  it('removes a category from the selection when an already-selected chip is clicked', () => {
    const onCategoriesChange = vi.fn()
    render(<FiltersBar {...baseProps} onCategoriesChange={onCategoriesChange} />)
    screen.getByRole('button', { name: /^Mercado/ }).click()
    expect(onCategoriesChange).toHaveBeenCalledWith([])
  })

  it('calls onTypeChange with the clicked type', () => {
    const onTypeChange = vi.fn()
    render(<FiltersBar {...baseProps} onTypeChange={onTypeChange} />)
    screen.getByRole('button', { name: 'Despesas' }).click()
    expect(onTypeChange).toHaveBeenCalledWith('Despesas')
  })

  it('renders live category counts next to each chip when provided (Fase 6)', () => {
    render(<FiltersBar {...baseProps} categoryCounts={{ Mercado: 4, Receitas: 1 }} />)
    expect(screen.getByRole('button', { name: /Mercado.*\(4\)/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Receitas.*\(1\)/ })).toBeInTheDocument()
  })

  it('renders without counts when categoryCounts is not provided, without crashing', () => {
    render(<FiltersBar {...baseProps} />)
    expect(screen.getByRole('button', { name: /^Mercado$/ })).toBeInTheDocument()
  })
})
