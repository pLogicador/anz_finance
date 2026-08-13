# ANZ Finance 2.0 — Documentação

Índice da documentação deste projeto. Para o histórico de decisões, achados e validações de cada fase da reconstrução, veja o [`CLAUDE.md`](../CLAUDE.md) na raiz do repositório — este `docs/` é a versão "manual do usuário/operador", escrita para quem vai rodar, manter ou colocar o projeto no ar, não um log de sessão.

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** — como o sistema funciona: o modelo de acesso (Syncron Hub → token → sessão própria), por que não há banco de dados, o pipeline de dados (OFX/CSV → classificação → métricas), a estrutura de pastas do frontend e do backend.
- **[RUNNING_LOCALLY.md](./RUNNING_LOCALLY.md)** — como rodar cada peça localmente: backend, frontend, o mock do `subscription_access_api`, e como rodar as suítes de teste.
- **[DEPLOY.md](./DEPLOY.md)** — como publicar o backend no Railway e o frontend na Vercel, variáveis de ambiente necessárias em cada um, e um checklist de smoke test pós-deploy.

## O que é o ANZ Finance

Analisador de extratos bancários (OFX/CSV) com categorização por IA e um painel financeiro interativo. É um dos serviços do ecossistema Syncron — **não tem cadastro nem login próprio**: só é acessado a partir do Syncron Hub, que entrega um token validado contra o `subscription_access_api` central. Não existe banco de dados neste projeto — todos os dados de uma sessão (extratos enviados, transações classificadas, filtros salvos) vivem só em memória no processo do backend, com expiração automática (TTL), e somem quando a sessão termina ou o processo reinicia.

## Stack

- **Backend**: FastAPI (Python), sem banco de dados, deploy no Railway.
- **Frontend**: React 19 + Vite + TypeScript + Tailwind CSS v4, deploy na Vercel.
- **IA**: Groq e OpenAI (chat completions) para classificação de transações e o assistente de perguntas; nenhum outro provedor de IA é usado.
