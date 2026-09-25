# Snitch: Supabase + FastAPI + GitHub Pages

Esta branch implementa um **modelo híbrido**:

```text
GitHub Pages (React/Vite, estático)
              |
              | HTTPS: VITE_API_URL
              v
FastAPI (hospedagem separada, HTTPS)
       /                       \
      v                         v
Supabase/PostgreSQL       APIs oficiais da Câmara
Histórico, vínculos       Presença e cota sob demanda
votos, proposições        Cache persistente com TTL
```

**GitHub Pages não executa FastAPI, Docker, Python ou tarefas de
sincronização.** Não exponha `DATABASE_URL`, a senha PostgreSQL nem
`SYNC_ADMIN_TOKEN` no frontend, nas variáveis VITE_* ou no repositório.

## 1. Criar o Supabase

1. Crie um projeto novo (sem tabelas de Snitch já existentes).
2. Abra **SQL Editor → New query** e cole o conteúdo completo de
   [`supabase/schema.sql`](../supabase/schema.sql). Execute **uma vez**.
3. O script cria as 22 tabelas atuais, índices, relacionamentos,
   `official_cache` e `alembic_version` (revisão
   `a64b8f27c901`), e ativa **RLS sem políticas para anon** nas
   tabelas do Snitch. O acesso ao banco será apenas pelo FastAPI.
4. Confira no Table Editor `deputados`, `proposicoes`,
   `votacoes`, `votos`, `instituicoes` e `official_cache`.
   O banco recém-criado está vazio até a primeira sincronização.

**Bancos Supabase já preenchidos:** não rode o schema.sql sobre um banco
existente; use as migrações Alembic após reconciliar a versão atual e
aplique a segurança RLS explicitamente. Não use `alembic stamp` sem
conferir quais migrações foram realmente aplicadas.

## 2. Configurar o backend

No painel Supabase, abra **Connect → Session Pooler** (porta 5432);
essa opção normalmente funciona também em ambientes que só oferecem IPv4.
Copie o endereço completo da conexão. Prefira SSL e inclua
`sslmode=require`. Senhas com caracteres especiais precisam ser
codificadas para URL. A conexão direta pode exigir IPv6.
Confira sempre o endereço exato mostrado pelo seu projeto.

Copie `backend/.env.example` para `backend/.env` e configure:

```dotenv
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@POOLER_HOST:5432/postgres?sslmode=require
AUTO_CREATE_TABLES=false
LOAD_DEMO_SEED=false
CORS_ORIGINS='["https://stormyasta.github.io","http://localhost:5173","http://localhost:3000"]'
SYNC_ADMIN_TOKEN=SEU_TOKEN_ALEATORIO_LONGO
PRESENCE_TTL_HOURS=6
EXPENSES_TTL_HOURS=24
```

`CORS_ORIGINS` deve incluir o **origin** do GitHub Pages, sem
`/Snitch`. Se usar um domínio próprio, ajuste o valor.

O FastAPI deve ser hospedado em um serviço **separado**, com HTTPS
e acesso de saída à Câmara e ao Supabase (por exemplo, um container
persistente). Configure essas variáveis **somente no ambiente do backend**.
Na instalação com schema.sql completo, as tabelas já existem e não
se deve usar `create_all` em produção.

Para desenvolvimento local usando o mesmo Supabase, sem o Postgres
local do Docker:

```bash
docker compose -f docker-compose.supabase.yml up -d --build
```

Frontend em `http://localhost:3000` e API em
`http://localhost:8000/docs`. O frontend Docker usa o proxy nginx
interno; o build GitHub Pages usa a URL pública `VITE_API_URL`.

Se escolher migrar por Alembic em um banco **novo e vazio**, no lugar
do SQL Editor, use `cd backend && alembic upgrade head`, depois
configure/valide a segurança de **todas** as tabelas: o bootstrap SQL
da pasta `supabase` inclui essa proteção de forma explícita.
Não execute as duas formas de criação no mesmo projeto.

## 3. Sincronizar histórico e iniciar o cache

Execute os comandos no ambiente do backend com a `DATABASE_URL`
configurada. A criação do banco, por si só, **não popula dados**.

```bash
python -m app.sync deputados
python -m app.sync legislaturas
python -m app.sync historico --ano-inicial 2025 --ano-final 2026
python -m app.sync siorg
```

A importação histórica pode levar horas e permite dividir por ano/tipo.
Proposições e vínculos temáticos devem ser sincronizados antes
das votações quando possível. As consultas de **presença** e **cota**
são realizadas ao acessar os indicadores de um deputado:
cache de 6h e 24h, respectivamente (configuráveis). Se uma fonte cair,
o Snitch usa o último snapshot válido e informa sua data, ou exibe
indisponibilidade se nunca conseguiu consultar.

Para sincronizações futuras, configure um job periódico no host do
backend ou execute manualmente os comandos da aplicação; **o GitHub Pages
não agenda jobs e o cache não substitui a carga histórica**.

O endpoint administrativo `POST /api/sync/trigger` exige o header
`X-Snitch-Sync-Token` e rejeita carga demonstrativa (`seed`).
Não exponha esse token no frontend.

## 4. Publicar no GitHub Pages

1. Hospede o FastAPI publicamente com URL HTTPS, por exemplo
   `https://api.exemplo.com/api` (o hostname é ilustrativo).
2. No GitHub, entre em **Settings → Secrets and variables → Actions →
   Variables** e crie **`VITE_API_URL`** com a URL da API terminada
   em `/api`. Essa variável é pública no JavaScript compilado;
   não coloque credenciais nela.
3. Em **Settings → Pages → Build and deployment**, selecione
   **Source: GitHub Actions**.
4. Faça merge da branch após validação. O workflow
   `.github/workflows/pages.yml` publica automaticamente quando o
   frontend da `main` é atualizado. Também permite execução manual.
   Antes do merge, esta branch **não está publicada em Pages**.

Para o repositório `StormYasta/Snitch`, o workflow usa
`VITE_BASE_PATH=/Snitch/` e `VITE_ROUTER_MODE=hash`.
Assim, rotas profundas não dependem de reescrita no GitHub Pages:
`https://stormyasta.github.io/Snitch/#/comparar`.

Se publicar em domínio próprio na raiz, ajuste
`VITE_BASE_PATH=/` no workflow.

## 5. Como os dados ficam distribuídos

| Recurso | Origem primária | Persistência local |
|---|---|---|
| Deputados, mandatos e histórico | Câmara | Supabase, sincronização |
| Proposições, temas, tramitações | Câmara | Supabase, sincronização |
| Votações, votos e vínculos | Câmara | Supabase, sincronização |
| Estrutura institucional | Constituição, SIORG e órgãos oficiais | Supabase |
| Presença no Plenário | WebService da Câmara | Cache por deputado/mês |
| Uso da cota | API v2 da Câmara | Cache por deputado/mês |

`GET /api/fontes/status` expõe apenas o registro das consultas
e sincronizações, não dados administrativos nem segredos.
Na página `/fontes`, a data de conferência editorial do link é
mostrada separadamente da última consulta **efetivamente registrada**
pelo Snitch.

## 6. Testes e segurança

O CI existente roda testes de FastAPI e build Vite. Também há um job
`supabase-schema` que executa o schema.sql em um PostgreSQL 16 limpo,
cria os papéis anon/authenticated/service_role para simulação e
verifica as tabelas, a versão do Alembic e o RLS.

No Supabase real, não dê grants de escrita aos papéis de navegador,
não exponha a `service_role` e nunca coloque uma senha PostgreSQL
em Actions Variables para o frontend. Configure backups e limites
de recursos conforme o plano contratado.

**Atenção:** a implementação foi testada no CI, mas a conectividade
com o seu projeto Supabase, o domínio do backend e a disponibilidade
dos serviços oficiais só podem ser confirmados após configurar seu
ambiente real.
