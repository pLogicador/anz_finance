# Deploy — Railway (backend) + Vercel (frontend)

Este é um runbook para uma pessoa com acesso às contas Railway/Vercel/Groq/OpenAI/Syncron executar o deploy manualmente. Nenhuma etapa aqui foi executada por mim — publicar em infraestrutura de nuvem real, com credenciais de produção, é uma ação que exige as contas e a decisão explícita de quem está de fato colocando o serviço no ar, então o que existe hoje no repositório é a **configuração pronta pra isso** (`backend/railway.toml`, `frontend/vercel.json`), não um deploy já feito.

## Ambiente real de produção (confirmado 2026-08-18)

- **Backend**: `https://anzfinance-production.up.railway.app/` — **Railway**, confirmado ao vivo (`GET /health` 200, `GET /openapi.json` com `"title": "ANZ Finance API"`) durante a integração com o Syncron Core.
- Esta seção do CLAUDE.md/deste runbook (Fase 10, "nenhum deploy real foi executado") ficou desatualizada — o serviço foi implantado depois daquela fase, sem deixar rastro documentado. Mesmo padrão já visto em Live Scheduler/FlexiPage/Docksmith durante esta mesma integração: a documentação "ainda não implantado" não é mais confiável como fonte de verdade sobre deploy em nenhum produto do ecossistema — sempre confirmar ao vivo antes de assumir.

Como o repositório é um monorepo (backend e frontend na mesma raiz de git), tanto o Railway quanto a Vercel precisam ser configurados com o **diretório raiz** apontando pra subpasta certa — veja abaixo.

## Pré-requisitos

- Conta no [Railway](https://railway.app) e na [Vercel](https://vercel.com), ambas com acesso ao repositório Git deste projeto.
- Uma chave de API da [Groq](https://console.groq.com) e/ou da [OpenAI](https://platform.openai.com) (pelo menos uma precisa estar configurada como padrão do operador — sem nenhuma, a classificação ainda funciona, mas degrada toda transação para "Erro na classificação"; ver `docs/ARCHITECTURE.md`).
- A URL base real do `subscription_access_api` de produção (esse serviço já existe e roda separado — não faz parte deste deploy).

## 1. Backend no Railway

1. **Novo projeto** → "Deploy from GitHub repo" → selecione este repositório.
2. Nas configurações do serviço criado, defina **Root Directory** = `backend`. É isso que faz o Railway ler `backend/railway.toml` (que já define o `startCommand` e o healthcheck em `/health`) em vez de tentar rodar a partir da raiz do monorepo.
3. Em **Variables**, configure (nomes exatos, batendo com `backend/app/core/config.py`):

   | Variável | Valor |
   |---|---|
   | `SYNCRON_API_BASE` | URL real do `subscription_access_api` de produção |
   | `SECRET_KEY` | um valor aleatório longo, gerado só pra este ambiente (`python -c "import secrets; print(secrets.token_urlsafe(48))"`) -- **nunca reaproveitar** o `SECRET_KEY` do `subscription_access_api` nem de outro serviço Syncron, é uma chave própria e independente por design |
   | `FRONTEND_URL` | a URL de produção do frontend na Vercel (depois do passo 2) -- usada só para CORS |
   | `GROQ_API_KEY` | chave da Groq (pode ficar vazia se só a OpenAI for usada como padrão) |
   | `OPENAI_API_KEY` | chave da OpenAI (pode ficar vazia se só a Groq for usada como padrão) |
   | `ALGORITHM` | `HS256` (padrão, só defina se quiser mudar) |
   | `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` (padrão) |
   | `WORKSPACE_TTL_MINUTES` | `60` (padrão) |

4. Deploy. O Railway usa Nixpacks (detecta `requirements.txt` automaticamente) e, graças ao `railway.toml`, sobe com `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
5. Confirme que `https://<seu-servico>.up.railway.app/health` responde `{"status": "ok"}`.

## 2. Frontend na Vercel

1. **Add New Project** → importe o mesmo repositório.
2. Em **Root Directory**, selecione `frontend`. A Vercel detecta automaticamente o preset "Vite" (build `vite build`, saída em `dist`). O arquivo `frontend/vercel.json` já está configurado com a regra de rewrite necessária para que rotas do React Router (`/app`, `/blocked/...`) não deem 404 ao serem acessadas diretamente ou recarregadas -- sem essa regra, um F5 em `/app` quebraria, já que a Vercel por padrão só serve arquivos estáticos que existem literalmente naquele caminho.
3. Em **Environment Variables**, configure:

   | Variável | Valor |
   |---|---|
   | `VITE_API_BASE_URL` | a URL do backend no Railway (passo 1), ex. `https://anz-finance-api.up.railway.app` |
   | `VITE_SYNCRON_HUB_URL` | a URL real do Syncron Hub de produção |

4. Deploy.
5. Volte no Railway e atualize `FRONTEND_URL` com a URL real que a Vercel gerou (necessário para o CORS do backend aceitar requisições do frontend em produção) -- redeploy do backend depois de mudar essa variável.

## 3. Smoke test pós-deploy

Depois dos dois deploys, confirme manualmente (nenhum destes foi/pôde ser executado nesta sessão, já que dependem da infraestrutura real estar no ar):

- [ ] `GET https://<backend>/health` responde 200.
- [ ] Acessar o frontend em produção **sem** `?token=` mostra a tela de bloqueio institucional (não expõe nenhuma parte do dashboard).
- [ ] Um redirecionamento real vindo do Syncron Hub (com um token válido de verdade, gerado pelo `subscription_access_api` de produção) completa o fluxo: bridge → dashboard → upload de um extrato real → categorização → painel renderizado.
- [ ] A URL fica limpa (sem `?token=`) depois do login.
- [ ] Um plano expirado de verdade mostra a tela de plano expirado, não a institucional genérica.
- [ ] `npm run build` local não teve nenhum erro antes deste deploy (rode `cd frontend && npm run build` como checagem final antes de publicar).

## Depois de confirmar tudo isso

Só então remover `legacy_streamlit/` do repositório -- ele existe hoje como referência funcional enquanto a reconstrução era validada, e sair definitivamente de cena é uma decisão que depende do deploy real ter sido confirmado de ponta a ponta, não de todas as fases de desenvolvimento estarem prontas.
