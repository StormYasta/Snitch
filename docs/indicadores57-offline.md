# Indicadores legislativos offline — 57ª Legislatura

Para redes que bloqueiam os serviços da Câmara, o Snitch mantém um snapshot
oficial separado dos dados demonstrativos.

O arquivo `backend/app/data/indicadores57_offline.json` guarda:
- PLs de autoria dos 100 deputados por ano, de 2023 ao ano atual;
- quantidade cuja situação textual retornada pela Câmara é compatível com
  aprovação/sanção/transformação em norma (o rótulo não é juízo de mérito);
- presença/faltas de Plenário para o mês do snapshot, via SitCamaraWS;
- valor líquido da CEAP para o mesmo mês;
- quantidade de votações nominais existentes na amostra offline do showcase.

O snapshot **não inventa zero** para uma fonte que falhou: ausência de dados é
mantida como nulo. A página e o comparativo sinalizam quando um indicador vem
do snapshot ou quando o total de votações corresponde somente à amostra.

Para atualizar o snapshot usa-se o workflow
`Refresh 57th Legislature offline indicators`. Ele também roda mensalmente.

Após o GitHub Actions gerar o arquivo, no computador bloqueado basta:

```powershell
git pull origin feat/mvp2-governo-historico
docker compose up -d --build
```

Não há importação separada: o backend lê o snapshot como fallback e continua
preferindo a fonte online quando ela estiver acessível para presença e CEAP.
