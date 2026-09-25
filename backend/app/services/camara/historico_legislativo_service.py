"""Importação histórica paginada dos registros legislativos da Câmara.

Cada item concluído é confirmado separadamente. Uma interrupção não apaga o que
foi carregado, e uma nova execução reaproveita as chaves oficiais (upsert).
Não afirma cobertura total quando há falhas em registros da API.
"""
import logging
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Proposicao
from app.services.camara.camara_client import CamaraClient
from app.services.camara.proposicoes_service import ProposicoesService
from app.services.camara.votacoes_service import VotacoesService
from app.services.camara.eventos_service import EventosService

logger = logging.getLogger(__name__)

TIPOS = ("proposicoes", "votacoes", "eventos")


class HistoricoLegislativoService:
    def __init__(self, client: Optional[CamaraClient] = None):
        self.client = client or CamaraClient()
        self.proposicoes = ProposicoesService(self.client)
        self.votacoes = VotacoesService(self.client)
        self.eventos = EventosService(self.client)
        self.concluidos = 0
        self.falhas: list[tuple[str, int, str, str]] = []

    def _importar_proposicao(self, db: Session, item: dict) -> None:
        prop_id = int(item["id"])
        raw = self.client.get_proposicao(prop_id) or item

        # Consultar antes de abrir a transação de escrita.
        autores = self.client.get_proposicao_autores(prop_id)
        temas = self.client.get_proposicao_temas(prop_id)
        tramitacoes = self.client.get_proposicao_tramitacoes(prop_id)

        prop = self.proposicoes.upsert_proposicao(db, raw)
        self.proposicoes.sync_autores(db, prop, autores)
        self.proposicoes.sync_temas(db, prop, temas)
        self.proposicoes.sync_tramitacoes(db, prop, tramitacoes)

    def _importar_votacao(self, db: Session, item: dict) -> None:
        votacao_id = str(item["id"])
        raw = self.client.get_votacao(votacao_id) or item
        votos = self.client.get_votacao_votos(votacao_id)
        orientacoes = self.client.get_votacao_orientacoes(votacao_id)

        votacao = self.votacoes.upsert_votacao(db, raw)
        self.votacoes.sync_votos(db, votacao, votos)
        self.votacoes.sync_orientacoes(db, votacao, orientacoes)

        # Nem toda votação informa sua proposição-objeto. Não inventar relações.
        objeto = raw.get("proposicaoObjeto")
        if isinstance(objeto, dict) and objeto.get("id"):
            prop = (
                db.query(Proposicao)
                .filter(Proposicao.camara_id == objeto["id"])
                .first()
            )
            if prop:
                self.votacoes.link_proposicao(
                    db, votacao, prop, "proposicao_objeto", raw.get("descricao")
                )

    def _importar_evento(self, db: Session, item: dict) -> None:
        evento_id = int(item["id"])
        raw = self.client.get_evento(evento_id) or item
        presentes = self.client.get_evento_deputados(evento_id)
        evento = self.eventos.upsert_evento(db, raw)
        self.eventos.sync_deputados_evento(db, evento, presentes)

    def sync_periodo(
        self,
        db: Session,
        ano_inicial: int,
        ano_final: int,
        somente: str = "todos",
        limite_paginas: Optional[int] = None,
    ) -> int:
        if not 2000 <= ano_inicial <= ano_final <= date.today().year:
            raise ValueError("Período inválido: use anos entre 2000 e o ano atual.")
        if somente != "todos" and somente not in TIPOS:
            raise ValueError("O tipo deve ser todos, proposicoes, votacoes ou eventos.")
        if limite_paginas is not None and limite_paginas < 1:
            raise ValueError("limite_paginas deve ser positivo.")

        # Todas as proposições precedem as votações, inclusive vínculos entre anos.
        tipos = TIPOS if somente == "todos" else (somente,)
        handlers = {
            "proposicoes": self._importar_proposicao,
            "votacoes": self._importar_votacao,
            "eventos": self._importar_evento,
        }
        try:
            for tipo in tipos:
                for ano in range(ano_inicial, ano_final + 1):
                    fim = min(date(ano, 12, 31), date.today()).isoformat()
                    inicio = f"{ano}-01-01"
                    params = (
                        {"ano": ano, "ordem": "ASC", "ordenarPor": "id"}
                        if tipo == "proposicoes"
                        else {
                            "dataInicio": inicio,
                            "dataFim": fim,
                            "ordem": "ASC",
                            "ordenarPor": "id",
                        }
                    )
                    logger.info(
                        "Importando %s de %s (até %s, limite de páginas: %s).",
                        tipo, ano, fim, limite_paginas or "sem limite",
                    )
                    total_ano = 0
                    for pagina, items in self.client.iter_paginated_pages(
                        f"/{tipo}", params=params,
                        page_size=100, max_pages=limite_paginas,
                    ):
                        for item in items:
                            try:
                                handlers[tipo](db, item)
                                db.commit()
                                self.concluidos += 1
                                total_ano += 1
                            except Exception as exc:
                                db.rollback()
                                self.falhas.append((
                                    tipo, ano, str(item.get("id")), str(exc)[:300]
                                ))
                                logger.exception(
                                    "Falha em %s %s/%s; prosseguindo.",
                                    tipo, ano, item.get("id"),
                                )
                        logger.info(
                            "%s/%s: página %s concluída (%s itens confirmados).",
                            tipo, ano, pagina, total_ano,
                        )
                    logger.info(
                        "Importação %s/%s: %s itens confirmados.", tipo, ano, total_ano
                    )
        finally:
            self.client.close()

        if self.falhas:
            resumo = "; ".join(
                f"{tipo}/{ano}/{id_oficial}: {motivo[:120]}"
                for tipo, ano, id_oficial, motivo in self.falhas[:10]
            )
            raise RuntimeError(
                f"Importação histórica parcial: {self.concluidos} registros confirmados, "
                f"{len(self.falhas)} falhas; primeiros erros: {resumo}. "
                "Reexecute o período/tipo correspondente para recuperar os pendentes."
            )
        if limite_paginas is not None:
            logger.warning(
                "Carga amostral: limite de %s página(s) por ano e tipo. "
                "Não representa o histórico completo.",
                limite_paginas,
            )
        return self.concluidos
