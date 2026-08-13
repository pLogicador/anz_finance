export interface OnboardingStep {
  title: string
  description: string
}

/** Shared between the auto-shown tour and the help center's summary --
 * one real source of what the product actually does, kept in sync by
 * construction instead of duplicated copy in two components. */
export const ONBOARDING_STEPS: OnboardingStep[] = [
  {
    title: 'Bem-vindo ao ANZ Finance',
    description: 'Seus extratos são processados só nesta sessão -- nada fica salvo permanentemente. Envie um .ofx ou importe um CSV para começar.',
  },
  {
    title: 'Filtros e busca',
    description: 'Filtre por ano, mês, categoria (com contagem ao vivo) e tipo. A busca no cabeçalho procura em todo o histórico, não só no mês selecionado.',
  },
  {
    title: 'Insights e assistente de IA',
    description: 'Alertas automáticos aparecem junto aos KPIs. Na aba "Assistente IA", faça perguntas em português sobre os dados desta sessão.',
  },
  {
    title: 'Análise avançada',
    description: 'A aba "Análise" mostra gastos fora do padrão e permite comparar dois meses quaisquer, não só o mês anterior.',
  },
  {
    title: 'Exportar, importar e salvar views',
    description: 'Baixe CSV/PDF respeitando os filtros ativos, importe um CSV com mapeamento de colunas, e salve combinações de filtro como "snapshots" para reaplicar depois.',
  },
  {
    title: 'Atalhos de teclado',
    description: 'Pressione Ctrl+K (ou Cmd+K no Mac) a qualquer momento para abrir a paleta de comandos e navegar pelo painel sem usar o mouse.',
  },
]
