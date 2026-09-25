"""Regressões da sincronização com falhas parciais e status oficiais extensos."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from sqlalchemy import Text

from app.database import Base
from app.models import Deputado, DeputadoHistorico, Legislatura, Proposicao
from app.services.camara.deputados_service import DeputadosService
from app.services.camara.historico_service import HistoricoService
from app.services.camara.proposicoes_service import ProposicoesService


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


class FakeCamara:
    def get_deputados_all(self, params):
        return [{"id": value} for value in (101, 102, 103)]

    def get_deputado(self, value):
        return {
            "id": value,
            "nomeCivil": f"Nome do deputado {value}",
            "ultimoStatus": {
                "nomeEleitoral": f"Deputado {value}",
                "descricaoStatus": "Registro oficial longo " * 35,
            },
        }

    def get_deputado_historico(self, value):
        return [{
            "dataHora": "2023-05-01",
            "descricaoStatus": "Registro histórico extenso " * 30,
        }]


class FailingOnceDeputadosService(DeputadosService):
    def __init__(self, client):
        super().__init__(client)
        self.failed = False

    def upsert_deputado(self, db, raw_data):
        if raw_data["id"] == 102 and not self.failed:
            self.failed = True
            # Simula uma falha SQL real após uma escrita ainda não confirmada.
            db.add(Deputado(camara_id=101, nome_parlamentar="Duplicado"))
            db.flush()
        return super().upsert_deputado(db, raw_data)


def test_enriquecimento_preserva_registros_anteriores_e_permite_reexecucao(db):
    db.add(Legislatura(camara_id=57, numero=57))
    db.commit()

    client = FakeCamara()
    failing_service = FailingOnceDeputadosService(client)
    sync = HistoricoService(client=client, deputados_service=failing_service)
    with pytest.raises(RuntimeError, match="1 falhas"):
        sync.enrich_current_deputies(db)

    assert {row.camara_id for row in db.query(Deputado).all()} == {101, 103}
    assert db.query(DeputadoHistorico).count() == 2
    assert isinstance(Deputado.__table__.columns.descricao_status.type, Text)
    assert isinstance(DeputadoHistorico.__table__.columns.descricao_status.type, Text)

    # Retoma apenas o deputado com falha, sem requisitar os 3 novamente.
    retried = HistoricoService(client=client)
    from app.models import Mandato
    db.add(Mandato(deputado_id=db.query(Deputado).filter_by(camara_id=101).one().id, legislatura_numero=57))
    db.add(Mandato(deputado_id=db.query(Deputado).filter_by(camara_id=103).one().id, legislatura_numero=57))
    db.add(Deputado(camara_id=102, nome_parlamentar="Deputado 102"))
    db.flush()
    db.add(Mandato(deputado_id=db.query(Deputado).filter_by(camara_id=102).one().id, legislatura_numero=57))
    db.commit()
    assert retried.enrich_current_deputies(db, ids={102}) == 1

    # A reexecução integral também é idempotente.
    assert retried.enrich_current_deputies(db) == 3
    assert {row.camara_id for row in db.query(Deputado).all()} == {101, 102, 103}
    assert db.query(DeputadoHistorico).count() == 3
    assert len(db.query(Deputado).filter(Deputado.camara_id == 101).one().descricao_status) > 255

    with pytest.raises(ValueError, match="sem mandato"):
        retried.enrich_current_deputies(db, ids={999999})


class FakeProposicoes:
    def get_proposicoes(self, params):
        return [{"id": 1}, {"id": 2}]

    def get_proposicao(self, prop_id):
        return {
            "id": prop_id,
            "siglaTipo": "PL",
            "numero": prop_id,
            "ano": 2026,
        }

    def get_proposicao_autores(self, prop_id):
        return []

    def get_proposicao_temas(self, prop_id):
        return []

    def get_proposicao_tramitacoes(self, prop_id):
        return []


class FailingProposicoesService(ProposicoesService):
    def upsert_proposicao(self, db, raw_data):
        if raw_data["id"] == 1:
            db.add(Proposicao(camara_id=999, sigla_tipo="PL", numero=1, ano=2026))
            db.add(Proposicao(camara_id=999, sigla_tipo="PL", numero=1, ano=2026))
            db.flush()
        return super().upsert_proposicao(db, raw_data)


def test_proposicoes_recupera_sessao_apos_erro_sql(db):
    service = FailingProposicoesService(FakeProposicoes())
    assert service.sync_proposicoes(db, ano=2026, limite=2) == 1
    assert db.query(Proposicao).count() == 1
    assert db.query(Proposicao).one().camara_id == 2
