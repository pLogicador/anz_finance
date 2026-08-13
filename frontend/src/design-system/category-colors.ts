/**
 * Stable per-category color mapping -- same *mechanism* as legacy
 * (modules/ui/theme.py::CATEGORY_COLORS/category_color()): a fixed color
 * per label so charts don't reshuffle colors across filter/rerun, with a
 * palette-cycling fallback for anything unrecognized. New hex values (full
 * creative freedom on the palette itself), same 11 label keys +
 * "Não classificado"/"Erro na classificação" (verbatim, must match
 * backend/app/pipeline/categorizer/labels.py).
 */
const CATEGORY_COLORS: Record<string, string> = {
  Moradia: '#38bdf8',
  Alimentação: '#fb923c',
  Mercado: '#34d399',
  Transporte: '#a78bfa',
  Telefone: '#22d3ee',
  Receitas: '#4ade80',
  'Transferência para terceiros': '#f472b6',
  Compras: '#e879f9',
  Educação: '#facc15',
  Saúde: '#2dd4bf',
  Investimento: '#84cc16',
  'Erro na classificação': '#94a3b8',
  'Não classificado': '#64748b',
}

const FALLBACK_PALETTE = ['#38bdf8', '#fb923c', '#34d399', '#a78bfa', '#22d3ee', '#4ade80', '#f472b6', '#facc15']

export function categoryColor(label: string, fallbackIndex = 0): string {
  return CATEGORY_COLORS[label] ?? FALLBACK_PALETTE[fallbackIndex % FALLBACK_PALETTE.length]
}
