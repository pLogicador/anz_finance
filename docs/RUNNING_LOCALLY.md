# Rodando localmente

Três peças precisam estar rodando ao mesmo tempo para testar o fluxo completo: o backend do ANZ, o frontend do ANZ, e (só em desenvolvimento) um mock do `subscription_access_api`, já que não há acesso a uma instância real dele fora de produção.

## 1. Mock do `subscription_access_api` (porta 9100)

```bash
cd backend
python -m venv .venv          # só na primeira vez
.venv\Scripts\activate        # Windows (ou: source .venv/bin/activate no Linux/Mac)
pip install -r requirements.txt
uvicorn tests.fixtures.mock_syncron_server:app --port 9100 --reload
```

Esse servidor simula o `POST /validate-agendador-token` real, sem precisar de credenciais nem de uma instância de verdade da Syncron rodando. O comportamento é controlado pelo valor do token enviado:

| Token começa com... | Resposta simulada |
|---|---|
| `valid` | 200 — acesso autorizado |
| `expired-plan` | 403 — plano expirado |
| `down` (exato) | 500 — serviço indisponível |
| qualquer outro valor | 401 — token inválido |

## 2. Backend do ANZ (porta 9101)

Crie `backend/.env` (nunca commitado — veja `backend/.env.example` para o template completo):

```env
SYNCRON_API_BASE=http://localhost:9100
SECRET_KEY=qualquer-valor-aleatorio-para-dev
FRONTEND_URL=http://localhost:5173
GROQ_API_KEY=            # opcional em dev -- vazio faz a classificação degradar
OPENAI_API_KEY=          # graciosamente (marca como "Erro na classificação"),
                          # não trava o upload
```

```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --port 9101 --reload
```

Documentação interativa da API (Swagger): `http://localhost:9101/docs`.

## 3. Frontend do ANZ (porta 5173)

Crie `frontend/.env` (veja `frontend/.env.example`):

```env
VITE_API_BASE_URL=http://localhost:9101
VITE_SYNCRON_HUB_URL=http://localhost:5100
```

```bash
cd frontend
npm install
npm run dev
```

## 4. Simulando um login vindo do Hub

Com as três peças rodando, acesse:

```
http://localhost:5173/?token=valid-qualquer-coisa
```

Isso simula o redirecionamento que o Syncron Hub faria de verdade. Um token começando com `expired-plan`/`down`/qualquer outra coisa mostra as respectivas telas de bloqueio (ver `docs/ARCHITECTURE.md`).

## Testes automatizados

**Backend** (166 testes — pytest, cobre controle de acesso, pipeline de dados, IA, filtros/busca/análise, exportação/importação, cabeçalhos de segurança):

```bash
cd backend
.venv\Scripts\activate
pytest
```

**Frontend** (vitest + Testing Library — formatação, stores, filtros, os estados de acesso):

```bash
cd frontend
npm test
```

**Typecheck + build de produção do frontend** (roda antes de qualquer deploy):

```bash
cd frontend
npm run build
```
