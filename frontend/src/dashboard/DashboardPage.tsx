import { lazy, Suspense, useEffect, useState } from 'react'

import { useSessionStore } from '@/auth/session-store'
import { LogoMark } from '@/design-system/Logo'
import { env } from '@/lib/env'

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
import { DashboardSkeleton } from './DashboardSkeleton'
import { DemoInsights } from './demo/DemoInsights'
import { DemoLockedPanel } from './demo/DemoLockedPanel'
import { DemoModeBanner } from './demo/DemoModeBanner'
import { demoAllCategories, demoCategoryCounts, demoMonthsResponse, demoSearch, demoSummaryFor, demoTransactionsFor, demoTrendTransactions } from './demo/demo-data'
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
import { WelcomeHub } from './WelcomeHub'
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
  return <div className="h-64 animate-pulse rounded-2xl bg-surface-1 motion-reduce:animate-none" aria-busy="true" aria-label="Carregando" />
}

const TABS = ['Visão Geral', 'Tendências', 'Mapa de Gastos', 'Transações', 'Análise', 'Assistente IA'] as const
type Tab = (typeof TABS)[number]

export default function DashboardPage() {
  const email = useSessionStore((s) => s.session?.email)
  const [showUpload, setShowUpload] = useState(false)
  // Fase 13 -- "explorar sem enviar nada ainda": a fully local, backend-free
  // preview of the real dashboard UI populated with `demo/demo-data.ts`.
  // Exiting demo mode always also sets `showUpload`, so "Enviar meus
  // extratos" from anywhere (header, command palette, the banner itself)
  // consistently lands on the real upload form, not back on the chooser.
  const [isDemo, setIsDemo] = useState(false)
  const goToRealUpload = () => {
    setIsDemo(false)
    setShowUpload(true)
  }

  const monthsQuery = useMonths(true)
  const hasRealData = monthsQuery.isSuccess && monthsQuery.data.months.length > 0 && !showUpload
  const hasData = hasRealData || isDemo

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

  const allMonths = isDemo ? demoMonthsResponse().months : (monthsQuery.data?.months ?? [])
  const allYears = isDemo ? demoMonthsResponse().years : (monthsQuery.data?.years ?? [])
  const monthsForYear = selectedYear === 'Todos' ? allMonths : allMonths.filter((m) => m.startsWith(selectedYear))
  const effectiveMonths = monthsForYear.length > 0 ? monthsForYear : allMonths

  useEffect(() => {
    if (effectiveMonths.length > 0 && !effectiveMonths.includes(selectedMonth)) {
      setSelectedMonth(effectiveMonths[0])
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [effectiveMonths.join(','), selectedMonth])

  const allCategoriesQuery = useAllCategories(hasData && !isDemo)
  const allCategories = isDemo ? demoAllCategories() : allCategoriesQuery.categories
  useEffect(() => {
    if (!categoriesInitialized && allCategories.length > 0) {
      setSelectedCategories(allCategories)
      setCategoriesInitialized(true)
    }
  }, [allCategories, categoriesInitialized])

  // Fase 13: each of these four flips to a synchronous local computation
  // (`demo/demo-data.ts`) when `isDemo` is active -- `enabled: false` keeps
  // the real react-query hooks from ever calling the backend in that state
  // (there is no real workspace behind a demo session to query).
  const transactionsQuery = useTransactions(selectedMonth, selectedCategories, selectedType, hasData && !isDemo)
  const transactions = isDemo ? demoTransactionsFor(selectedMonth, selectedCategories, selectedType) : (transactionsQuery.data?.transactions ?? [])
  const transactionsCount = isDemo ? transactions.length : transactionsQuery.data?.count

  const summaryQuery = useSummary(selectedMonth, selectedCategories, selectedType, hasData && !isDemo)
  const summaryData = isDemo ? demoSummaryFor(selectedMonth, selectedCategories, selectedType) : summaryQuery.data

  const trendQuery = useTrend(selectedCategories, selectedType, hasData && tab !== 'Visão Geral' && !isDemo)
  const trendTransactions = isDemo ? demoTrendTransactions(selectedCategories, selectedType) : trendQuery.data?.transactions

  const categoryCountsQuery = useCategoryCounts(selectedMonth, hasData && !isDemo)
  const categoryCounts = isDemo ? demoCategoryCounts(selectedMonth) : categoryCountsQuery.data?.counts

  // Auto-show the onboarding tour the first time this browser reaches a
  // real dashboard with data -- never on the upload screen itself (nothing
  // to tour yet), and never again once dismissed (persisted flag).
  useEffect(() => {
    if (hasData && !onboardingSeen) setShowTour(true)
  }, [hasData, onboardingSeen])

  if (monthsQuery.isLoading) {
    return <DashboardSkeleton />
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
        <WelcomeHub
          initialPath={showUpload ? 'upload' : 'choose'}
          onUploaded={() => {
            setShowUpload(false)
            setCategoriesInitialized(false)
            monthsQuery.refetch()
          }}
          onEnterDemo={() => setIsDemo(true)}
        />
      </div>
    )
  }

  const commands: Command[] = [
    ...TABS.map((t) => ({ id: `tab-${t}`, label: `Ir para "${t}"`, section: 'Navegação', onRun: () => setTab(t) })),
    { id: 'presentation-on', label: 'Ativar modo apresentação', section: 'Visualização', onRun: () => setPresentationMode(true) },
    { id: 'presentation-off', label: 'Sair do modo apresentação', section: 'Visualização', onRun: () => setPresentationMode(false) },
    { id: 'new-upload', label: 'Enviar novos extratos', section: 'Dados', onRun: goToRealUpload },
    // Export hits the real backend against the current workspace -- there
    // is none in demo mode, so these two commands simply don't exist there
    // rather than producing a confusing failed-download error.
    ...(!isDemo
      ? [
          { id: 'export-csv', label: 'Baixar CSV do mês selecionado', section: 'Exportar', onRun: () => void downloadCsv(selectedMonth, selectedCategories, selectedType) },
          { id: 'export-pdf', label: 'Baixar PDF do mês selecionado', section: 'Exportar', onRun: () => void downloadPdf(selectedMonth, selectedCategories, selectedType) },
        ]
      : []),
    { id: 'help', label: 'Abrir central de ajuda', section: 'Ajuda', keywords: 'shortcuts atalhos', onRun: () => setShowHelp(true) },
    { id: 'tour', label: 'Ver o tour de boas-vindas', section: 'Ajuda', onRun: () => setShowTour(true) },
    ...effectiveMonths.map((m) => ({ id: `month-${m}`, label: `Ir para o mês ${m}`, section: 'Período', onRun: () => setSelectedMonth(m) })),
  ]

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6 print:max-w-full print:space-y-4 print:p-0">
      <CommandPalette commands={commands} />

      {isDemo ? <DemoModeBanner onExit={goToRealUpload} /> : null}

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
          {/* Two rows on purpose, not one unwrapping row: the primary
              identity+action pair (logo/title, "Novo envio") never
              competes for space with the secondary utilities (search,
              help, presentation mode) below it -- confirmed by hand that a
              single flex row here overflowed at 375px (search box alone
              was ~85% of the viewport width). */}
          <header className="space-y-3 print:hidden">
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <LogoMark size={32} />
                <div>
                  <p className="text-xs text-neutral-500">ANZ Finance</p>
                  <h1 className="font-display text-xl font-semibold text-neutral-50">Painel financeiro</h1>
                </div>
              </div>
              <button
                type="button"
                onClick={goToRealUpload}
                className="rounded-lg bg-accent-strong px-3.5 py-2 text-xs font-semibold text-neutral-950 transition hover:brightness-110"
              >
                Novo envio
              </button>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <GlobalSearch
                categories={selectedCategories}
                type={selectedType}
                onJumpToMonth={setSelectedMonth}
                demoSource={isDemo ? demoSearch : undefined}
              />
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
            </div>
          </header>

          {/* print-only heading -- the interactive header above is hidden entirely when printing/exporting to PDF via the browser */}
          <h1 className="font-display hidden text-xl font-semibold text-neutral-950 print:block">ANZ Finance -- Painel financeiro ({selectedMonth})</h1>

          <div className="flex flex-wrap items-center justify-between gap-3 print:hidden">
            <FiltersBar
              years={allYears}
              months={effectiveMonths}
              selectedYear={selectedYear}
              onYearChange={setSelectedYear}
              selectedMonth={selectedMonth}
              onMonthChange={setSelectedMonth}
              allCategories={allCategories}
              selectedCategories={selectedCategories}
              onCategoriesChange={setSelectedCategories}
              selectedType={selectedType}
              onTypeChange={setSelectedType}
              categoryCounts={categoryCounts}
              resultCount={tab === 'Transações' ? transactionsCount : undefined}
            />
            {!isDemo ? (
              <ExportButtons month={selectedMonth} categories={selectedCategories} type={selectedType} />
            ) : (
              <span className="text-xs text-neutral-600">Exportar disponível com seus dados reais</span>
            )}
          </div>

          {/* Snapshots are persisted on the real backend workspace (Fase 6)
              -- there's nothing to save/list in demo mode, so the bar (and
              its `useSnapshots(true)` call on mount) simply doesn't render. */}
          {!isDemo ? (
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
          ) : null}
        </>
      ) : null}

      {summaryData ? (
        <KpiRow summary={summaryData.summary} deltas={summaryData.deltas} month={selectedMonth} />
      ) : null}

      {isDemo ? (
        <DemoInsights month={selectedMonth} categories={selectedCategories} type={selectedType} />
      ) : (
        <AiInsights month={selectedMonth} categories={selectedCategories} type={selectedType} enabled={hasData} />
      )}

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

      {tab === 'Visão Geral' && summaryData ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="glass-panel p-4">
            <h3 className="mb-2 text-sm font-medium text-neutral-300">Distribuição por categoria</h3>
            <CategoryDonutChart data={summaryData.category_breakdown} />
          </div>
          <div className="glass-panel p-4">
            <h3 className="mb-2 text-sm font-medium text-neutral-300">Maiores categorias de gasto</h3>
            <TopCategoriesBarChart data={summaryData.category_breakdown} />
          </div>
        </div>
      ) : null}

      {tab === 'Tendências' && summaryData ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="glass-panel p-4">
            <h3 className="mb-2 text-sm font-medium text-neutral-300">Receitas vs. despesas por mês</h3>
            <MonthlyIncomeExpenseChart data={summaryData.monthly_series} />
          </div>
          <div className="glass-panel p-4">
            <h3 className="mb-2 text-sm font-medium text-neutral-300">Saldo acumulado</h3>
            <CumulativeBalanceChart data={summaryData.monthly_series} />
          </div>
        </div>
      ) : null}

      {tab === 'Mapa de Gastos' ? (
        <div className="glass-panel p-4">
          <h3 className="mb-3 text-sm font-medium text-neutral-300">Categoria x mês</h3>
          {trendTransactions ? (
            <CategoryMonthHeatmap transactions={trendTransactions} />
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
          <TransactionsTable transactions={transactions} />
        </div>
      ) : null}

      {tab === 'Análise' ? (
        isDemo ? (
          <DemoLockedPanel
            title="Análise avançada disponível com seus dados reais"
            description="Detecção de gastos fora do padrão e comparação entre períodos usam o histórico completo que você enviar -- não fazem sentido sobre dados de exemplo."
            onUpload={goToRealUpload}
          />
        ) : (
          <Suspense fallback={<TabLoadingFallback />}>
            <div className="grid gap-4 lg:grid-cols-2">
              <AnomaliesPanel categories={selectedCategories} type={selectedType} enabled={hasData} />
              <ComparePanel months={allMonths} categories={selectedCategories} type={selectedType} />
            </div>
          </Suspense>
        )
      ) : null}

      {tab === 'Assistente IA' ? (
        isDemo ? (
          <DemoLockedPanel
            title="Assistente de IA disponível com seus dados reais"
            description="As respostas do assistente são geradas só a partir dos dados que você enviar -- ainda não há nada real para responder sobre."
            onUpload={goToRealUpload}
          />
        ) : (
          <Suspense fallback={<TabLoadingFallback />}>
            <AiAssistantPanel month={selectedMonth} categories={selectedCategories} type={selectedType} />
          </Suspense>
        )
      ) : null}

      {/* Rodapé padronizado com o Hub (mesma estrutura/lógica de navegação já
          aplicada no Live Scheduler/FlexiPage/AgenteOS/landing do ANZ Finance)
          -- fora do gate de presentationMode (chrome de navegação, não faz
          sentido esconder junto com abas/filtros) mas com print:hidden, já
          que não tem lugar num export em PDF. */}
      <footer className="border-t border-surface-border/60 pt-6 print:hidden">
        <div className="flex flex-col gap-6 md:flex-row md:justify-between">
          <div className="max-w-xs">
            <p className="font-display text-sm font-semibold text-neutral-50">ANZ Finance</p>
            <p className="mt-2 text-xs text-neutral-500">
              Controle financeiro completo -- parte do ecossistema Syncron.
            </p>
          </div>

          <div className="flex gap-10 text-xs">
            <div className="flex flex-col gap-2">
              <span className="font-semibold uppercase tracking-wide text-neutral-600">Ecossistema</span>
              <a href={env.syncronHubUrl} className="text-neutral-400 transition-colors hover:text-neutral-50">
                Acessar o Hub
              </a>
              <a
                href={`${env.syncronHubUrl}/app/services/`}
                className="text-neutral-400 transition-colors hover:text-neutral-50"
              >
                Minhas ferramentas
              </a>
            </div>
            <div className="flex flex-col gap-2">
              <span className="font-semibold uppercase tracking-wide text-neutral-600">Suporte</span>
              <a
                href="mailto:pedrologicador@gmail.com"
                className="text-neutral-400 transition-colors hover:text-neutral-50"
              >
                Falar com suporte
              </a>
              <a
                href={`${env.syncronHubUrl}/legal/privacy/`}
                className="text-neutral-400 transition-colors hover:text-neutral-50"
              >
                Privacidade
              </a>
              <a
                href={`${env.syncronHubUrl}/legal/terms/`}
                className="text-neutral-400 transition-colors hover:text-neutral-50"
              >
                Termos de Uso
              </a>
              <a
                href={`${env.syncronHubUrl}/legal/cookies/`}
                className="text-neutral-400 transition-colors hover:text-neutral-50"
              >
                Cookies
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
