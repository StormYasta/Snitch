"""Cobertura do importador histórico e retomada depois de falhas parciais."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import (
    Deputado, Evento, EventoDeputado, Proposicao, ProposicaoAutor,
    ProposicaoTema, Tema, Tramitacao, Votacao, VotacaoProposicao, Voto,
)
from app.services.camara.camara_client import CamaraClient
from app.services.camara.historico_legislativo_service import HistoricoLegislativoService


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


class FakeAPI:
    def __init__(self):
        self.calls = []
        self.closed = False
        self.fail_one_vote = False

    def iter_paginated_pages(self, endpoint, params, page_size, max_pages):
        self.calls.append((endpoint, params.copy(), page_size, max_pages))
        assert page_size == 100
        if endpoint == "/proposicoes" and params["ano"] == 2018:
            yield 1, [{"id": 11}]
        elif endpoint == "/votacoes" and params["dataInicio"] == "2018-01-01":
            yield 1, [{"id": "9-11"}, {"id": "9-12"}]
        elif endpoint == "/eventos" and params["dataInicio"] == "2018-01-01":
            yield 1, [{"id": 31}]

    def get_proposicao(self, _):
        return {"id": 11, "siglaTipo": "PL", "numero": 1, "ano": 2018,
                "ementa": "Exemplo de teste", "dataApresentacao": "2018-03-01"}

    def get_proposicao_autores(self, _):
        return [{"nome": "Parlamentar de teste", "uri": "/deputados/501"}]

    def get_proposicao_temas(self, _):
        return [{"tema": "Educação", "codTema": 5}]

    def get_proposicao_tramitacoes(self, _):
        return [{"sequencia": 1, "dataHora": "2018-04-01"}]

    def get_votacao(self, vote_id):
        return {
            "id": vote_id,
            "dataHoraRegistro": "2018-09-01",
            "descricao": "Votação de teste",
            "proposicaoObjeto": {"id": 11},
        }

    def get_votacao_votos(self, vote_id):
        if vote_id == "9-11" and self.fail_one_vote:
            self.fail_one_vote = False
            raise RuntimeError("API temporariamente indisponível")
        return [{"deputado_": {"id": 501, "nome": "Parlamentar de teste"},
                 "tipoVoto": "Sim"}]

    def get_votacao_orientacoes(self, _):
        return []

    def get_evento(self, _):
        return {"id": 31, "dataHoraInicio": "2018-05-01T11:00:00",
                "descricao": "Sessão de teste"}

    def get_evento_deputados(self, _):
        return [{"id": 501, "nome": "Parlamentar de teste"}]

    def close(self):
        self.closed = True


def test_importacao_completa_preserva_relacoes_e_nao_duplica(db):
    client = FakeAPI()
    db.add(Deputado(camara_id=501, nome_parlamentar="Parlamentar de teste"))
    db.commit()

    sync = HistoricoLegislativoService(client)
    assert sync.sync_periodo(db, 2018, 2018) == 4
    assert client.closed
    assert [name for name, _, _, _ in client.calls] == [
        "/proposicoes", "/votacoes", "/eventos"
    ]
    assert db.query(Proposicao).count() == 1
    assert db.query(ProposicaoAutor).count() == 1
    assert db.query(ProposicaoTema).count() == 1
    assert db.query(Tema).count() == 1
    assert db.query(Tramitacao).count() == 1
    assert db.query(Votacao).count() == 2
    assert db.query(Voto).count() == 2
    assert db.query(VotacaoProposicao).count() == 2
    assert db.query(Evento).count() == 1
    assert db.query(EventoDeputado).count() == 1

    assert HistoricoLegislativoService(FakeAPI()).sync_periodo(db, 2018, 2018) == 4
    assert db.query(Proposicao).count() == 1
    assert db.query(Votacao).count() == 2
    assert db.query(Voto).count() == 2
    assert db.query(Evento).count() == 1
    assert db.query(EventoDeputado).count() == 1


def test_falha_em_um_registro_preserva_os_outros_e_permite_reexecucao(db):
    client = FakeAPI()
    client.fail_one_vote = True
    with pytest.raises(RuntimeError, match="1 falhas"):
        HistoricoLegislativoService(client).sync_periodo(
            db, 2018, 2018, somente="votacoes"
        )
    assert {v.camara_id for v in db.query(Votacao).all()} == {"9-12"}
    assert HistoricoLegislativoService(client).sync_periodo(
        db, 2018, 2018, somente="votacoes"
    ) == 2
    assert {v.camara_id for v in db.query(Votacao).all()} == {"9-11", "9-12"}
    assert db.query(Voto).count() == 2


def test_cliente_paginado_respeita_proxima_pagina_sem_acumular():
    client = CamaraClient()
    requests = []

    def fake_get(endpoint, params):
        requests.append(params.copy())
        if params["pagina"] == 1:
            return {"dados": [{"id": 1}], "links": [{"rel": "next"}]}
        return {"dados": [{"id": 2}], "links": []}

    client.get = fake_get
    try:
        pages = list(client.iter_paginated_pages("/proposicoes", {"ano": 2018}))
        assert pages == [(1, [{"id": 1}]), (2, [{"id": 2}])]
        assert requests[0]["ano"] == 2018
        assert requests[1]["pagina"] == 2
        requests.clear()
        limited = list(
            client.iter_paginated_pages(
                "/proposicoes", {"ano": 2018}, max_pages=1
            )
        )
        assert limited == [(1, [{"id": 1}])]
        assert len(requests) == 1
    finally:
        client.close()
