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
}: FiltersBarProps) {
  const toggleCategory = (category: string) => {
    if (selectedCategories.includes(category)) {
      onCategoriesChange(selectedCategories.filter((c) => c !== category))
    } else {
      onCategoriesChange([...selectedCategories, category])
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-surface-border bg-surface-1 p-3">
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

      <div className="ml-auto flex rounded-lg border border-surface-border bg-surface-2 p-0.5">
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
  )
}
