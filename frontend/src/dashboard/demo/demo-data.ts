import type { AiInsight } from '../ai/types'
import type { CategoryBreakdownRow, MonthlySeriesRow, MonthsResponse, PeriodSummary, SummaryResponse, Transaction, TypeFilter } from '../types'

/**
 * Fase 13 -- "explorar sem enviar nada ainda". A hand-authored, realistic
 * 3-month dataset covering all 11 real category labels (see
 * backend/app/pipeline/categorizer -- these must stay in sync with the
 * classifier's actual output labels, this is presentation-only demo data,
 * never sent anywhere), used to let an authenticated Syncron user see the
 * real dashboard UI fully populated before deciding whether to upload their
 * own statements. Every function here is pure/local -- nothing in this file
 * ever calls `apiRequest`/`apiUpload`/`fetch`, by design: demo mode must
 * never touch the backend (there is no real workspace behind it yet), so
 * every derived shape (summary, monthly series, category breakdown, search,
 * category counts) is computed client-side from `DEMO_TRANSACTIONS` using
 * the same filter semantics documented for the real pipeline (empty
 * category list = no filter; Receitas = Valor >= 0, Despesas = Valor < 0).
 */

export const DEMO_TRANSACTIONS: Transaction[] = [
  // 2026-06
  { Data: '2026-06-01', Valor: 6800, Descrição: 'Salário -- Empresa XPTO Ltda', Mês: '2026-06', Categorias: 'Receitas' },
  { Data: '2026-06-02', Valor: -1450, Descrição: 'Aluguel apartamento', Mês: '2026-06', Categorias: 'Moradia' },
  { Data: '2026-06-03', Valor: -380, Descrição: 'Condomínio', Mês: '2026-06', Categorias: 'Moradia' },
  { Data: '2026-06-04', Valor: -215.4, Descrição: 'Supermercado Extra', Mês: '2026-06', Categorias: 'Mercado' },
  { Data: '2026-06-06', Valor: -68.9, Descrição: 'iFood -- Restaurante Sabor Caseiro', Mês: '2026-06', Categorias: 'Alimentação' },
  { Data: '2026-06-07', Valor: -45.0, Descrição: 'Padaria Pão Quente', Mês: '2026-06', Categorias: 'Alimentação' },
  { Data: '2026-06-08', Valor: -89.3, Descrição: 'Posto Ipiranga -- combustível', Mês: '2026-06', Categorias: 'Transporte' },
  { Data: '2026-06-09', Valor: -32.5, Descrição: 'Uber', Mês: '2026-06', Categorias: 'Transporte' },
  { Data: '2026-06-10', Valor: -74.9, Descrição: 'Conta de telefone -- Vivo', Mês: '2026-06', Categorias: 'Telefone' },
  { Data: '2026-06-11', Valor: -189.9, Descrição: 'Loja de roupas Zenith', Mês: '2026-06', Categorias: 'Compras' },
  { Data: '2026-06-13', Valor: -119.0, Descrição: 'Curso online -- Plataforma Educa+', Mês: '2026-06', Categorias: 'Educação' },
  { Data: '2026-06-14', Valor: -310.0, Descrição: 'Plano de saúde', Mês: '2026-06', Categorias: 'Saúde' },
  { Data: '2026-06-15', Valor: -58.7, Descrição: 'Farmácia São João', Mês: '2026-06', Categorias: 'Saúde' },
  { Data: '2026-06-18', Valor: -500.0, Descrição: 'Aporte CDB -- corretora', Mês: '2026-06', Categorias: 'Investimento' },
  { Data: '2026-06-20', Valor: -150.0, Descrição: 'Pix -- Divisão de conta com amigo', Mês: '2026-06', Categorias: 'Transferência para terceiros' },
  { Data: '2026-06-22', Valor: -96.4, Descrição: 'Supermercado Extra', Mês: '2026-06', Categorias: 'Mercado' },
  { Data: '2026-06-25', Valor: -52.0, Descrição: 'iFood -- Pizzaria Napoli', Mês: '2026-06', Categorias: 'Alimentação' },
  { Data: '2026-06-28', Valor: 450.0, Descrição: 'Freelance -- projeto pontual', Mês: '2026-06', Categorias: 'Receitas' },

  // 2026-07
  { Data: '2026-07-01', Valor: 6800, Descrição: 'Salário -- Empresa XPTO Ltda', Mês: '2026-07', Categorias: 'Receitas' },
  { Data: '2026-07-02', Valor: -1450, Descrição: 'Aluguel apartamento', Mês: '2026-07', Categorias: 'Moradia' },
  { Data: '2026-07-03', Valor: -380, Descrição: 'Condomínio', Mês: '2026-07', Categorias: 'Moradia' },
  { Data: '2026-07-04', Valor: -264.8, Descrição: 'Supermercado Extra', Mês: '2026-07', Categorias: 'Mercado' },
  { Data: '2026-07-05', Valor: -71.2, Descrição: 'iFood -- Restaurante Sabor Caseiro', Mês: '2026-07', Categorias: 'Alimentação' },
  { Data: '2026-07-07', Valor: -95.6, Descrição: 'Restaurante Cantina da Nona', Mês: '2026-07', Categorias: 'Alimentação' },
  { Data: '2026-07-08', Valor: -112.0, Descrição: 'Posto Ipiranga -- combustível', Mês: '2026-07', Categorias: 'Transporte' },
  { Data: '2026-07-09', Valor: -48.7, Descrição: 'Uber', Mês: '2026-07', Categorias: 'Transporte' },
  { Data: '2026-07-10', Valor: -74.9, Descrição: 'Conta de telefone -- Vivo', Mês: '2026-07', Categorias: 'Telefone' },
  { Data: '2026-07-12', Valor: -420.0, Descrição: 'Notebook -- Loja Kabum', Mês: '2026-07', Categorias: 'Compras' },
  { Data: '2026-07-14', Valor: -310.0, Descrição: 'Plano de saúde', Mês: '2026-07', Categorias: 'Saúde' },
  { Data: '2026-07-16', Valor: -41.9, Descrição: 'Farmácia São João', Mês: '2026-07', Categorias: 'Saúde' },
  { Data: '2026-07-18', Valor: -500.0, Descrição: 'Aporte CDB -- corretora', Mês: '2026-07', Categorias: 'Investimento' },
  { Data: '2026-07-19', Valor: -200.0, Descrição: 'Pix -- Aluguel de equipamento', Mês: '2026-07', Categorias: 'Transferência para terceiros' },
  { Data: '2026-07-21', Valor: -108.3, Descrição: 'Supermercado Extra', Mês: '2026-07', Categorias: 'Mercado' },
  { Data: '2026-07-23', Valor: -119.0, Descrição: 'Curso online -- Plataforma Educa+', Mês: '2026-07', Categorias: 'Educação' },
  { Data: '2026-07-27', Valor: -63.5, Descrição: 'iFood -- Pizzaria Napoli', Mês: '2026-07', Categorias: 'Alimentação' },

  // 2026-08
  { Data: '2026-08-01', Valor: 6800, Descrição: 'Salário -- Empresa XPTO Ltda', Mês: '2026-08', Categorias: 'Receitas' },
  { Data: '2026-08-02', Valor: -1450, Descrição: 'Aluguel apartamento', Mês: '2026-08', Categorias: 'Moradia' },
  { Data: '2026-08-03', Valor: -380, Descrição: 'Condomínio', Mês: '2026-08', Categorias: 'Moradia' },
  { Data: '2026-08-04', Valor: -178.6, Descrição: 'Supermercado Extra', Mês: '2026-08', Categorias: 'Mercado' },
  { Data: '2026-08-05', Valor: -39.9, Descrição: 'iFood -- Restaurante Sabor Caseiro', Mês: '2026-08', Categorias: 'Alimentação' },
  { Data: '2026-08-06', Valor: -78.4, Descrição: 'Posto Ipiranga -- combustível', Mês: '2026-08', Categorias: 'Transporte' },
  { Data: '2026-08-07', Valor: -74.9, Descrição: 'Conta de telefone -- Vivo', Mês: '2026-08', Categorias: 'Telefone' },
  { Data: '2026-08-09', Valor: -95.0, Descrição: 'Loja de roupas Zenith', Mês: '2026-08', Categorias: 'Compras' },
  { Data: '2026-08-10', Valor: -310.0, Descrição: 'Plano de saúde', Mês: '2026-08', Categorias: 'Saúde' },
  { Data: '2026-08-11', Valor: -500.0, Descrição: 'Aporte CDB -- corretora', Mês: '2026-08', Categorias: 'Investimento' },
  { Data: '2026-08-12', Valor: -66.3, Descrição: 'Supermercado Extra', Mês: '2026-08', Categorias: 'Mercado' },
  { Data: '2026-08-13', Valor: 300.0, Descrição: 'Freelance -- projeto pontual', Mês: '2026-08', Categorias: 'Receitas' },
]

const MONTH_LABELS_PT: Record<string, string> = { '06': 'junho', '07': 'julho', '08': 'agosto' }

export function demoMonthLabel(month: string): string {
  const [, m] = month.split('-')
  return MONTH_LABELS_PT[m] ?? month
}

function chronologicalMonths(): string[] {
  return Array.from(new Set(DEMO_TRANSACTIONS.map((t) => t.Mês))).sort()
}

export function demoMonthsResponse(): MonthsResponse {
  const months = chronologicalMonths()
  const years = Array.from(new Set(months.map((m) => m.slice(0, 4)))).sort()
  return { months, years }
}

export function demoAllCategories(): string[] {
  return Array.from(new Set(DEMO_TRANSACTIONS.map((t) => t.Categorias))).sort()
}

/** Same semantics as the real backend's `filter_transactions`/`_apply_type_filter`: an empty `categories` list means "no category filter", and `month` is optional (omitting it is the "trend" variant -- full history, category/type only). */
function applyFilters(transactions: Transaction[], categories: string[], type: TypeFilter, month?: string): Transaction[] {
  return transactions.filter((t) => {
    if (month && t.Mês !== month) return false
    if (categories.length > 0 && !categories.includes(t.Categorias)) return false
    if (type === 'Receitas' && t.Valor < 0) return false
    if (type === 'Despesas' && t.Valor >= 0) return false
    return true
  })
}

export function demoTransactionsFor(month: string, categories: string[], type: TypeFilter): Transaction[] {
  return applyFilters(DEMO_TRANSACTIONS, categories, type, month)
}

export function demoTrendTransactions(categories: string[], type: TypeFilter): Transaction[] {
  return applyFilters(DEMO_TRANSACTIONS, categories, type)
}

function computeSummary(transactions: Transaction[]): PeriodSummary {
  const income = transactions.filter((t) => t.Valor >= 0).reduce((sum, t) => sum + t.Valor, 0)
  const expense = transactions.filter((t) => t.Valor < 0).reduce((sum, t) => sum + t.Valor, 0)
  const byCategory = new Map<string, number>()
  for (const t of transactions) {
    if (t.Valor < 0) byCategory.set(t.Categorias, (byCategory.get(t.Categorias) ?? 0) + Math.abs(t.Valor))
  }
  let topCategory: string | null = null
  let topAmount = 0
  for (const [category, amount] of byCategory) {
    if (amount > topAmount) {
      topCategory = category
      topAmount = amount
    }
  }
  return {
    income,
    expense,
    net: income + expense,
    transaction_count: transactions.length,
    top_category: topCategory,
    top_category_amount: topAmount,
  }
}

function pctDelta(current: number, previous: number, invert = false): number | null {
  if (previous === 0) return null
  const raw = ((current - previous) / Math.abs(previous)) * 100
  return invert ? -raw : raw
}

function monthlySeriesFor(categories: string[], type: TypeFilter): MonthlySeriesRow[] {
  const filtered = applyFilters(DEMO_TRANSACTIONS, categories, type)
  return chronologicalMonths().map((month) => {
    const rows = filtered.filter((t) => t.Mês === month)
    const receitas = rows.filter((t) => t.Valor >= 0).reduce((sum, t) => sum + t.Valor, 0)
    const despesas = rows.filter((t) => t.Valor < 0).reduce((sum, t) => sum + t.Valor, 0)
    return { Mês: month, Receitas: receitas, Despesas: despesas, Saldo: receitas + despesas }
  })
}

function categoryBreakdownFor(month: string, categories: string[], type: TypeFilter): CategoryBreakdownRow[] {
  const rows = applyFilters(DEMO_TRANSACTIONS, categories, type, month)
  const byCategory = new Map<string, number>()
  for (const t of rows) byCategory.set(t.Categorias, (byCategory.get(t.Categorias) ?? 0) + Math.abs(t.Valor))
  return Array.from(byCategory.entries())
    .map(([Categorias, Valor]) => ({ Categorias, Valor }))
    .sort((a, b) => b.Valor - a.Valor)
}

export function demoSummaryFor(month: string, categories: string[], type: TypeFilter): SummaryResponse {
  const monthRows = applyFilters(DEMO_TRANSACTIONS, categories, type, month)
  const summary = computeSummary(monthRows)

  const months = chronologicalMonths()
  const idx = months.indexOf(month)
  const previousMonth = idx > 0 ? months[idx - 1] : null
  let deltas: SummaryResponse['deltas'] = { income: null, expense: null, net: null }
  if (previousMonth) {
    const previousSummary = computeSummary(applyFilters(DEMO_TRANSACTIONS, categories, type, previousMonth))
    deltas = {
      income: pctDelta(summary.income, previousSummary.income),
      expense: pctDelta(summary.expense, previousSummary.expense, true),
      net: pctDelta(summary.net, previousSummary.net),
    }
  }

  return {
    summary,
    deltas,
    monthly_series: monthlySeriesFor(categories, type),
    category_breakdown: categoryBreakdownFor(month, categories, type),
  }
}

export function demoCategoryCounts(month: string): Record<string, number> {
  const counts: Record<string, number> = {}
  for (const t of DEMO_TRANSACTIONS) {
    if (t.Mês !== month) continue
    counts[t.Categorias] = (counts[t.Categorias] ?? 0) + 1
  }
  return counts
}

export function demoSearch(query: string, categories: string[], type: TypeFilter): Transaction[] {
  const q = query.trim().toLowerCase()
  if (!q) return []
  return applyFilters(DEMO_TRANSACTIONS, categories, type).filter(
    (t) => t.Descrição.toLowerCase().includes(q) || t.Categorias.toLowerCase().includes(q),
  )
}

/** Same visual contract as `ai/AiInsights.tsx` (deterministic, rule-based, not an LLM call) -- a couple of illustrative callouts for the latest demo month, so the feature is legible in explore mode without ever hitting the real (paid, workspace-scoped) insights endpoint. */
export function demoInsights(month: string, categories: string[], type: TypeFilter): AiInsight[] {
  const { summary, deltas } = demoSummaryFor(month, categories, type)
  const insights: AiInsight[] = []

  if (deltas.expense !== null && Math.abs(deltas.expense) >= 1) {
    insights.push({
      kind: deltas.expense >= 0 ? 'positive' : 'negative',
      text: deltas.expense >= 0 ? `Despesas ${Math.abs(deltas.expense).toFixed(0)}% menores que no mês anterior.` : `Despesas ${Math.abs(deltas.expense).toFixed(0)}% maiores que no mês anterior.`,
    })
  }

  if (summary.top_category) {
    insights.push({
      kind: 'neutral',
      text: `"${summary.top_category}" é a maior categoria de gasto do mês, com R$ ${summary.top_category_amount.toFixed(0)}.`,
    })
  }

  if (summary.net >= 0) {
    insights.push({ kind: 'positive', text: 'Saldo do mês positivo -- receitas superaram despesas.' })
  }

  return insights
}
