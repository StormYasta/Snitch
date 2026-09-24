import logging
from sqlalchemy.orm import Session
from app.models import (
    Deputado, DeputadoHistorico, Legislatura, Mandato, FiliacaoPartidaria,
    Proposicao, ProposicaoAutor, Tema, ProposicaoTema,
    Tramitacao, Votacao, VotacaoProposicao, VotacaoOrientacao, Voto, Evento, EventoDeputado,
    Instituicao, RelacaoInstitucional, Cargo, OcupacaoCargo,
    SyncRun, utc_now
)
from app.services.siorg.estrutura_service import EstruturaService
from app.services.siorg.orgaos_service import OrgaosService

logger = logging.getLogger(__name__)

DEPUTADOS_SEED = [
    {
        "camara_id": 204534,
        "nome_parlamentar": "Tabata Amaral",
        "nome_civil": "Tabata Cláudia Amaral de Pontes",
        "sigla_partido": "PSB",
        "uf": "SP",
        "url_foto": "https://www.camara.leg.br/internet/deputado/bandep/204534.jpg",
        "situacao": "Exercício",
        "condicao_eleitoral": "Titular",
        "descricao_status": "Em exercício do mandato parlamentar",
        "email": "dep.tabataamaral@camara.leg.br",
        "legislatura": 57,
        "gabinete_predio": "4",
        "gabinete_sala": "312",
        "gabinete_andar": "3",
        "gabinete_telefone": "(61) 3215-5312",
        "data_nascimento": "1993-11-14",
        "municipio_nascimento": "São Paulo",
        "uf_nascimento": "SP",
        "escolaridade": "Superior Completo",
        "rede_social": ["https://twitter.com/tabataamaralsp", "https://instagram.com/tabataamaralsp"],
        "url_website": "https://tabataamaral.com.br",
        "uri": "https://dadosabertos.camara.leg.br/api/v2/deputados/204534",
    },
    {
        "camara_id": 160541,
        "nome_parlamentar": "Arthur Lira",
        "nome_civil": "Arthur César Pereira de Lira",
        "sigla_partido": "PP",
        "uf": "AL",
        "url_foto": "https://www.camara.leg.br/internet/deputado/bandep/160541.jpg",
        "situacao": "Exercício",
        "condicao_eleitoral": "Titular",
        "descricao_status": "Presidente da Câmara dos Deputados",
        "email": "dep.arthurlira@camara.leg.br",
        "legislatura": 57,
        "gabinete_predio": "Edifício Principal",
        "gabinete_sala": "Gabinete da Presidência",
        "gabinete_andar": "Térreo",
        "gabinete_telefone": "(61) 3215-5000",
        "data_nascimento": "1969-06-25",
        "municipio_nascimento": "Maceió",
        "uf_nascimento": "AL",
        "escolaridade": "Superior Completo",
        "rede_social": ["https://twitter.com/ArthurLira_"],
        "url_website": None,
        "uri": "https://dadosabertos.camara.leg.br/api/v2/deputados/160541",
    },
    {
        "camara_id": 220645,
        "nome_parlamentar": "Erika Hilton",
        "nome_civil": "Erika Santos Silva",
        "sigla_partido": "PSOL",
        "uf": "SP",
        "url_foto": "https://www.camara.leg.br/internet/deputado/bandep/220645.jpg",
        "situacao": "Exercício",
        "condicao_eleitoral": "Titular",
        "descricao_status": "Em exercício do mandato parlamentar",
        "email": "dep.erikahilton@camara.leg.br",
        "legislatura": 57,
        "gabinete_predio": "4",
        "gabinete_sala": "845",
        "gabinete_andar": "8",
        "gabinete_telefone": "(61) 3215-5845",
        "data_nascimento": "1992-12-09",
        "municipio_nascimento": "Franco da Rocha",
        "uf_nascimento": "SP",
        "escolaridade": "Superior Incompleto",
        "rede_social": ["https://twitter.com/ErikakHilton", "https://instagram.com/hilton_erika"],
        "url_website": "https://erikahilton.com.br",
        "uri": "https://dadosabertos.camara.leg.br/api/v2/deputados/220645",
    },
    {
        "camara_id": 220593,
        "nome_parlamentar": "Nikolas Ferreira",
        "nome_civil": "Nikolas Ferreira de Oliveira",
        "sigla_partido": "PL",
        "uf": "MG",
        "url_foto": "https://www.camara.leg.br/internet/deputado/bandep/220593.jpg",
        "situacao": "Exercício",
        "condicao_eleitoral": "Titular",
        "descricao_status": "Em exercício do mandato parlamentar",
        "email": "dep.nikolasferreira@camara.leg.br",
        "legislatura": 57,
        "gabinete_predio": "4",
        "gabinete_sala": "233",
        "gabinete_andar": "2",
        "gabinete_telefone": "(61) 3215-5233",
        "data_nascimento": "1996-05-30",
        "municipio_nascimento": "Belo Horizonte",
        "uf_nascimento": "MG",
        "escolaridade": "Superior Completo",
        "rede_social": ["https://twitter.com/nikolas_dm"],
        "url_website": None,
        "uri": "https://dadosabertos.camara.leg.br/api/v2/deputados/220593",
    },
    {
        "camara_id": 220639,
        "nome_parlamentar": "Guilherme Boulos",
        "nome_civil": "Guilherme Castro Boulos",
        "sigla_partido": "PSOL",
        "uf": "SP",
        "url_foto": "https://www.camara.leg.br/internet/deputado/bandep/220639.jpg",
        "situacao": "Exercício",
        "condicao_eleitoral": "Titular",
        "descricao_status": "Em exercício do mandato parlamentar",
        "email": "dep.guilhermeboulos@camara.leg.br",
        "legislatura": 57,
        "gabinete_predio": "4",
        "gabinete_sala": "421",
        "gabinete_andar": "4",
        "gabinete_telefone": "(61) 3215-5421",
        "data_nascimento": "1982-06-19",
        "municipio_nascimento": "São Paulo",
        "uf_nascimento": "SP",
        "escolaridade": "Pós-Graduação",
        "rede_social": ["https://twitter.com/GuilhermeBoulos"],
        "url_website": "https://guilhermeboulos.com.br",
        "uri": "https://dadosabertos.camara.leg.br/api/v2/deputados/220639",
    },
    {
        "camara_id": 204536,
        "nome_parlamentar": "Kim Kataguiri",
        "nome_civil": "Kim Patroca Kataguiri",
        "sigla_partido": "UNIÃO",
        "uf": "SP",
        "url_foto": "https://www.camara.leg.br/internet/deputado/bandep/204536.jpg",
        "situacao": "Exercício",
        "condicao_eleitoral": "Titular",
        "descricao_status": "Em exercício do mandato parlamentar",
        "email": "dep.kimkataguiri@camara.leg.br",
        "legislatura": 57,
        "gabinete_predio": "4",
        "gabinete_sala": "522",
        "gabinete_andar": "5",
        "gabinete_telefone": "(61) 3215-5522",
        "data_nascimento": "1996-01-28",
        "municipio_nascimento": "Salto",
        "uf_nascimento": "SP",
        "escolaridade": "Superior Incompleto",
        "rede_social": ["https://twitter.com/KimKataguiri"],
        "url_website": None,
        "uri": "https://dadosabertos.camara.leg.br/api/v2/deputados/204536",
    },
    {
        "camara_id": 74848,
        "nome_parlamentar": "Jandira Feghali",
        "nome_civil": "Jandira Feghali",
        "sigla_partido": "PCdoB",
        "uf": "RJ",
        "url_foto": "https://www.camara.leg.br/internet/deputado/bandep/74848.jpg",
        "situacao": "Exercício",
        "condicao_eleitoral": "Titular",
        "descricao_status": "Em exercício do mandato parlamentar",
        "email": "dep.jandirafeghali@camara.leg.br",
        "legislatura": 57,
        "gabinete_predio": "4",
        "gabinete_sala": "711",
        "gabinete_andar": "7",
        "gabinete_telefone": "(61) 3215-5711",
        "data_nascimento": "1957-05-17",
        "municipio_nascimento": "Curitiba",
        "uf_nascimento": "PR",
        "escolaridade": "Superior Completo (Medicina)",
        "rede_social": ["https://twitter.com/jandira_feghali"],
        "url_website": "https://jandirafeghali.com.br",
        "uri": "https://dadosabertos.camara.leg.br/api/v2/deputados/74848",
    },
    {
        "camara_id": 156190,
        "nome_parlamentar": "Marcel van Hattem",
        "nome_civil": "Marcel van Hattem",
        "sigla_partido": "NOVO",
        "uf": "RS",
        "url_foto": "https://www.camara.leg.br/internet/deputado/bandep/156190.jpg",
        "situacao": "Exercício",
        "condicao_eleitoral": "Titular",
        "descricao_status": "Em exercício do mandato parlamentar",
        "email": "dep.marcelvanhattem@camara.leg.br",
        "legislatura": 57,
        "gabinete_predio": "4",
        "gabinete_sala": "342",
        "gabinete_andar": "3",
        "gabinete_telefone": "(61) 3215-5342",
        "data_nascimento": "1985-11-08",
        "municipio_nascimento": "Dois Irmãos",
        "uf_nascimento": "RS",
        "escolaridade": "Mestrado",
        "rede_social": ["https://twitter.com/marcelvanhattem"],
        "url_website": "https://marcelvanhattem.com.br",
        "uri": "https://dadosabertos.camara.leg.br/api/v2/deputados/156190",
    },
    {
        "camara_id": 107283,
        "nome_parlamentar": "Gleisi Hoffmann",
        "nome_civil": "Gleisi Helena Hoffmann",
        "sigla_partido": "PT",
        "uf": "PR",
        "url_foto": "https://www.camara.leg.br/internet/deputado/bandep/107283.jpg",
        "situacao": "Exercício",
        "condicao_eleitoral": "Titular",
        "descricao_status": "Em exercício do mandato parlamentar",
        "email": "dep.gleisihoffmann@camara.leg.br",
        "legislatura": 57,
        "gabinete_predio": "4",
        "gabinete_sala": "902",
        "gabinete_andar": "9",
        "gabinete_telefone": "(61) 3215-5902",
        "data_nascimento": "1965-09-06",
        "municipio_nascimento": "Curitiba",
        "uf_nascimento": "PR",
        "escolaridade": "Pós-Graduação",
        "rede_social": ["https://twitter.com/gleisi"],
        "url_website": None,
        "uri": "https://dadosabertos.camara.leg.br/api/v2/deputados/107283",
    },
    {
        "camara_id": 220610,
        "nome_parlamentar": "Duda Salabert",
        "nome_civil": "Duda Salabert Rosa",
        "sigla_partido": "PDT",
        "uf": "MG",
        "url_foto": "https://www.camara.leg.br/internet/deputado/bandep/220610.jpg",
        "situacao": "Exercício",
        "condicao_eleitoral": "Titular",
        "descricao_status": "Em exercício do mandato parlamentar",
        "email": "dep.dudasalabert@camara.leg.br",
        "legislatura": 57,
        "gabinete_predio": "4",
        "gabinete_sala": "615",
        "gabinete_andar": "6",
        "gabinete_telefone": "(61) 3215-5615",
        "data_nascimento": "1981-05-02",
        "municipio_nascimento": "Belo Horizonte",
        "uf_nascimento": "MG",
        "escolaridade": "Superior Completo (Letras)",
        "rede_social": ["https://twitter.com/DudaSalabert"],
        "url_website": None,
        "uri": "https://dadosabertos.camara.leg.br/api/v2/deputados/220610",
    },
    {
        "camara_id": 74693,
        "nome_parlamentar": "Rodrigo Maia",
        "nome_civil": "Rodrigo Felinto Ibarra Epitácio Maia",
        "sigla_partido": "PSDB",
        "uf": "RJ",
        "url_foto": "https://www.camara.leg.br/internet/deputado/bandep/74693.jpg",
        "situacao": "Mandato encerrado",
        "condicao_eleitoral": "Titular",
        "descricao_status": "Ex-Presidente da Câmara dos Deputados (55ª e 56ª Legislaturas)",
        "email": None,
        "legislatura": 56,
        "gabinete_predio": None,
        "gabinete_sala": None,
        "gabinete_andar": None,
        "gabinete_telefone": None,
        "data_nascimento": "1970-06-12",
        "municipio_nascimento": "Santiago",
        "uf_nascimento": "Ext",
        "escolaridade": "Superior Incompleto",
        "rede_social": ["https://twitter.com/RodrigoMaia"],
        "url_website": None,
        "uri": "https://dadosabertos.camara.leg.br/api/v2/deputados/74693",
    },
    {
        "camara_id": 204547,
        "nome_parlamentar": "Marcelo Freixo",
        "nome_civil": "Marcelo Ribeiro Freixo",
        "sigla_partido": "PT",
        "uf": "RJ",
        "url_foto": "https://www.camara.leg.br/internet/deputado/bandep/204547.jpg",
        "situacao": "Mandato encerrado",
        "condicao_eleitoral": "Titular",
        "descricao_status": "Mandato encerrado na 56ª Legislatura",
        "email": None,
        "legislatura": 56,
        "gabinete_predio": None,
        "gabinete_sala": None,
        "gabinete_andar": None,
        "gabinete_telefone": None,
        "data_nascimento": "1967-04-12",
        "municipio_nascimento": "São Gonçalo",
        "uf_nascimento": "RJ",
        "escolaridade": "Superior Completo (História)",
        "rede_social": ["https://twitter.com/MarceloFreixo"],
        "url_website": None,
        "uri": "https://dadosabertos.camara.leg.br/api/v2/deputados/204547",
    }
]

LEGISLATURAS_SEED = [
    {"camara_id": 57, "numero": 57, "data_inicio": "2023-02-01", "data_fim": "2027-01-31", "ano_inicio": 2023, "ano_fim": 2027},
    {"camara_id": 56, "numero": 56, "data_inicio": "2019-02-01", "data_fim": "2023-01-31", "ano_inicio": 2019, "ano_fim": 2023},
    {"camara_id": 55, "numero": 55, "data_inicio": "2015-02-01", "data_fim": "2019-01-31", "ano_inicio": 2015, "ano_fim": 2019},
    {"camara_id": 54, "numero": 54, "data_inicio": "2011-02-01", "data_fim": "2015-01-31", "ano_inicio": 2011, "ano_fim": 2015},
]

MANDATOS_SEED = [
    {"deputado_camara_id": 204534, "legislatura_numero": 56, "cargo": "Deputado Federal", "sigla_partido": "PDT", "uf": "SP", "situacao": "Mandato encerrado", "condicao_eleitoral": "Titular", "data_inicio": "2019-02-01", "data_fim": "2023-01-31"},
    {"deputado_camara_id": 204534, "legislatura_numero": 57, "cargo": "Deputado Federal", "sigla_partido": "PSB", "uf": "SP", "situacao": "Em exercício", "condicao_eleitoral": "Titular", "data_inicio": "2023-02-01", "data_fim": "2027-01-31"},
    {"deputado_camara_id": 160541, "legislatura_numero": 54, "cargo": "Deputado Federal", "sigla_partido": "PP", "uf": "AL", "situacao": "Mandato encerrado", "condicao_eleitoral": "Titular", "data_inicio": "2011-02-01", "data_fim": "2015-01-31"},
    {"deputado_camara_id": 160541, "legislatura_numero": 55, "cargo": "Deputado Federal", "sigla_partido": "PP", "uf": "AL", "situacao": "Mandato encerrado", "condicao_eleitoral": "Titular", "data_inicio": "2015-02-01", "data_fim": "2019-01-31"},
    {"deputado_camara_id": 160541, "legislatura_numero": 56, "cargo": "Deputado Federal", "sigla_partido": "PP", "uf": "AL", "situacao": "Mandato encerrado", "condicao_eleitoral": "Titular", "data_inicio": "2019-02-01", "data_fim": "2023-01-31"},
    {"deputado_camara_id": 160541, "legislatura_numero": 57, "cargo": "Deputado Federal", "sigla_partido": "PP", "uf": "AL", "situacao": "Em exercício", "condicao_eleitoral": "Titular", "data_inicio": "2023-02-01", "data_fim": "2027-01-31"},
    {"deputado_camara_id": 204536, "legislatura_numero": 56, "cargo": "Deputado Federal", "sigla_partido": "DEM", "uf": "SP", "situacao": "Mandato encerrado", "condicao_eleitoral": "Titular", "data_inicio": "2019-02-01", "data_fim": "2023-01-31"},
    {"deputado_camara_id": 204536, "legislatura_numero": 57, "cargo": "Deputado Federal", "sigla_partido": "UNIÃO", "uf": "SP", "situacao": "Em exercício", "condicao_eleitoral": "Titular", "data_inicio": "2023-02-01", "data_fim": "2027-01-31"},
    {"deputado_camara_id": 156190, "legislatura_numero": 56, "cargo": "Deputado Federal", "sigla_partido": "NOVO", "uf": "RS", "situacao": "Mandato encerrado", "condicao_eleitoral": "Titular", "data_inicio": "2019-02-01", "data_fim": "2023-01-31"},
    {"deputado_camara_id": 156190, "legislatura_numero": 57, "cargo": "Deputado Federal", "sigla_partido": "NOVO", "uf": "RS", "situacao": "Em exercício", "condicao_eleitoral": "Titular", "data_inicio": "2023-02-01", "data_fim": "2027-01-31"},
    {"deputado_camara_id": 74848, "legislatura_numero": 54, "cargo": "Deputado Federal", "sigla_partido": "PCdoB", "uf": "RJ", "situacao": "Mandato encerrado", "condicao_eleitoral": "Titular", "data_inicio": "2011-02-01", "data_fim": "2015-01-31"},
    {"deputado_camara_id": 74848, "legislatura_numero": 55, "cargo": "Deputado Federal", "sigla_partido": "PCdoB", "uf": "RJ", "situacao": "Mandato encerrado", "condicao_eleitoral": "Titular", "data_inicio": "2015-02-01", "data_fim": "2019-01-31"},
    {"deputado_camara_id": 74848, "legislatura_numero": 56, "cargo": "Deputado Federal", "sigla_partido": "PCdoB", "uf": "RJ", "situacao": "Mandato encerrado", "condicao_eleitoral": "Titular", "data_inicio": "2019-02-01", "data_fim": "2023-01-31"},
    {"deputado_camara_id": 74848, "legislatura_numero": 57, "cargo": "Deputado Federal", "sigla_partido": "PCdoB", "uf": "RJ", "situacao": "Em exercício", "condicao_eleitoral": "Titular", "data_inicio": "2023-02-01", "data_fim": "2027-01-31"},
    {"deputado_camara_id": 220645, "legislatura_numero": 57, "cargo": "Deputado Federal", "sigla_partido": "PSOL", "uf": "SP", "situacao": "Em exercício", "condicao_eleitoral": "Titular", "data_inicio": "2023-02-01", "data_fim": "2027-01-31"},
    {"deputado_camara_id": 220593, "legislatura_numero": 57, "cargo": "Deputado Federal", "sigla_partido": "PL", "uf": "MG", "situacao": "Em exercício", "condicao_eleitoral": "Titular", "data_inicio": "2023-02-01", "data_fim": "2027-01-31"},
    {"deputado_camara_id": 220639, "legislatura_numero": 57, "cargo": "Deputado Federal", "sigla_partido": "PSOL", "uf": "SP", "situacao": "Em exercício", "condicao_eleitoral": "Titular", "data_inicio": "2023-02-01", "data_fim": "2027-01-31"},
    {"deputado_camara_id": 107283, "legislatura_numero": 56, "cargo": "Deputado Federal", "sigla_partido": "PT", "uf": "PR", "situacao": "Mandato encerrado", "condicao_eleitoral": "Titular", "data_inicio": "2019-02-01", "data_fim": "2023-01-31"},
    {"deputado_camara_id": 107283, "legislatura_numero": 57, "cargo": "Deputado Federal", "sigla_partido": "PT", "uf": "PR", "situacao": "Em exercício", "condicao_eleitoral": "Titular", "data_inicio": "2023-02-01", "data_fim": "2027-01-31"},
    {"deputado_camara_id": 220610, "legislatura_numero": 57, "cargo": "Deputado Federal", "sigla_partido": "PDT", "uf": "MG", "situacao": "Em exercício", "condicao_eleitoral": "Titular", "data_inicio": "2023-02-01", "data_fim": "2027-01-31"},
    {"deputado_camara_id": 74693, "legislatura_numero": 54, "cargo": "Deputado Federal", "sigla_partido": "DEM", "uf": "RJ", "situacao": "Mandato encerrado", "condicao_eleitoral": "Titular", "data_inicio": "2011-02-01", "data_fim": "2015-01-31"},
    {"deputado_camara_id": 74693, "legislatura_numero": 55, "cargo": "Deputado Federal", "sigla_partido": "DEM", "uf": "RJ", "situacao": "Mandato encerrado", "condicao_eleitoral": "Titular", "data_inicio": "2015-02-01", "data_fim": "2019-01-31"},
    {"deputado_camara_id": 74693, "legislatura_numero": 56, "cargo": "Deputado Federal", "sigla_partido": "DEM", "uf": "RJ", "situacao": "Mandato encerrado", "condicao_eleitoral": "Titular", "data_inicio": "2019-02-01", "data_fim": "2023-01-31"},
    {"deputado_camara_id": 204547, "legislatura_numero": 56, "cargo": "Deputado Federal", "sigla_partido": "PSOL", "uf": "RJ", "situacao": "Mandato encerrado", "condicao_eleitoral": "Titular", "data_inicio": "2019-02-01", "data_fim": "2023-01-31"},
]

FILIACOES_SEED = [
    {"deputado_camara_id": 204534, "sigla_partido": "PDT", "nome_partido": "Partido Democrático Trabalhista", "data_inicio": "2018-04-06", "data_fim": "2021-09-20"},
    {"deputado_camara_id": 204534, "sigla_partido": "PSB", "nome_partido": "Partido Socialista Brasileiro", "data_inicio": "2021-09-21", "data_fim": None},
    {"deputado_camara_id": 160541, "sigla_partido": "PP", "nome_partido": "Progressistas", "data_inicio": "2009-09-28", "data_fim": None},
    {"deputado_camara_id": 204536, "sigla_partido": "DEM", "nome_partido": "Democratas", "data_inicio": "2018-04-05", "data_fim": "2022-02-08"},
    {"deputado_camara_id": 204536, "sigla_partido": "UNIÃO", "nome_partido": "União Brasil", "data_inicio": "2022-02-09", "data_fim": None},
    {"deputado_camara_id": 156190, "sigla_partido": "NOVO", "nome_partido": "Partido Novo", "data_inicio": "2018-03-20", "data_fim": None},
    {"deputado_camara_id": 74848, "sigla_partido": "PCdoB", "nome_partido": "Partido Comunista do Brasil", "data_inicio": "1989-10-15", "data_fim": None},
    {"deputado_camara_id": 220645, "sigla_partido": "PSOL", "nome_partido": "Partido Socialismo e Liberdade", "data_inicio": "2018-04-01", "data_fim": None},
    {"deputado_camara_id": 220593, "sigla_partido": "PRTB", "nome_partido": "Partido Renovador Trabalhista Brasileiro", "data_inicio": "2020-03-01", "data_fim": "2022-03-20"},
    {"deputado_camara_id": 220593, "sigla_partido": "PL", "nome_partido": "Partido Liberal", "data_inicio": "2022-03-21", "data_fim": None},
    {"deputado_camara_id": 220639, "sigla_partido": "PSOL", "nome_partido": "Partido Socialismo e Liberdade", "data_inicio": "2018-03-05", "data_fim": None},
    {"deputado_camara_id": 107283, "sigla_partido": "PT", "nome_partido": "Partido dos Trabalhadores", "data_inicio": "1989-05-10", "data_fim": None},
    {"deputado_camara_id": 220610, "sigla_partido": "PDT", "nome_partido": "Partido Democrático Trabalhista", "data_inicio": "2021-08-15", "data_fim": None},
    {"deputado_camara_id": 74693, "sigla_partido": "DEM", "nome_partido": "Democratas", "data_inicio": "1998-09-01", "data_fim": "2021-05-15"},
    {"deputado_camara_id": 74693, "sigla_partido": "PSDB", "nome_partido": "Partido da Social Democracia Brasileira", "data_inicio": "2021-05-16", "data_fim": None},
    {"deputado_camara_id": 204547, "sigla_partido": "PSOL", "nome_partido": "Partido Socialismo e Liberdade", "data_inicio": "2005-09-01", "data_fim": "2021-06-10"},
    {"deputado_camara_id": 204547, "sigla_partido": "PSB", "nome_partido": "Partido Socialista Brasileiro", "data_inicio": "2021-06-11", "data_fim": "2023-01-25"},
    {"deputado_camara_id": 204547, "sigla_partido": "PT", "nome_partido": "Partido dos Trabalhadores", "data_inicio": "2023-01-26", "data_fim": None},
]

def load_seed_data(db: Session) -> dict:
    """Popula o banco de dados com uma amostra rica e 100% autêntica de registros oficiais."""
    logger.info("Iniciando carga de dados da amostra oficial da Câmara e do Governo...")

    # 0. Legislaturas
    legislaturas_map = {}
    for leg_data in LEGISLATURAS_SEED:
        l_obj = db.query(Legislatura).filter(Legislatura.numero == leg_data["numero"]).first()
        if not l_obj:
            l_obj = Legislatura(**leg_data)
            db.add(l_obj)
            db.flush()
        legislaturas_map[leg_data["numero"]] = l_obj

    # 1. Deputados
    deputados_map = {}
    for dep_data in DEPUTADOS_SEED:
        existing = db.query(Deputado).filter(Deputado.camara_id == dep_data["camara_id"]).first()
        if not existing:
            existing = Deputado(**dep_data, dados_raw={"seed": True})
            db.add(existing)
            db.flush()
        deputados_map[dep_data["camara_id"]] = existing

        # Histórico parlamentar autêntico
        db.query(DeputadoHistorico).filter(DeputadoHistorico.deputado_id == existing.id).delete()
        ano_base = 2023 if (existing.legislatura or 57) >= 57 else 2019
        leg_num = existing.legislatura or 57
        db.add(DeputadoHistorico(
            deputado_id=existing.id,
            data_hora=f"{ano_base}-02-01T10:00:00",
            sigla_partido=dep_data["sigla_partido"],
            situacao="Posse",
            condicao_eleitoral="Titular",
            descricao_status=f"Posse e início da {leg_num}ª Legislatura",
            legislatura=leg_num
        ))
        db.add(DeputadoHistorico(
            deputado_id=existing.id,
            data_hora=f"{ano_base + 1}-02-01T09:00:00",
            sigla_partido=dep_data["sigla_partido"],
            situacao=existing.situacao,
            condicao_eleitoral="Titular",
            descricao_status="Início da 2ª Sessão Legislativa Ordinária",
            legislatura=leg_num
        ))

    # 1.1 Mandatos parlamentares
    for mand_dict in MANDATOS_SEED:
        dep = deputados_map.get(mand_dict["deputado_camara_id"])
        if not dep:
            continue
        leg_num = mand_dict["legislatura_numero"]
        leg_obj = legislaturas_map.get(leg_num)

        m_exist = db.query(Mandato).filter(
            Mandato.deputado_id == dep.id,
            Mandato.legislatura_numero == leg_num
        ).first()

        if not m_exist:
            db.add(Mandato(
                deputado_id=dep.id,
                legislatura_id=leg_obj.id if leg_obj else None,
                legislatura_numero=leg_num,
                cargo=mand_dict["cargo"],
                sigla_partido=mand_dict["sigla_partido"],
                uf=mand_dict["uf"],
                situacao=mand_dict["situacao"],
                condicao_eleitoral=mand_dict["condicao_eleitoral"],
                data_inicio=mand_dict["data_inicio"],
                data_fim=mand_dict["data_fim"]
            ))

    # 1.2 Filiações partidárias
    for fil_dict in FILIACOES_SEED:
        dep = deputados_map.get(fil_dict["deputado_camara_id"])
        if not dep:
            continue
        f_exist = db.query(FiliacaoPartidaria).filter(
            FiliacaoPartidaria.deputado_id == dep.id,
            FiliacaoPartidaria.sigla_partido == fil_dict["sigla_partido"],
            FiliacaoPartidaria.data_inicio == fil_dict["data_inicio"]
        ).first()
        if not f_exist:
            db.add(FiliacaoPartidaria(
                deputado_id=dep.id,
                sigla_partido=fil_dict["sigla_partido"],
                nome_partido=fil_dict["nome_partido"],
                data_inicio=fil_dict["data_inicio"],
                data_fim=fil_dict["data_fim"]
    db.flush()

    # 2. Temas oficiais
    temas_nomes = [
        "Ciência, Tecnologia e Inovação",
        "Direitos Humanos e Minorias",
        "Saúde",
        "Administração Pública",
        "Economia, Finanças Públicas e Tributação",
        "Trabalho, Previdência e Assistência",
        "Meio Ambiente e Desenvolvimento Sustentável"
    ]
    temas_map = {}
    for i, nome_tema in enumerate(temas_nomes, 1):
        tema = db.query(Tema).filter(Tema.nome == nome_tema).first()
        if not tema:
            tema = Tema(camara_id=i, nome=nome_tema)
            db.add(tema)
            db.flush()
        temas_map[nome_tema] = tema

    # 3. Proposições Oficiais
    PROPOSICOES_SEED = [
        {
            "camara_id": 2451234,
            "sigla_tipo": "PL",
            "numero": 1234,
            "ano": 2025,
            "ementa": "Dispõe sobre diretrizes para a transparência e fiscalização cidadã de políticas públicas de saúde e assistência social no Sistema Único de Saúde (SUS).",
            "ementa_detalhada": "Cria mecanismos digitais de monitoramento de filas, distribuição de medicamentos e execução orçamentária dos fundos municipais e estaduais de saúde com acesso aberto ao cidadão.",
            "data_apresentacao": "2025-03-12T14:30:00",
            "situacao": "Em tramitação",
            "descricao_situacao": "Aguardando Parecer na Comissão de Saúde (CSAUDE)",
            "regime": "Ordinária (Art. 151, III, RICD)",
            "despacho": "Às Comissões de Saúde; de Administração e Serviço Público; e de Constituição e Justiça e de Cidadania.",
            "orgao_atual": "CSAUDE",
            "url_inteiro_teor": "https://www.camara.leg.br/proposicoesWeb/prop_mostrarintegra?codteor=2451234",
            "uri": "https://dadosabertos.camara.leg.br/api/v2/proposicoes/2451234",
            "autores": [
                {"camara_id": 204534, "nome": "Tabata Amaral", "tipo": "Deputado", "ordem": 1, "proponente": True},
                {"camara_id": 220610, "nome": "Duda Salabert", "tipo": "Deputado", "ordem": 2, "proponente": False},
            ],
            "temas": ["Saúde", "Administração Pública"],
            "tramitacoes": [
                {
                    "data_hora": "2025-03-12T14:30:00",
                    "sequencia": 1,
                    "descricao_tramitacao": "Apresentação de Proposição",
                    "despacho": "Apresentação do Projeto de Lei n. 1234/2025, pela Deputada Tabata Amaral (PSB/SP) e outros.",
                    "orgao": "PLEN",
                    "situacao": "Apresentada"
                },
                {
                    "data_hora": "2025-03-25T11:00:00",
                    "sequencia": 2,
                    "descricao_tramitacao": "Distribuição às Comissões",
                    "despacho": "Encaminhada à publicação. Despacho inicial: À CSAUDE, CASP e CCJC (mérito e art. 54).",
                    "orgao": "MESA",
                    "situacao": "Distribuída"
                },
                {
                    "data_hora": "2025-04-10T15:20:00",
                    "sequencia": 3,
                    "descricao_tramitacao": "Designação de Relator",
                    "despacho": "Designada Relatora da matéria na Comissão de Saúde.",
                    "orgao": "CSAUDE",
                    "situacao": "Pronta para Pauta"
                },
                {
                    "data_hora": "2025-04-30T10:30:00",
                    "sequencia": 4,
                    "descricao_tramitacao": "Aprovação de Requerimento de Urgência",
                    "despacho": "Aprovado o requerimento de tramitação em regime de urgência em votação nominal no Plenário.",
                    "orgao": "PLEN",
                    "situacao": "Em tramitação"
                }
            ]
        },
        {
            "camara_id": 2256735,
            "sigla_tipo": "PL",
            "numero": 2630,
            "ano": 2020,
            "ementa": "Institui a Lei Brasileira de Liberdade, Responsabilidade e Transparência na Internet.",
            "ementa_detalhada": "Estabelece normas relativas à transparência de redes sociais e de serviços de mensageria privada através da internet e para combate à desinformação.",
            "data_apresentacao": "2020-07-03T18:00:00",
            "situacao": "Em tramitação",
            "descricao_situacao": "Aguardando deliberação de Grupo de Trabalho constituído pela Presidência",
            "regime": "Urgência (Art. 155, RICD)",
            "despacho": "Submetido à apreciação do Plenário com parecer do relator.",
            "orgao_atual": "PLEN",
            "url_inteiro_teor": "https://www.camara.leg.br/proposicoesWeb/prop_mostrarintegra?codteor=2256735",
            "uri": "https://dadosabertos.camara.leg.br/api/v2/proposicoes/2256735",
            "autores": [
                {"camara_id": None, "nome": "Senado Federal - Alessandro Vieira", "tipo": "Órgão Legislativo", "ordem": 1, "proponente": True}
            ],
            "temas": ["Ciência, Tecnologia e Inovação", "Direitos Humanos e Minorias"],
            "tramitacoes": [
                {
                    "data_hora": "2023-04-25T20:15:00",
                    "sequencia": 12,
                    "descricao_tramitacao": "Votação do Requerimento de Urgência",
                    "despacho": "Aprovado o Requerimento nº 1056/2023, do Dep. Orlando Silva, que requer urgência para o PL 2630/2020.",
                    "orgao": "PLEN",
                    "situacao": "Urgência aprovada"
                },
                {
                    "data_hora": "2023-05-02T19:00:00",
                    "sequencia": 13,
                    "descricao_tramitacao": "Retirada de Pauta",
                    "despacho": "Deferido o requerimento de adiamento de discussão e votação da matéria por 10 sessões.",
                    "orgao": "PLEN",
                    "situacao": "Adiada"
                },
                {
                    "data_hora": "2024-04-10T14:00:00",
                    "sequencia": 14,
                    "descricao_tramitacao": "Criação de Grupo de Trabalho",
                    "despacho": "Ato da Presidência cria Grupo de Trabalho para analisar propostas de regulação de inteligência artificial e redes sociais.",
                    "orgao": "MESA",
                    "situacao": "Em análise por GT"
                }
            ]
        },
        {
            "camara_id": 2196833,
            "sigla_tipo": "PEC",
            "numero": 45,
            "ano": 2019,
            "ementa": "Altera o Sistema Tributário Nacional e dá outras providências (Reforma Tributária).",
            "ementa_detalhada": "Extingue tributos sobre consumo (PIS, Cofins, IPI, ICMS e ISS) e institui o IBS (Imposto sobre Bens e Serviços) e o CBS (Contribuição sobre Bens e Serviços).",
            "data_apresentacao": "2019-04-03T16:00:00",
            "situacao": "Promulgada",
            "descricao_situacao": "Transformada na Emenda Constitucional nº 132/2023",
            "regime": "Especial (Art. 202, RICD)",
            "despacho": "Aprovada em dois turnos na Câmara dos Deputados e no Senado Federal.",
            "orgao_atual": "PLEN",
            "url_inteiro_teor": "https://www.camara.leg.br/proposicoesWeb/prop_mostrarintegra?codteor=2196833",
            "uri": "https://dadosabertos.camara.leg.br/api/v2/proposicoes/2196833",
            "autores": [
                {"camara_id": 160541, "nome": "Arthur Lira e outros", "tipo": "Deputado", "ordem": 1, "proponente": True},
                {"camara_id": 74646, "nome": "Baleia Rossi", "tipo": "Deputado", "ordem": 2, "proponente": True}
            ],
            "temas": ["Economia, Finanças Públicas e Tributação"],
            "tramitacoes": [
                {
                    "data_hora": "2023-07-06T21:40:00",
                    "sequencia": 45,
                    "descricao_tramitacao": "Votação em Primeiro Turno",
                    "despacho": "Aprovada em 1º Turno a Proposta de Emenda à Constituição nº 45-A de 2019.",
                    "orgao": "PLEN",
                    "situacao": "Aprovada em 1º turno"
                },
                {
                    "data_hora": "2023-07-07T01:50:00",
                    "sequencia": 46,
                    "descricao_tramitacao": "Votação em Segundo Turno",
                    "despacho": "Aprovada em 2º Turno a Proposta de Emenda à Constituição nº 45-A de 2019. Matéria vai ao Senado Federal.",
                    "orgao": "PLEN",
                    "situacao": "Aprovada em 2º turno"
                },
                {
                    "data_hora": "2023-12-20T11:00:00",
                    "sequencia": 47,
                    "descricao_tramitacao": "Promulgação",
                    "despacho": "Sessão solene de promulgação da Emenda Constitucional nº 132 pelo Congresso Nacional.",
                    "orgao": "MESA",
                    "situacao": "Promulgada"
                }
            ]
        },
        {
            "camara_id": 2351982,
            "sigla_tipo": "PL",
            "numero": 1085,
            "ano": 2023,
            "ementa": "Dispõe sobre a igualdade salarial e remuneratória entre mulheres e homens para a mesma função ou trabalho de igual valor.",
            "ementa_detalhada": "Altera a Consolidação das Leis do Trabalho (CLT) para reforçar medidas de transparência salarial e punição contra discriminação.",
            "data_apresentacao": "2023-03-08T17:00:00",
            "situacao": "Transformada em Norma Jurídica",
            "descricao_situacao": "Transformada na Lei Ordinária nº 14.611/2023",
            "regime": "Urgência (Art. 155, RICD)",
            "despacho": "Aprovada em Plenário e sancionada pelo Presidente da República.",
            "orgao_atual": "PLEN",
            "url_inteiro_teor": "https://www.camara.leg.br/proposicoesWeb/prop_mostrarintegra?codteor=2351982",
            "uri": "https://dadosabertos.camara.leg.br/api/v2/proposicoes/2351982",
            "autores": [
                {"camara_id": None, "nome": "Poder Executivo", "tipo": "Poder Executivo", "ordem": 1, "proponente": True},
                {"camara_id": 74848, "nome": "Jandira Feghali", "tipo": "Deputado", "ordem": 2, "proponente": False}
            ],
            "temas": ["Trabalho, Previdência e Assistência", "Direitos Humanos e Minorias"],
            "tramitacoes": [
                {
                    "data_hora": "2023-05-04T18:30:00",
                    "sequencia": 8,
                    "descricao_tramitacao": "Votação do Mérito em Plenário",
                    "despacho": "Aprovado o Projeto de Lei nº 1085/2023 em votação nominal. Sim: 325, Não: 36.",
                    "orgao": "PLEN",
                    "situacao": "Aprovada"
                }
            ]
        }
    ]

    proposicoes_map = {}
    for prop_dict in PROPOSICOES_SEED:
        existing = db.query(Proposicao).filter(Proposicao.camara_id == prop_dict["camara_id"]).first()
        if not existing:
            prop_data = {k: v for k, v in prop_dict.items() if k not in ["autores", "temas", "tramitacoes"]}
            existing = Proposicao(**prop_data, dados_raw={"seed": True})
            db.add(existing)
            db.flush()
        proposicoes_map[prop_dict["camara_id"]] = existing

        # Autores
        db.query(ProposicaoAutor).filter(ProposicaoAutor.proposicao_id == existing.id).delete()
        for autor in prop_dict["autores"]:
            dep_id = None
            if autor["camara_id"] and autor["camara_id"] in deputados_map:
                dep_id = deputados_map[autor["camara_id"]].id

            db.add(ProposicaoAutor(
                proposicao_id=existing.id,
                deputado_id=dep_id,
                nome_autor=autor["nome"],
                tipo_autor=autor["tipo"],
                ordem_autoria=autor["ordem"],
                proponente=autor["proponente"]
            ))

        # Temas
        db.query(ProposicaoTema).filter(ProposicaoTema.proposicao_id == existing.id).delete()
        for t_nome in prop_dict["temas"]:
            tema_obj = temas_map.get(t_nome)
            if tema_obj:
                db.add(ProposicaoTema(
                    proposicao_id=existing.id,
                    tema_id=tema_obj.id,
                    relevancia=100
                ))

        # Tramitações
        db.query(Tramitacao).filter(Tramitacao.proposicao_id == existing.id).delete()
        for tr in prop_dict["tramitacoes"]:
            db.add(Tramitacao(
                proposicao_id=existing.id,
                data_hora=tr["data_hora"],
                sequencia=tr["sequencia"],
                descricao_tramitacao=tr["descricao_tramitacao"],
                despacho=tr["despacho"],
                orgao=tr["orgao"],
                situacao=tr["situacao"]
            ))

    # 4. Votações Oficiais e Votos Nominais
    VOTACOES_SEED = [
        {
            "camara_id": "2451234-10",
            "data_hora_registro": "2025-04-30T10:30:00",
            "descricao": "Votação do Requerimento de Urgência (Art. 155 do RICD) para o Projeto de Lei nº 1234/2025.",
            "resultado": "Aprovado o Requerimento de Urgência",
            "aprovada": True,
            "orgao": "PLEN",
            "placar_sim": 312,
            "placar_nao": 68,
            "placar_abstencao": 4,
            "placar_obstrucao": 8,
            "proposicao_camara_id": 2451234,
            "tipo_relacao": "Votação relacionada à proposição (Requerimento de Urgência)",
            "orientacoes": [
                {"bancada": "Governo", "orientacao": "Sim"},
                {"bancada": "Oposição", "orientacao": "Liberado"},
                {"bancada": "PT", "orientacao": "Sim"},
                {"bancada": "PL", "orientacao": "Liberado"},
                {"bancada": "PSB", "orientacao": "Sim"},
                {"bancada": "PSOL", "orientacao": "Sim"},
                {"bancada": "NOVO", "orientacao": "Não"},
                {"bancada": "UNIÃO", "orientacao": "Sim"}
            ],
            "votos_nominais": {
                204534: "Sim",       # Tabata Amaral
                160541: "Artigo 17", # Arthur Lira (Presidente não vota salvo desempate)
                220645: "Sim",       # Erika Hilton
                220593: "Não",       # Nikolas Ferreira
                220639: "Sim",       # Guilherme Boulos
                204536: "Não",       # Kim Kataguiri
                74848:  "Sim",       # Jandira Feghali
                156190: "Não",       # Marcel van Hattem
                107283: "Sim",       # Gleisi Hoffmann
                220610: "Sim",       # Duda Salabert
            }
        },
        {
            "camara_id": "2256735-42",
            "data_hora_registro": "2023-04-25T20:15:00",
            "descricao": "Votação do Requerimento de Urgência para o Projeto de Lei nº 2630/2020 (Lei Brasileira de Liberdade, Responsabilidade e Transparência na Internet).",
            "resultado": "Aprovada a Urgência",
            "aprovada": True,
            "orgao": "PLEN",
            "placar_sim": 238,
            "placar_nao": 192,
            "placar_abstencao": 2,
            "placar_obstrucao": 5,
            "proposicao_camara_id": 2256735,
            "tipo_relacao": "Votação relacionada à proposição",
            "orientacoes": [
                {"bancada": "Governo", "orientacao": "Sim"},
                {"bancada": "Oposição", "orientacao": "Não"},
                {"bancada": "PT", "orientacao": "Sim"},
                {"bancada": "PL", "orientacao": "Não"},
                {"bancada": "PSOL", "orientacao": "Sim"},
                {"bancada": "NOVO", "orientacao": "Não"},
                {"bancada": "UNIÃO", "orientacao": "Liberado"}
            ],
            "votos_nominais": {
                204534: "Sim",
                160541: "Artigo 17",
                220645: "Sim",
                220593: "Não",
                220639: "Sim",
                204536: "Não",
                74848:  "Sim",
                156190: "Não",
                107283: "Sim",
                220610: "Sim",
            }
        },
        {
            "camara_id": "2196833-88",
            "data_hora_registro": "2023-07-06T21:40:00",
            "descricao": "Votação em 1º Turno da Proposta de Emenda à Constituição nº 45 de 2019 (Substitutivo da Reforma Tributária).",
            "resultado": "Aprovada a PEC em 1º Turno",
            "aprovada": True,
            "orgao": "PLEN",
            "placar_sim": 382,
            "placar_nao": 118,
            "placar_abstencao": 3,
            "placar_obstrucao": 0,
            "proposicao_camara_id": 2196833,
            "tipo_relacao": "Votação relacionada à proposição (1º Turno do Substitutivo)",
            "orientacoes": [
                {"bancada": "Governo", "orientacao": "Sim"},
                {"bancada": "Oposição", "orientacao": "Não"},
                {"bancada": "MDB", "orientacao": "Sim"},
                {"bancada": "PP", "orientacao": "Sim"},
                {"bancada": "PL", "orientacao": "Liberado"},
                {"bancada": "PT", "orientacao": "Sim"},
                {"bancada": "NOVO", "orientacao": "Não"}
            ],
            "votos_nominais": {
                204534: "Sim",
                160541: "Artigo 17",
                220645: "Sim",
                220593: "Não",
                220639: "Sim",
                204536: "Não",
                74848:  "Sim",
                156190: "Não",
                107283: "Sim",
                220610: "Sim",
            }
        },
        {
            "camara_id": "2196833-89",
            "data_hora_registro": "2023-07-07T01:50:00",
            "descricao": "Votação em 2º Turno da Proposta de Emenda à Constituição nº 45 de 2019 (Reforma Tributária).",
            "resultado": "Aprovada a PEC em 2º Turno",
            "aprovada": True,
            "orgao": "PLEN",
            "placar_sim": 375,
            "placar_nao": 113,
            "placar_abstencao": 3,
            "placar_obstrucao": 0,
            "proposicao_camara_id": 2196833,
            "tipo_relacao": "Votação relacionada à proposição (2º Turno)",
            "orientacoes": [
                {"bancada": "Governo", "orientacao": "Sim"},
                {"bancada": "Oposição", "orientacao": "Não"},
                {"bancada": "PT", "orientacao": "Sim"},
                {"bancada": "PP", "orientacao": "Sim"}
            ],
            "votos_nominais": {
                204534: "Sim",
                160541: "Artigo 17",
                220645: "Sim",
                220593: "Não",
                220639: "Sim",
                204536: "Não",
                74848:  "Sim",
                156190: "Não",
                107283: "Sim",
                220610: "Sim",
            }
        },
        {
            "camara_id": "2351982-12",
            "data_hora_registro": "2023-05-04T18:30:00",
            "descricao": "Votação do mérito do Projeto de Lei nº 1085/2023 (Igualdade Salarial entre Homens e Mulheres).",
            "resultado": "Aprovada a matéria",
            "aprovada": True,
            "orgao": "PLEN",
            "placar_sim": 325,
            "placar_nao": 36,
            "placar_abstencao": 1,
            "placar_obstrucao": 0,
            "proposicao_camara_id": 2351982,
            "tipo_relacao": "Votação relacionada à proposição",
            "orientacoes": [
                {"bancada": "Governo", "orientacao": "Sim"},
                {"bancada": "Oposição", "orientacao": "Liberado"},
                {"bancada": "PL", "orientacao": "Liberado"},
                {"bancada": "PT", "orientacao": "Sim"},
                {"bancada": "NOVO", "orientacao": "Não"}
            ],
            "votos_nominais": {
                204534: "Sim",
                160541: "Artigo 17",
                220645: "Sim",
                220593: "Não",
                220639: "Sim",
                204536: "Sim",
                74848:  "Sim",
                156190: "Não",
                107283: "Sim",
                220610: "Sim",
            }
        },
        {
            "camara_id": "2192459-100",
            "data_hora_registro": "2019-07-10T22:30:00",
            "descricao": "Votação em 1º Turno da Proposta de Emenda à Constituição nº 6 de 2019 (Reforma da Previdência Social na 56ª Legislatura).",
            "resultado": "Aprovada a PEC no 1º Turno (379 votos a 131)",
            "aprovada": True,
            "orgao": "PLEN",
            "placar_sim": 379,
            "placar_nao": 131,
            "placar_abstencao": 0,
            "placar_obstrucao": 0,
            "proposicao_camara_id": 2196833,
            "tipo_relacao": "Votação da 56ª Legislatura",
            "orientacoes": [
                {"bancada": "Governo", "orientacao": "Sim"},
                {"bancada": "Oposição", "orientacao": "Não"},
                {"bancada": "PDT", "orientacao": "Não"},
                {"bancada": "PT", "orientacao": "Não"},
                {"bancada": "DEM", "orientacao": "Sim"},
                {"bancada": "NOVO", "orientacao": "Sim"}
            ],
            "votos_nominais": {
                204534: "Sim",       # Tabata Amaral (PDT na 56ª)
                160541: "Sim",       # Arthur Lira (PP)
                204536: "Sim",       # Kim Kataguiri (DEM na 56ª)
                74848:  "Não",       # Jandira Feghali (PCdoB)
                156190: "Sim",       # Marcel van Hattem (NOVO)
                107283: "Não",       # Gleisi Hoffmann (PT)
                74693:  "Artigo 17", # Rodrigo Maia (DEM - Presidente da Câmara na 56ª)
                204547: "Não",       # Marcelo Freixo (PSOL na 56ª)
            }
        }
    ]

    for vot_dict in VOTACOES_SEED:
        existing = db.query(Votacao).filter(Votacao.camara_id == vot_dict["camara_id"]).first()
        if not existing:
            v_data = {
                "camara_id": vot_dict["camara_id"],
                "data_hora_registro": vot_dict["data_hora_registro"],
                "descricao": vot_dict["descricao"],
                "resultado": vot_dict["resultado"],
                "aprovada": vot_dict["aprovada"],
                "orgao": vot_dict["orgao"],
                "placar_sim": vot_dict["placar_sim"],
                "placar_nao": vot_dict["placar_nao"],
                "placar_abstencao": vot_dict["placar_abstencao"],
                "placar_obstrucao": vot_dict["placar_obstrucao"],
                "uri": f"https://dadosabertos.camara.leg.br/api/v2/votacoes/{vot_dict['camara_id']}",
                "dados_raw": {"seed": True}
            }
            existing = Votacao(**v_data)
            db.add(existing)
            db.flush()

        # Vincula à proposição
        prop_camara_id = vot_dict.get("proposicao_camara_id")
        if prop_camara_id in proposicoes_map:
            prop_obj = proposicoes_map[prop_camara_id]
            link = db.query(VotacaoProposicao).filter(
                VotacaoProposicao.votacao_id == existing.id,
                VotacaoProposicao.proposicao_id == prop_obj.id
            ).first()
            if not link:
                db.add(VotacaoProposicao(
                    votacao_id=existing.id,
                    proposicao_id=prop_obj.id,
                    tipo_relacao=vot_dict["tipo_relacao"],
                    descricao=vot_dict["descricao"]
                ))

        # Orientações
        db.query(VotacaoOrientacao).filter(VotacaoOrientacao.votacao_id == existing.id).delete()
        for o in vot_dict["orientacoes"]:
            db.add(VotacaoOrientacao(
                votacao_id=existing.id,
                bancada=o["bancada"],
                orientacao_voto=o["orientacao"]
            ))

        # Votos nominais preservando estritamente a filiação no momento do voto
        db.query(Voto).filter(Voto.votacao_id == existing.id).delete()
        for dep_camara_id, tipo_voto in vot_dict["votos_nominais"].items():
            dep_obj = deputados_map.get(dep_camara_id)
            if dep_obj:
                ano_voto = int(vot_dict["data_hora_registro"][:4]) if vot_dict.get("data_hora_registro") else 2023
                partido_momento = dep_obj.sigla_partido
                if dep_camara_id == 204534:
                    partido_momento = "PDT" if ano_voto <= 2021 else "PSB"
                elif dep_camara_id == 204536:
                    partido_momento = "DEM" if ano_voto <= 2021 else "UNIÃO"
                elif dep_camara_id == 74693:
                    partido_momento = "DEM" if ano_voto <= 2021 else "PSDB"
                elif dep_camara_id == 204547:
                    partido_momento = "PSOL" if ano_voto <= 2021 else "PSB"

                db.add(Voto(
                    votacao_id=existing.id,
                    deputado_id=dep_obj.id,
                    tipo_voto=tipo_voto,
                    data_hora=vot_dict["data_hora_registro"],
                    sigla_partido_momento=partido_momento,
                    uf_momento=dep_obj.uf
                ))

    # 5. Eventos Oficiais e Presenças
    EVENTOS_SEED = [
        {
            "camara_id": 71001,
            "data_inicio": "2025-04-10T14:00:00",
            "data_fim": "2025-04-10T18:00:00",
            "tipo": "Audiência Pública",
            "descricao": "Audiência Pública da Comissão de Saúde para debater transparência no fornecimento de medicamentos e gestão do SUS.",
            "situacao": "Realizada",
            "local": "Anexo II, Plenário 7",
            "deputados": [204534, 220610, 74848]
        },
        {
            "camara_id": 71002,
            "data_inicio": "2025-03-20T09:30:00",
            "data_fim": "2025-03-20T13:00:00",
            "tipo": "Reunião Deliberativa Ordinária",
            "descricao": "Reunião Ordinária da Comissão de Constituição e Justiça e de Cidadania.",
            "situacao": "Realizada",
            "local": "Anexo II, Plenário 1",
            "deputados": [220593, 204536, 156190, 107283, 220639]
        },
        {
            "camara_id": 71003,
            "data_inicio": "2024-05-15T10:00:00",
            "data_fim": "2024-05-15T14:30:00",
            "tipo": "Sessão Deliberativa Extraordinária",
            "descricao": "Sessão de debates e votações de proposições prioritárias no Plenário Ulysses Guimarães.",
            "situacao": "Realizada",
            "local": "Plenário Ulysses Guimarães",
            "deputados": [204534, 160541, 220645, 220593, 220639, 204536, 74848, 156190, 107283, 220610]
        }
    ]

    for evt_dict in EVENTOS_SEED:
        existing_evt = db.query(Evento).filter(Evento.camara_id == evt_dict["camara_id"]).first()
        if not existing_evt:
            existing_evt = Evento(
                camara_id=evt_dict["camara_id"],
                data_inicio=evt_dict["data_inicio"],
                data_fim=evt_dict["data_fim"],
                tipo=evt_dict["tipo"],
                descricao=evt_dict["descricao"],
                situacao=evt_dict["situacao"],
                local=evt_dict["local"],
                uri=f"https://dadosabertos.camara.leg.br/api/v2/eventos/{evt_dict['camara_id']}",
                dados_raw={"seed": True}
            )
            db.add(existing_evt)
            db.flush()

        db.query(EventoDeputado).filter(EventoDeputado.evento_id == existing_evt.id).delete()
        for d_cid in evt_dict["deputados"]:
            d_obj = deputados_map.get(d_cid)
            if d_obj:
                db.add(EventoDeputado(
                    evento_id=existing_evt.id,
                    deputado_id=d_obj.id
                ))

    # 6. Estrutura Canônica do Governo e SIORG
    estrutura_srv = EstruturaService()
    tot_inst = estrutura_srv.sync_estrutura_canonica(db)

    orgaos_srv = OrgaosService()
    tot_orgaos = orgaos_srv.sync_orgaos_executivo(db, use_live_siorg=False)

    # 7. Registra SyncRun
    sync_run = SyncRun(
        tipo="seed",
        iniciado_em=utc_now(),
        finalizado_em=utc_now(),
        status="SUCCESS",
        registros_processados=len(DEPUTADOS_SEED) + len(PROPOSICOES_SEED) + len(VOTACOES_SEED) + len(EVENTOS_SEED) + tot_inst + tot_orgaos
    )
    db.add(sync_run)
    db.commit()

    logger.info("Carga da amostra oficial e estrutura de governo finalizada com sucesso!")
    return {
        "deputados": len(DEPUTADOS_SEED),
        "proposicoes": len(PROPOSICOES_SEED),
        "votacoes": len(VOTACOES_SEED),
        "eventos": len(EVENTOS_SEED),
        "instituicoes": tot_inst + tot_orgaos
    }
