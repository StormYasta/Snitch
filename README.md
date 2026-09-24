# Snitch

Plataforma web para consulta de atividade legislativa e navegação pela estrutura institucional brasileira.

## Escopo atual

O MVP possui duas dimensões conectadas:

- **Legislativa:** deputados, proposições, tramitações, votações, votos nominais, eventos e atividade parlamentar.
- **Institucional:** União, estados, Distrito Federal, municípios, Poderes e instituições públicas, com integração do Executivo Federal ao SIORG.

A aplicação não produz ranking político, nota de produtividade, avaliação ideológica ou recomendação eleitoral.

## Fontes

A aplicação possui uma tela pública em `/fontes` com links, finalidade de uso e data de acesso de cada fonte catalogada.

Fontes primárias:
- Câmara dos Deputados — Dados Abertos API v2
- Câmara dos Deputados — WebService de presença parlamentar em Plenário
- SIORG — Estruturas Organizacionais do Poder Executivo Federal
- Constituição Federal, além das páginas institucionais oficiais usadas na estrutura constitucional de alto nível

Os dados demonstrativos de `backend/app/data/seed_data.py` existem apenas para testes e desenvolvimento. Eles **não são carregados por padrão** e não devem ser tratados como dados oficiais.

## Stack

### Backend

- Python 3.11
- FastAPI
- SQLAlchemy
- PostgreSQL 16
- Alembic
- httpx
- pytest

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- TanStack Query
- Recharts
- Nginx no container de produção

## Subindo o projeto

```bash
docker compose up -d --build
```

Frontend:

```text
http://localhost:3000
```

Backend / Swagger:

```text
http://localhost:8000/docs
```

## Sincronizando a segunda etapa do MVP

Com os containers em execução:

```bash
docker compose exec backend python -m app.sync mvp2
```

O comando executa:

1. sincronização das legislaturas;
2. carga histórica de deputados por legislatura;
3. enriquecimento dos deputados da legislatura atual;
4. estrutura institucional de alto nível;
5. integração do Executivo Federal com SIORG.

A carga histórica pode realizar muitas requisições na primeira execução. O comando `mvp2`
**não importa proposições, votações nem eventos**. Essas cargas são independentes.

Se a carga histórica já terminou e somente o enriquecimento falhou, execute:

```bash
docker compose exec backend python -m app.sync enriquecer_deputados
```

O enriquecimento confirma cada deputado individualmente e mantém os anteriores
quando há erro. Pode ser executado novamente sem duplicar deputados nem mandatos.

Para importar proposições de um ano específico (até 100 por execução):

```bash
docker compose exec backend python -m app.sync proposicoes --ano 2026 --limite 100
docker compose exec backend python -m app.sync votacoes
docker compose exec backend python -m app.sync eventos
```

Importe as proposições antes das votações para que as matérias já existentes
possam ser associadas aos votos quando a API fornece a relação. A carga de
proposições é uma amostra paginada limitada; não representa todo o histórico
legislativo.

### Atualização de bases PostgreSQL já criadas

Bancos inicializados pelo `create_all` do FastAPI podem não possuir
`alembic_version`. Para uma instalação PostgreSQL existente, execute a
alteração **não destrutiva** antes de retomar o enriquecimento:

```bash
docker compose exec db psql -U snitch -d snitch_db -c "ALTER TABLE deputados ALTER COLUMN descricao_status TYPE TEXT; ALTER TABLE deputado_historico ALTER COLUMN descricao_status TYPE TEXT;"
```

A nova migração Alembic aplica a mesma alteração em bancos gerenciados por
revisões. Não execute `alembic upgrade head` diretamente sobre uma instalação
existente criada por `create_all` sem antes reconciliar seu histórico de
migrações. Nunca use `docker compose down -v` para resolver essa falha.

### Comandos individuais

```bash
docker compose exec backend python -m app.sync legislaturas
docker compose exec backend python -m app.sync deputados_historicos
docker compose exec backend python -m app.sync estrutura_governo
docker compose exec backend python -m app.sync siorg
```

Os comandos anteriores do MVP continuam disponíveis:

```bash
docker compose exec backend python -m app.sync deputados
docker compose exec backend python -m app.sync proposicoes
docker compose exec backend python -m app.sync votacoes
docker compose exec backend python -m app.sync eventos
```

## Dados demonstrativos

Para trabalhar sem depender das APIs externas:

```bash
docker compose exec -e LOAD_DEMO_SEED=true backend python -m app.sync seed
```

O seed contém fixtures demonstrativas e deve permanecer separado de bases usadas para consulta pública.

## Rotas principais

### Frontend

```text
/
/proposicoes
/proposicoes/:id
/deputados
/deputados/:id
/governo
/governo/instituicoes/:id
/fontes
```

### API

```text
GET /api/deputados
GET /api/deputados/{id}
GET /api/deputados/{id}/trajetoria
GET /api/deputados/{id}/temporal
GET /api/legislaturas

GET /api/proposicoes
GET /api/proposicoes/{id}

GET /api/votacoes/{id}
GET /api/votacoes/{id}/votos

GET /api/governo/estrutura
GET /api/governo/instituicoes
GET /api/governo/instituicoes/{id}
GET /api/governo/busca
```

## Modelo histórico

A pessoa e sua trajetória parlamentar são preservadas separadamente:

```text
Deputado / pessoa parlamentar
  ├── Mandatos
  │    └── Legislatura + partido + UF + período
  ├── Histórico oficial
  ├── Votos
  └── Proposições
```

Uma votação antiga pode, portanto, mostrar o partido registrado no momento do voto sem substituir essa informação pelo partido atual.

## Mapa institucional

As relações institucionais são tipadas. A aplicação diferencia, entre outras:

- `COMPOSICAO`
- `HIERARQUIA_ADMINISTRATIVA`
- `VINCULACAO`
- `CONTROLE`
- `FISCALIZACAO`

O mapa principal é compacto. Unidades internas do Executivo sincronizadas pelo SIORG ficam disponíveis ao navegar pelos detalhes das instituições, evitando renderizar milhares de nós de uma só vez.

## Testes

Backend:

```bash
cd backend
pytest -q
```

Frontend:

```bash
cd frontend
npm ci
npm run build
```

A branch também possui GitHub Actions executando os dois fluxos.

## Princípios do projeto

- dado oficial acima de inferência;
- preservação histórica;
- neutralidade política;
- rastreabilidade das fontes;
- nenhuma classificação de "melhor" ou "pior" parlamentar;
- relações institucionais não são reduzidas a uma cadeia única de comando.
