# Base offline da 57ª Legislatura

Esta base existe para desenvolvimento em redes que não conseguem acessar
`dadosabertos.camara.leg.br`. Ela é uma **amostra oficial e não representativa**.

Conteúdo atual:
- 100 perfis do snapshot offline de deputados;
- até 20 votações com registros individuais por ano, de 2023 a 2026;
- votos registrados dos 100 perfis nessas votações;
- orientações de bancada;
- proposição-objeto quando informada pela API;
- autores e temas das proposições-objeto encontradas.

A seleção de votações é temporal e automática. Não utiliza partido, parlamentar,
tema, resultado, voto Sim/Não ou qualquer avaliação política como critério.

Para carregar no banco local:

```bash
docker compose exec backend python -m app.sync base57_offline
```

A carga faz upsert e **não apaga votos de deputados fora do snapshot** que já
tenham sido sincronizados por outra fonte.

O arquivo `base57_showcase.json.gz` é gerado pelo GitHub Actions a partir da
API v2 oficial. A metadata interna registra a data de acesso e as limitações.
