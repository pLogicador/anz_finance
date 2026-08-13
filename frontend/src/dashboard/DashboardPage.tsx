import { lazy, Suspense, useEffect, useState } from 'react'

import { useSessionStore } from '@/auth/session-store'
import { LogoMark } from '@/design-system/Logo'

import { AiInsights } from './ai/AiInsights'
import { GlobalSearch } from './analysis/GlobalSearch'
import { useCategoryCounts } from './analysis/hooks'
import { SnapshotsBar } from './analysis/SnapshotsBar'
import { CategoryDonutChart } from './charts/CategoryDonutChart'
import { CategoryMonthHeatmap } from './charts/CategoryMonthHeatmap'
import { CumulativeBalanceChart } from './charts/CumulativeBalanceChart'
import { MonthlyIncomeExpenseChart } from './charts/MonthlyIncomeExpenseChart'
import { TopCategoriesBarChart } from './charts/TopCategoriesBarChart'
import { type Command, CommandPalette } from './command-palette/CommandPalette'
import { EmptyState } from './EmptyState'
import { downloadCsv, downloadPdf } from './export/api'
import { ExportButtons } from './export/ExportButtons'
import { FiltersBar } from './FiltersBar'
import { HelpCenter } from './help/HelpCenter'
import { isWorkSessionExpired, useAllCategories, useMonths, useSummary, useTransactions, useTrend } from './hooks'
import { KpiRow } from './KpiRow'
import { OnboardingTour } from './onboarding/OnboardingTour'
import { useOnboardingStore } from './onboarding/onboarding-store'
import { TransactionsTable } from './TransactionsTable'
import type { TypeFilter } from './types'
import { UploadPanel } from './UploadPanel'
import { WorkSessionExpiredNotice } from './WorkSessionExpiredNotice'

// Fase 9 performance pass: these three are the heaviest optional pieces of
// the dashboard (the AI chat's own state machine, the anomaly/compare
// analysis panels) -- a user might never open "Análise" or "Assistente IA"
// in a given session, so their code shouldn't have to be parsed/executed
// before the default "Visão Geral" tab is interactive. `AiInsights` is NOT
// lazy -- it renders on every tab, unconditionally, right under the KPIs.
const AnomaliesPanel = lazy(() => import('./analysis/AnomaliesPanel').then((m) => ({ default: m.AnomaliesPanel })))
const ComparePanel = lazy(() => import('./analysis/ComparePanel').then((m) => ({ default: m.ComparePanel })))
const AiAssistantPanel = lazy(() => import('./ai/AiAssistantPanel').then((m) => ({ default: m.AiAssistantPanel })))

function TabLoadingFallback() {
  return <div className="p-8 text-sm text-neutral-500">Carregando...</div>
}

const TABS = ['Visão Geral', 'Tendências', 'Mapa de Gastos', 'Transações', 'Análise', 'Assistente IA'] as const
type Tab = (typeof TABS)[number]

export default function DashboardPage() {
  const email = useSessionStore((s) => s.session?.email)
  const [showUpload, setShowUpload] = useState(false)

  const monthsQuery = useMonths(true)
  const hasData = monthsQuery.isSuccess && monthsQuery.data.months.length > 0 && !showUpload

  const [selectedYear, setSelectedYear] = useState('Todos')
  const [selectedMonth, setSelectedMonth] = useState('')
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [categoriesInitialized, setCategoriesInitialized] = useState(false)
  const [selectedType, setSelectedType] = useState<TypeFilter>('Todas')
  const [tab, setTab] = useState<Tab>('Visão Geral')
  const [presentationMode, setPresentationMode] = useState(false)
  const [showHelp, setShowHelp] = useState(false)
  const [showTour, setShowTour] = useState(false)
  const onboardingSeen = useOnboardingStore((s) => s.seen)
  const markOnboardingSeen = useOnboardingStore((s) => s.markSeen)

  const allMonths = monthsQuery.data?.months ?? []
  const allYears = monthsQuery.data?.years ?? []
  const monthsForYear = selectedYear === 'Todos' ? allMonths : allMonths.filter((m) => m.startsWith(selectedYear))
  const effectiveMonths = monthsForYear.length > 0 ? monthsForYear : allMonths

  useEffect(() => {
    if (effectiveMonths.length > 0 && !effectiveMonths.includes(selectedMonth)) {
      setSelectedMonth(effectiveMonths[0])
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [effectiveMonths.join(','), selectedMonth])

  const allCategoriesQuery = useAllCategories(hasData)
  useEffect(() => {
    if (!categoriesInitialized && allCategoriesQuery.categories.length > 0) {
      setSelectedCategories(allCategoriesQuery.categories)
      setCategoriesInitialized(true)
    }
  }, [allCategoriesQuery.categories, categoriesInitialized])

  const transactionsQuery = useTransactions(selectedMonth, selectedCategories, selectedType, hasData)
  const summaryQuery = useSummary(selectedMonth, selectedCategories, selectedType, hasData)
  const trendQuery = useTrend(selectedCategories, selectedType, hasData && tab !== 'Visão Geral')
  const categoryCountsQuery = useCategoryCounts(selectedMonth, hasData)

  // Auto-show the onboarding tour the first time this browser reaches a
  // real dashboard with data -- never on the upload screen itself (nothing
  // to tour yet), and never again once dismissed (persisted flag).
  useEffect(() => {
    if (hasData && !onboardingSeen) setShowTour(true)
  }, [hasData, onboardingSeen])

  if (monthsQuery.isLoading) {
    return <div className="p-8 text-sm text-neutral-500">Carregando...</div>
  }

  if (!hasData) {
    // `showUpload` (the user explicitly asked to send new files, whether
    // via "Novo envio" or the work-session-expired notice's action) always
    // wins over an error left over from the previous, now-abandoned query
    // -- otherwise clicking "Enviar extratos novamente" would just show
    // the same expired notice again since monthsQuery hasn't refetched yet.
    if (!showUpload && monthsQuery.isError && isWorkSessionExpired(monthsQuery.error)) {
      return (
        <div className="p-8">
          <WorkSessionExpiredNotice onReupload={() => setShowUpload(true)} />
        </div>
      )
    }
    return (
      <div className="p-8">
        <UploadPanel
          onUploaded={() => {
            setShowUpload(false)
            setCategoriesInitialized(false)
            monthsQuery.refetch()
          }}
        />
      </div>
    )
  }

  const commands: Command[] = [
    ...TABS.map((t) => ({ id: `tab-${t}`, label: `Ir para "${t}"`, section: 'Navegação', onRun: () => setTab(t) })),
    { id: 'presentation-on', label: 'Ativar modo apresentação', section: 'Visualização', onRun: () => setPresentationMode(true) },
    { id: 'presentation-off', label: 'Sair do modo apresentação', section: 'Visualização', onRun: () => setPresentationMode(false) },
    { id: 'new-upload', label: 'Enviar novos extratos', section: 'Dados', onRun: () => setShowUpload(true) },
    { id: 'export-csv', label: 'Baixar CSV do mês selecionado', section: 'Exportar', onRun: () => void downloadCsv(selectedMonth, selectedCategories, selectedType) },
    { id: 'export-pdf', label: 'Baixar PDF do mês selecionado', section: 'Exportar', onRun: () => void downloadPdf(selectedMonth, selectedCategories, selectedType) },
    { id: 'help', label: 'Abrir central de ajuda', section: 'Ajuda', keywords: 'shortcuts atalhos', onRun: () => setShowHelp(true) },
    { id: 'tour', label: 'Ver o tour de boas-vindas', section: 'Ajuda', onRun: () => setShowTour(true) },
    ...effectiveMonths.map((m) => ({ id: `month-${m}`, label: `Ir para o mês ${m}`, section: 'Período', onRun: () => setSelectedMonth(m) })),
  ]

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6 print:max-w-full print:space-y-4 print:p-0">
      <CommandPalette commands={commands} />

      {showTour ? (
        <OnboardingTour
          onClose={() => {
            setShowTour(false)
            markOnboardingSeen()
          }}
        />
      ) : null}

      {showHelp ? (
        <HelpCenter
          onClose={() => setShowHelp(false)}
          onRestartTour={() => {
            setShowHelp(false)
            setShowTour(true)
          }}
        />
      ) : null}

      {presentationMode ? (
        <button
          type="button"
          onClick={() => setPresentationMode(false)}
          className="fixed top-4 right-4 z-20 rounded-lg border border-surface-border bg-surface-1 px-3 py-1.5 text-xs text-neutral-300 shadow-lg hover:border-accent/50 print:hidden"
        >
          Sair do modo apresentação
        </button>
      ) : null}

      {!presentationMode ? (
        <>
          <header className="flex flex-wrap items-center justify-between gap-3 print:hidden">
            <div className="flex items-center gap-3">
              <LogoMark size={32} />
              <div>
                <p className="text-xs text-neutral-500">ANZ Finance</p>
                <h1 className="text-xl font-semibold text-neutral-50">Painel financeiro</h1>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <GlobalSearch categories={selectedCategories} type={selectedType} onJumpToMonth={setSelectedMonth} />
              {email ? <span className="hidden text-sm text-neutral-500 sm:inline">{email}</span> : null}
              <button
                type="button"
                onClick={() => setShowHelp(true)}
                aria-label="Ajuda"
                title="Ajuda (ou pressione Ctrl/Cmd+K para comandos)"
                className="rounded-lg border border-surface-border px-3 py-1.5 text-xs text-neutral-300 hover:border-accent/50"
              >
                ?
              </button>
              <button
                type="button"
                onClick={() => setPresentationMode(true)}
                className="rounded-lg border border-surface-border px-3 py-1.5 text-xs text-neutral-300 hover:border-accent/50"
              >
                Modo apresentação
              </button>
              <button
                type="button"
                onClick={() => setShowUpload(true)}
                className="rounded-lg border border-surface-border px-3 py-1.5 text-xs text-neutral-300 hover:border-accent/50"
              >
                Novo envio
              </button>
            </div>
          </header>

          {/* print-only heading -- the interactive header above is hidden entirely when printing/exporting to PDF via the browser */}
          <h1 className="hidden text-xl font-semibold text-neutral-950 print:block">ANZ Finance -- Painel financeiro ({selectedMonth})</h1>

          <div className="flex flex-wrap items-center justify-between gap-3 print:hidden">
            <FiltersBar
              years={allYears}
              months={effectiveMonths}
              selectedYear={selectedYear}
              onYearChange={setSelectedYear}
              selectedMonth={selectedMonth}
              onMonthChange={setSelectedMonth}
              allCategories={allCategoriesQuery.categories}
              selectedCategories={selectedCategories}
              onCategoriesChange={setSelectedCategories}
              selectedType={selectedType}
              onTypeChange={setSelectedType}
              categoryCounts={categoryCountsQuery.data?.counts}
            />
            <ExportButtons month={selectedMonth} categories={selectedCategories} type={selectedType} />
          </div>

          <SnapshotsBar
            month={selectedMonth}
            categories={selectedCategories}
            type={selectedType}
            onApply={(s) => {
              setSelectedMonth(s.month)
              setSelectedCategories(s.categories)
              setSelectedType(s.type)
            }}
          />
        </>
      ) : null}

      {summaryQuery.data ? (
        <KpiRow summary={summaryQuery.data.summary} deltas={summaryQuery.data.deltas} month={selectedMonth} />
      ) : null}

      <AiInsights month={selectedMonth} categories={selectedCategories} type={selectedType} enabled={hasData} />

      {!presentationMode ? (
        <div className="flex gap-1 overflow-x-auto border-b border-surface-border print:hidden">
          {TABS.map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setTab(t)}
              className={`px-3 py-2 text-sm font-medium whitespace-nowrap transition ${
                tab === t ? 'border-b-2 border-accent text-neutral-50' : 'text-neutral-500 hover:text-neutral-300'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      ) : null}

      {tab === 'Visão Geral' && summaryQuery.data ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-2xl border border-surface-border bg-surface-1 p-4">
            <h3 className="mb-2 text-sm font-medium text-neutral-300">Distribuição por categoria</h3>
            <CategoryDonutChart data={summaryQuery.data.category_breakdown} />
          </div>
          <div className="rounded-2xl border border-surface-border bg-surface-1 p-4">
            <h3 className="mb-2 text-sm font-medium text-neutral-300">Maiores categorias de gasto</h3>
            <TopCategoriesBarChart data={summaryQuery.data.category_breakdown} />
          </div>
        </div>
      ) : null}

      {tab === 'Tendências' && summaryQuery.data ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-2xl border border-surface-border bg-surface-1 p-4">
            <h3 className="mb-2 text-sm font-medium text-neutral-300">Receitas vs. despesas por mês</h3>
            <MonthlyIncomeExpenseChart data={summaryQuery.data.monthly_series} />
          </div>
          <div className="rounded-2xl border border-surface-border bg-surface-1 p-4">
            <h3 className="mb-2 text-sm font-medium text-neutral-300">Saldo acumulado</h3>
            <CumulativeBalanceChart data={summaryQuery.data.monthly_series} />
          </div>
        </div>
      ) : null}

      {tab === 'Mapa de Gastos' ? (
        <div className="rounded-2xl border border-surface-border bg-surface-1 p-4">
          <h3 className="mb-3 text-sm font-medium text-neutral-300">Categoria x mês</h3>
          {trendQuery.data ? (
            <CategoryMonthHeatmap transactions={trendQuery.data.transactions} />
          ) : (
            <EmptyState icon="🗓️" title="Carregando..." subtitle="" />
          )}
        </div>
      ) : null}

      {tab === 'Transações' ? (
        <div>
          <div className="mb-2 text-xs text-neutral-500">
            {selectedMonth} · {selectedType}
          </div>
          <TransactionsTable transactions={transactionsQuery.data?.transactions ?? []} />
        </div>
      ) : null}

      {tab === 'Análise' ? (
        <Suspense fallback={<TabLoadingFallback />}>
          <div className="grid gap-4 lg:grid-cols-2">
            <AnomaliesPanel categories={selectedCategories} type={selectedType} enabled={hasData} />
            <ComparePanel months={allMonths} categories={selectedCategories} type={selectedType} />
          </div>
        </Suspense>
      ) : null}

      {tab === 'Assistente IA' ? (
        <Suspense fallback={<TabLoadingFallback />}>
          <AiAssistantPanel month={selectedMonth} categories={selectedCategories} type={selectedType} />
        </Suspense>
      ) : null}
    </div>
  )
}
