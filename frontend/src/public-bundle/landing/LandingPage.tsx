import { env } from '@/lib/env'
import { Logo } from '@/design-system/Logo'

import { DashboardPreview } from './DashboardPreview'

/**
 * The real front door of the product (PARTE "Experiência de Entrada"):
 * whoever lands on `/` with no `?token=` and no still-valid ANZ session
 * sees THIS, not the terse institutional block screen (that one is now
 * reserved for a genuine error -- a token that WAS present but got
 * rejected, see RootRoute.tsx/HubBridgeGate.tsx). Everything here is
 * public-bundle: no dashboard code, no charting library, no auth-only
 * component is imported by this file or DashboardPreview.tsx.
 */
export function LandingPage() {
  return (
    // overflow-x-clip guards against decorative bleed (e.g. the hero's
    // glow blur, which intentionally extends past its own box) ever
    // pushing the page wider than the viewport -- confirmed necessary by
    // hand: a first pass without it measured a real horizontal overflow
    // on mobile (390px) even though nothing was visibly cut off in a
    // screenshot, exactly the kind of overflow a visual check alone
    // misses.
    <div className="min-h-screen overflow-x-clip bg-surface-0 text-neutral-100">
      <TopNav />
      <Hero />
      <ProblemSolution />
      <Features />
      <HowItWorks />
      <AiSpotlight />
      <SecuritySection />
      <FinalCta />
      <Footer />
    </div>
  )
}

function TopNav() {
  return (
    <header className="sticky top-0 z-20 border-b border-surface-border/60 bg-surface-0/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3 sm:px-8">
        <Logo size={26} />
        <a
          href={env.syncronHubUrl}
          className="rounded-lg bg-accent-strong px-4 py-2 text-sm font-semibold text-neutral-950 transition hover:brightness-110"
        >
          Entrar com Syncron
        </a>
      </div>
    </header>
  )
}

function Hero() {
  return (
    <section className="mx-auto grid max-w-6xl items-center gap-10 px-5 pt-14 pb-20 sm:px-8 lg:grid-cols-[1.05fr_1fr] lg:gap-14 lg:pt-24 lg:pb-28">
      <div className="text-center lg:text-left">
        <p className="mb-4 inline-flex items-center gap-1.5 rounded-full border border-surface-border bg-surface-1 px-3 py-1 text-xs text-neutral-400">
          <span className="h-1.5 w-1.5 rounded-full bg-accent" aria-hidden />
          Um serviço do ecossistema Syncron
        </p>
        <h1 className="text-4xl leading-[1.08] font-semibold tracking-tight text-neutral-50 sm:text-5xl lg:text-[3.4rem]">
          Entenda seus dados.
          <br />
          Tome decisões <span className="text-accent">melhores</span>.
        </h1>
        <p className="mx-auto mt-5 max-w-md text-base leading-relaxed text-neutral-400 lg:mx-0 lg:text-lg">
          Envie o extrato do seu banco e o ANZ Finance organiza, categoriza com IA e transforma seus dados financeiros num
          painel que faz sentido -- sem planilha, sem cadastro novo.
        </p>
        <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center lg:justify-start">
          <a
            href={env.syncronHubUrl}
            className="w-full rounded-lg bg-accent-strong px-6 py-3 text-center text-sm font-semibold text-neutral-950 transition hover:brightness-110 sm:w-auto"
          >
            Entrar com Syncron
          </a>
          <a
            href="#como-funciona"
            className="w-full rounded-lg border border-surface-border px-6 py-3 text-center text-sm font-medium text-neutral-300 transition hover:border-accent/50 hover:text-neutral-100 sm:w-auto"
          >
            Como funciona
          </a>
        </div>
        <p className="mt-5 text-xs text-neutral-600">
          Sem novo cadastro -- sua conta Syncron já dá acesso. Nada fica salvo além da sua sessão.
        </p>
      </div>

      <div className="relative">
        <div
          className="pointer-events-none absolute -inset-8 -z-10 rounded-full bg-accent/10 blur-3xl motion-safe:animate-pulse"
          aria-hidden
        />
        <DashboardPreview className="mx-auto max-w-md lg:max-w-none" />
      </div>
    </section>
  )
}

function ProblemSolution() {
  return (
    <section className="border-t border-surface-border/60 bg-surface-1/40">
      <div className="mx-auto max-w-5xl px-5 py-16 sm:px-8 sm:py-20">
        <div className="grid gap-8 sm:grid-cols-2 sm:gap-6">
          <div className="rounded-2xl border border-surface-border bg-surface-1 p-6 sm:p-7">
            <p className="mb-3 text-xs font-medium tracking-wide text-neutral-500 uppercase">O problema</p>
            <h2 className="text-xl font-semibold text-neutral-50 sm:text-2xl">Seu extrato bancário não conta a história toda.</h2>
            <p className="mt-3 text-sm leading-relaxed text-neutral-400 sm:text-base">
              Uma lista de transações não mostra pra onde o dinheiro realmente vai, o que mudou entre um mês e outro, ou o que
              merece sua atenção. Entender isso à mão, numa planilha, toma tempo que ninguém tem sobrando.
            </p>
          </div>
          <div className="rounded-2xl border border-accent/30 bg-accent-soft p-6 sm:p-7">
            <p className="mb-3 text-xs font-medium tracking-wide text-accent uppercase">Como o ANZ resolve</p>
            <h2 className="text-xl font-semibold text-neutral-50 sm:text-2xl">
              A IA categoriza. O painel explica. Você decide.
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-neutral-300 sm:text-base">
              Envie o extrato, e em segundos cada transação já está organizada por categoria, com métricas, comparações e
              alertas automáticos prontos -- sem você precisar montar nada.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}

const FEATURES: { icon: string; title: string; description: string }[] = [
  { icon: '🤖', title: 'IA multi-modelo', description: 'Groq e OpenAI classificam suas transações automaticamente -- use a chave padrão ou a sua própria.' },
  { icon: '📊', title: 'Painel completo', description: 'Visão geral, tendências, mapa de gastos por categoria e mês, tudo num só lugar.' },
  { icon: '🔍', title: 'Análise avançada', description: 'Detecção de gastos fora do padrão e comparação entre dois períodos quaisquer, não só o mês anterior.' },
  { icon: '💬', title: 'Assistente de perguntas', description: 'Pergunte em português sobre seus dados -- a IA responde só com base no que está na sua sessão.' },
  { icon: '📤', title: 'Exportação real', description: 'CSV e PDF respeitando exatamente os filtros que você aplicou, prontos pra compartilhar.' },
  { icon: '🔒', title: 'Sem dado permanente', description: 'Nada fica salvo além da sua sessão -- ela expira sozinha e os dados somem com ela.' },
]

function Features() {
  return (
    <section className="mx-auto max-w-6xl px-5 py-16 sm:px-8 sm:py-20">
      <div className="mx-auto max-w-xl text-center">
        <p className="mb-3 text-xs font-medium tracking-wide text-neutral-500 uppercase">O que você pode fazer</p>
        <h2 className="text-2xl font-semibold text-neutral-50 sm:text-3xl">Tudo que você precisa, nada que você não usa.</h2>
      </div>
      <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map((f) => (
          <div key={f.title} className="rounded-2xl border border-surface-border bg-surface-1 p-5 transition hover:border-accent/40">
            <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-accent-soft text-lg">{f.icon}</div>
            <h3 className="font-semibold text-neutral-50">{f.title}</h3>
            <p className="mt-1.5 text-sm leading-relaxed text-neutral-400">{f.description}</p>
          </div>
        ))}
      </div>
    </section>
  )
}

const STEPS: { number: string; title: string; description: string }[] = [
  { number: '01', title: 'Entre', description: 'Clique em "Entrar com Syncron" -- se você já tem uma conta ativa, o acesso é imediato.' },
  { number: '02', title: 'Configure', description: 'Envie o extrato (.ofx) ou importe um CSV. Escolha o modelo de IA, se quiser.' },
  { number: '03', title: 'Analise', description: 'Suas transações aparecem categorizadas, com KPIs, gráficos e insights automáticos.' },
  { number: '04', title: 'Explore', description: 'Filtre por período, categoria e tipo. Busque, compare meses, veja anomalias.' },
  { number: '05', title: 'Exporte', description: 'Baixe um CSV ou PDF com exatamente o recorte que você estava vendo.' },
]

function HowItWorks() {
  return (
    <section id="como-funciona" className="border-t border-surface-border/60 bg-surface-1/40">
      <div className="mx-auto max-w-6xl px-5 py-16 sm:px-8 sm:py-20">
        <div className="mx-auto max-w-xl text-center">
          <p className="mb-3 text-xs font-medium tracking-wide text-neutral-500 uppercase">Como funciona</p>
          <h2 className="text-2xl font-semibold text-neutral-50 sm:text-3xl">Do extrato ao insight, em 5 passos.</h2>
        </div>

        {/* Native horizontal scroll-snap on mobile (real swipe, no custom gesture JS needed); a normal grid from sm upward. */}
        <div className="mt-10 flex snap-x snap-mandatory gap-4 overflow-x-auto pb-2 sm:grid sm:snap-none sm:grid-cols-3 sm:overflow-visible lg:grid-cols-5">
          {STEPS.map((s) => (
            <div
              key={s.number}
              className="w-[78%] shrink-0 snap-center rounded-2xl border border-surface-border bg-surface-1 p-5 sm:w-auto sm:shrink"
            >
              <span className="text-2xl font-bold text-accent/40">{s.number}</span>
              <h3 className="mt-2 font-semibold text-neutral-50">{s.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-neutral-400">{s.description}</p>
            </div>
          ))}
        </div>
        <p className="mt-3 text-center text-xs text-neutral-600 sm:hidden">Arraste para o lado para ver os próximos passos →</p>
      </div>
    </section>
  )
}

function AiSpotlight() {
  return (
    <section className="mx-auto max-w-6xl px-5 py-16 sm:px-8 sm:py-20">
      <div className="grid items-center gap-10 lg:grid-cols-2 lg:gap-16">
        <div>
          <p className="mb-3 text-xs font-medium tracking-wide text-neutral-500 uppercase">Inteligência artificial</p>
          <h2 className="text-2xl font-semibold text-neutral-50 sm:text-3xl">Não é um botão de "perguntar à IA". É um assistente de verdade.</h2>
          <p className="mt-4 text-base leading-relaxed text-neutral-400">
            Pergunte com suas próprias palavras -- "qual foi minha maior variação?", "o que merece minha atenção?", "compare os
            dois períodos" -- e a resposta vem só dos dados reais da sua sessão. A IA nunca inventa números que não existem no
            seu extrato.
          </p>
          <ul className="mt-5 space-y-2.5 text-sm text-neutral-300">
            {['Insights automáticos ao lado dos gráficos, sem precisar perguntar', 'Detecção de gastos fora do padrão comparando com sua própria média', 'Groq ou OpenAI -- use a chave padrão ou a sua'].map((item) => (
              <li key={item} className="flex items-start gap-2">
                <span className="mt-0.5 text-accent">✓</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-2xl border border-surface-border bg-surface-1 p-5">
          <p className="text-xs text-neutral-500">Você perguntou</p>
          <p className="mt-1 text-sm font-medium text-neutral-200">Onde posso economizar esse mês?</p>
          <div className="mt-4 rounded-xl border border-accent/30 bg-accent-soft p-4 text-sm leading-relaxed text-neutral-200">
            "Moradia" concentra 34% dos seus gastos em julho -- bem acima da sua média histórica de 24%. As demais categorias
            estão dentro do esperado.
          </div>
        </div>
      </div>
    </section>
  )
}

function SecuritySection() {
  return (
    <section className="border-t border-surface-border/60 bg-surface-1/40">
      <div className="mx-auto max-w-4xl px-5 py-16 text-center sm:px-8 sm:py-20">
        <p className="mb-3 text-xs font-medium tracking-wide text-neutral-500 uppercase">Seus dados</p>
        <h2 className="text-2xl font-semibold text-neutral-50 sm:text-3xl">Sem cadastro novo. Sem dado guardado além da sua sessão.</h2>
        <div className="mt-8 grid gap-4 text-left sm:grid-cols-3">
          {[
            { title: 'Sua conta já é a Syncron', text: 'O ANZ nunca pede um login próprio -- ele confirma seu acesso direto com a Syncron, uma vez, e pronto.' },
            { title: 'Nada fica salvo', text: 'Extratos, categorias e filtros vivem só enquanto sua sessão está ativa. Sem banco de dados, sem histórico permanente.' },
            { title: 'Sessão expira sozinha', text: 'Se ficar inativo por um tempo, sua sessão simplesmente expira -- sem risco de dado esquecido em algum lugar.' },
          ].map((item) => (
            <div key={item.title} className="rounded-2xl border border-surface-border bg-surface-1 p-5">
              <h3 className="font-semibold text-neutral-50">{item.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-neutral-400">{item.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function FinalCta() {
  return (
    <section className="mx-auto max-w-4xl px-5 py-20 text-center sm:px-8 sm:py-28">
      <h2 className="text-2xl font-semibold text-neutral-50 sm:text-4xl">Pronto para ver seus dados com clareza?</h2>
      <p className="mx-auto mt-4 max-w-md text-base text-neutral-400">
        Entre com sua conta Syncron -- não precisa criar nada novo, o acesso é imediato.
      </p>
      <a
        href={env.syncronHubUrl}
        className="mt-8 inline-flex rounded-lg bg-accent-strong px-8 py-3.5 text-sm font-semibold text-neutral-950 transition hover:brightness-110"
      >
        Entrar com Syncron
      </a>
    </section>
  )
}

function Footer() {
  return (
    <footer className="border-t border-surface-border/60 px-5 py-8 text-center text-xs text-neutral-600 sm:px-8">
      <p>ANZ Finance é um serviço do ecossistema Syncron.</p>
    </footer>
  )
}
