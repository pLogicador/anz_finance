import type { TypeFilter } from './types'

const TYPE_OPTIONS: TypeFilter[] = ['Todas', 'Receitas', 'Despesas']

interface FiltersBarProps {
  years: string[]
  months: string[]
  selectedYear: string
  onYearChange: (year: string) => void
  selectedMonth: string
  onMonthChange: (month: string) => void
  allCategories: string[]
  selectedCategories: string[]
  onCategoriesChange: (categories: string[]) => void
  selectedType: TypeFilter
  onTypeChange: (type: TypeFilter) => void
  /** Live per-category transaction counts for the selected month (Fase 6) -- optional so this component still works standalone/pre-data. */
  categoryCounts?: Record<string, number>
  /** Live count of transactions matching the current filter combination -- "128 resultados encontrados" / "Nenhum resultado" feedback (redesign principle: filters should feel like an intelligent panel, not an admin form with no visible effect). */
  resultCount?: number
}

export function FiltersBar({
  years,
  months,
  selectedYear,
  onYearChange,
  selectedMonth,
  onMonthChange,
  allCategories,
  selectedCategories,
  onCategoriesChange,
  selectedType,
  onTypeChange,
  categoryCounts,
  resultCount,
}: FiltersBarProps) {
  const toggleCategory = (category: string) => {
    if (selectedCategories.includes(category)) {
      onCategoriesChange(selectedCategories.filter((c) => c !== category))
    } else {
      onCategoriesChange([...selectedCategories, category])
    }
  }

  const isDefault = selectedType === 'Todas' && selectedCategories.length === allCategories.length && selectedYear === 'Todos'
  const clearFilters = () => {
    onTypeChange('Todas')
    onCategoriesChange(allCategories)
    onYearChange('Todos')
  }

  return (
    <div className="glass-panel w-full p-3">
      <div className="flex flex-wrap items-center gap-3">
        <div>
          <label className="mb-1 block text-[10px] font-medium tracking-wide text-neutral-600 uppercase">Período</label>
          <div className="flex gap-2">
            <select
              value={selectedYear}
              onChange={(e) => onYearChange(e.target.value)}
              className="rounded-lg border border-surface-border bg-surface-2 px-3 py-1.5 text-sm text-neutral-200"
            >
              <option value="Todos">Todos os anos</option>
              {years.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>

            <select
              value={selectedMonth}
              onChange={(e) => onMonthChange(e.target.value)}
              className="rounded-lg border border-surface-border bg-surface-2 px-3 py-1.5 text-sm text-neutral-200"
            >
              {months.map((month) => (
                <option key={month} value={month}>
                  {month}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* `w-full` at the base breakpoint forces this onto its own row on
            narrow viewports -- `min-w-0 flex-1` alone lets a flex item
            shrink to fit the remaining space on the SAME row instead of
            wrapping (min-w-0 removes the min-content floor that would
            otherwise force a wrap), so a single long chip ends up
            squeezed into a sliver of space and overflows it. Confirmed
            by hand at 375px before fixing. */}
        <div className="w-full sm:min-w-0 sm:flex-1">
          <label className="mb-1 block text-[10px] font-medium tracking-wide text-neutral-600 uppercase">Categorias</label>
          <div className="flex flex-wrap gap-1.5">
            {allCategories.map((category) => {
              const active = selectedCategories.includes(category)
              return (
                <button
                  key={category}
                  type="button"
                  onClick={() => toggleCategory(category)}
                  className={`rounded-full border px-2.5 py-1 text-xs transition ${
                    active ? 'border-accent/50 bg-accent-soft text-accent' : 'border-surface-border text-neutral-500 hover:text-neutral-300'
                  }`}
                >
                  {category}
                  {categoryCounts?.[category] !== undefined ? <span className="ml-1 opacity-60">({categoryCounts[category]})</span> : null}
                </button>
              )
            })}
          </div>
        </div>

        <div>
          <label className="mb-1 block text-[10px] font-medium tracking-wide text-neutral-600 uppercase">Tipo</label>
          <div className="flex rounded-lg border border-surface-border bg-surface-2 p-0.5">
            {TYPE_OPTIONS.map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => onTypeChange(option)}
                className={`rounded-md px-3 py-1 text-xs font-medium transition ${
                  selectedType === option ? 'bg-accent-strong text-neutral-950' : 'text-neutral-400 hover:text-neutral-200'
                }`}
              >
                {option}
              </button>
            ))}
          </div>
        </div>
      </div>

      {resultCount !== undefined || !isDefault ? (
        <div className="mt-3 flex items-center justify-between border-t border-surface-border/60 pt-2.5 text-xs text-neutral-500">
          <span>
            {resultCount === undefined
              ? ' '
              : resultCount === 0
                ? 'Nenhum resultado para estes filtros.'
                : `${resultCount} ${resultCount === 1 ? 'transação encontrada' : 'transações encontradas'}.`}
          </span>
          {!isDefault ? (
            <button type="button" onClick={clearFilters} className="font-medium text-neutral-400 transition hover:text-accent">
              Limpar filtros
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
