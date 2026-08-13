# Arquitetura

## Visão geral

```
Syncron Hub  ──(redireciona com ?token=...)──>  Frontend (Vercel)
                                                      │
                                                      │ POST /auth/bridge { token }
                                                      ▼
                                              Backend (Railway)
                                                      │
                                                      │ POST /validate-agendador-token
                                                      ▼
                                        subscription_access_api (Syncron,
                                        serviço externo, nunca modificado
                                        por este projeto — só chamado
                                        via HTTP, leitura)
```

O backend nunca é a fonte de verdade sobre quem é o usuário ou se o plano dele está ativo — isso é sempre decidido pelo `subscription_access_api`. O que o backend do ANZ faz, uma única vez por login, é: validar o token recebido do Hub contra esse serviço e, se a resposta confirmar um plano ativo, emitir seu **próprio** JWT de curta duração (30 min por padrão), assinado com uma chave (`SECRET_KEY`) totalmente independente da do Syncron. Esse JWT do ANZ nunca vira cookie — vai no corpo da resposta e o frontend o guarda em `localStorage`, mandando em todo request como `Authorization: Bearer`.

**Duas regras que não devem ser quebradas em nenhuma mudança futura:**
1. **Nenhum banco de dados, Redis ou armazenamento persistente** para dados do usuário, em nenhuma hipótese. Toda informação de uma sessão (extratos processados, transações classificadas, filtros salvos) vive num dicionário em memória do processo (`backend/app/workspace/store.py`), com expiração automática por tempo (TTL, 60 minutos por padrão) — reiniciar o processo do backend apaga tudo, por design.
2. **O ANZ nunca vira uma segunda fonte de identidade.** O JWT que ele emite é só uma sessão técnica temporária, válida somente depois de uma checagem bem-sucedida contra a Syncron — nunca ganha um mecanismo de renovação próprio. Se expira, o usuário volta pra tela de bloqueio institucional (precisa passar pelo Hub de novo), nunca por um "renovar sessão" que não passe pela Syncron.

## Os estados de acesso

O frontend (`frontend/src/auth/`, `frontend/src/public-bundle/`) trata estas situações distintas ao carregar:

| Estado | Quando acontece | Tela |
|---|---|---|
| Validando | `POST /auth/bridge` em andamento | `ValidatingScreen` (spinner) |
| Autorizado | Bridge deu certo, JWT emitido | O dashboard de verdade (`AppShell`) |
| Plano expirado | Syncron respondeu 403 (plano vencido) | `PlanExpiredScreen` |
| Token inválido/ausente | Sem `?token=` na URL, ou Syncron respondeu 401/404 | `InstitutionalBlockScreen` |
| Sem dados ainda | JWT válido, sessão de trabalho existe e não expirou, mas nada foi enviado ainda (backend responde 404 `no_data_yet`) | `WelcomeHub` — dentro do dashboard: escolher entre enviar extratos reais ou explorar com dados de exemplo (Fase 13) |
| Sessão de trabalho expirada | JWT ainda válido, mas os dados de uma sessão que **já tinha** upload expiraram (backend responde 410 `work_session_expired`) | `WorkSessionExpiredNotice` — aparece **dentro** do dashboard, não manda o usuário de volta ao Hub |
| Serviço indisponível | `subscription_access_api` não respondeu (timeout/5xx) | `ServiceUnavailableScreen`, com botão de tentar de novo |

"Sem dados ainda" e "Sessão de trabalho expirada" usam `error_code`s diferentes de propósito (`no_data_yet` vs. `work_session_expired`, ver `backend/app/workspace/deps.py`) — antes da Fase 13 os dois colapsavam no mesmo código, o que fazia todo usuário de primeira viagem ver uma mensagem de "sua sessão expirou" sem nunca ter enviado nada.

O bundle JS do dashboard autenticado só é buscado pelo navegador depois que o estado "Autorizado" é confirmado (`React.lazy` no roteador, `frontend/src/app/router.tsx`) — isso é verificável na aba de rede do navegador e é uma exigência explícita do modelo de acesso, não só uma otimização.

## Explorar com dados de exemplo (Fase 13)

Um usuário autenticado que ainda não enviou nada pode explorar o painel real (KPIs, gráficos, tabela de transações, filtros, busca) populado com um dataset fixo e fictício de 3 meses (`frontend/src/dashboard/demo/demo-data.ts`), sem enviar nada e sem nenhuma chamada ao backend real — todo o cálculo (resumo, série mensal, distribuição por categoria, busca) é feito no próprio navegador, com as mesmas regras de filtro do backend real (categoria vazia = sem filtro; Receitas = valor ≥ 0). Recursos que dependem de verdade do workspace do backend (exportar CSV/PDF, salvar snapshots, detecção de anomalias, comparação entre períodos, assistente de IA) ficam desabilitados ou mostram um aviso/estado bloqueado explicando que precisam de dados reais — nunca chamam o backend com uma sessão vazia. Uma faixa fixa no topo do painel ("Você está explorando com dados de exemplo") deixa isso sempre visível, com um atalho direto para o formulário de envio real.

## Pipeline de dados

1. **Ingestão** — extrato bancário `.ofx` (`POST /workspace/upload`, múltiplos arquivos, um arquivo malformado não derruba o lote) ou CSV com mapeamento de colunas (`POST /workspace/import/csv/preview` depois `/commit` — o CSV **soma** aos dados já existentes na sessão, o OFX **substitui**).
2. **Pré-processamento** — normaliza datas, deriva a coluna `Mês` (`YYYY-MM`).
3. **Classificação por IA** — cada transação é enviada a um provedor (Groq ou OpenAI, `backend/app/pipeline/categorizer/`) que devolve uma de 11 categorias fixas (`Moradia`, `Alimentação`, `Mercado`, `Transporte`, `Telefone`, `Receitas`, `Transferência para terceiros`, `Compras`, `Educação`, `Saúde`, `Investimento`) ou um rótulo de erro/não-classificado. As chamadas rodam em paralelo (limitadas por um semáforo), não uma de cada vez.
4. **Métricas e filtros** (`backend/app/pipeline/metrics.py`, `filters.py`) — resumos por período, comparação com o mês anterior, série mensal, detecção de gastos fora do padrão, comparação entre dois meses quaisquer.
5. **Apresentação** — o painel React consome tudo isso via os endpoints em `backend/app/routes/`.

## IA multi-modelo

Dois provedores reais e independentes (não um "modo simulado"): Groq e OpenAI, ambos com API de chat completions compatível. O usuário pode usar a chave padrão do operador (configurada via variável de ambiente) ou fornecer a própria chave — nesse caso, ela é usada só para aquela requisição específica, nunca fica salva em lugar nenhum (nem no backend, nem no `localStorage` do navegador).

Além da classificação, existem dois outros usos de IA:
- **Insights automáticos** (`GET /ai/insights`) — na verdade **não usam IA nenhuma**: são regras determinísticas sobre os números já calculados (concentração de gastos numa categoria, variação vs. mês anterior, taxa de poupança). Decisão deliberada — mais rápido, mais barato, sem risco de alucinação.
- **Assistente de perguntas** (`POST /ai/ask`) — esse sim usa um modelo de verdade, mas só responde com base nos dados reais da sessão atual (o prompt inclui um resumo real dos números filtrados) e é instruído a dizer claramente quando não sabe a resposta, em vez de inventar.

## Estrutura de pastas

```
anz_finance/
  backend/
    app/
      access/        controle de acesso (PARTE 5): bridge de token, sessão JWT própria
      workspace/      armazenamento em memória com TTL (PARTE 4)
      pipeline/       parsing, classificação, métricas, filtros, análise, export/import, IA
      routes/         endpoints da API
    tests/            166 testes automatizados (pytest)
  frontend/
    src/
      auth/           bridge de token, guarda de rota, os 6 estados de acesso
      public-bundle/   telas de bloqueio (carregadas ANTES de qualquer autenticação)
      dashboard/       o painel autenticado inteiro (carregado só depois do estado "Autorizado")
        ai/             seleção de modelo, insights, assistente de perguntas
        analysis/        busca global, contagem de categorias, anomalias, comparação, snapshots
        export/          exportação CSV/PDF
        import/          importação de CSV com mapeamento de colunas
        command-palette/ paleta de comandos (Ctrl/Cmd+K)
        onboarding/      tour de boas-vindas
        help/            central de ajuda
      design-system/   tokens visuais, formatação de moeda/data, cores por categoria
  legacy_streamlit/    app Streamlit original, arquivado como referência (ver seu próprio README)
```
