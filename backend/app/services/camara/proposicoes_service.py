import logging
import re
from typing import Optional
from sqlalchemy.orm import Session
from app.models import Proposicao, ProposicaoAutor, Tema, ProposicaoTema, Tramitacao, Deputado, utc_now
from app.services.camara.camara_client import CamaraClient

logger = logging.getLogger(__name__)

class ProposicoesService:
    def __init__(self, client: Optional[CamaraClient] = None):
        self.client = client or CamaraClient()

    def transform_proposicao(self, raw_data: dict) -> dict:
        status = raw_data.get("statusProposicao") or {}
        return {
            "camara_id": raw_data.get("id"),
            "sigla_tipo": raw_data.get("siglaTipo") or "PL",
            "numero": raw_data.get("numero") or 0,
            "ano": raw_data.get("ano") or 2024,
            "ementa": raw_data.get("ementa"),
            "ementa_detalhada": raw_data.get("ementaDetalhada"),
            "data_apresentacao": raw_data.get("dataApresentacao"),
            "situacao": status.get("descricaoSituacao") or raw_data.get("situacao") or "Em tramitação",
            "descricao_situacao": status.get("descricaoSituacao"),
            "regime": status.get("regime"),
            "despacho": status.get("despacho"),
            "orgao_atual": status.get("siglaOrgao"),
            "url_inteiro_teor": raw_data.get("urlInteiroTeor"),
            "uri": raw_data.get("uri") or f"https://dadosabertos.camara.leg.br/api/v2/proposicoes/{raw_data.get('id')}",
            "dados_raw": raw_data,
        }

    def upsert_proposicao(self, db: Session, raw_data: dict) -> Proposicao:
        data = self.transform_proposicao(raw_data)
        camara_id = data["camara_id"]
        prop = db.query(Proposicao).filter(Proposicao.camara_id == camara_id).first()

        if prop:
            for k, v in data.items():
                if v is not None or getattr(prop, k) is None:
                    setattr(prop, k, v)
            prop.updated_at = utc_now()
        else:
            prop = Proposicao(**data)
            db.add(prop)

        db.flush()
        return prop

    def sync_autores(self, db: Session, prop: Proposicao, autores_data: list[dict]):
        db.query(ProposicaoAutor).filter(ProposicaoAutor.proposicao_id == prop.id).delete()
        for idx, autor in enumerate(autores_data):
            uri_autor = autor.get("uri") or ""
            deputado_id = None

            # Extrai ID do deputado da URI se for link de deputado
            dep_camara_id = None
            match = re.search(r"/deputados/(\d+)", uri_autor)
            if match:
                dep_camara_id = int(match.group(1))
            elif autor.get("codTipo") == 10000 and autor.get("id"):
                dep_camara_id = autor.get("id")

            if dep_camara_id:
                dep = db.query(Deputado).filter(Deputado.camara_id == dep_camara_id).first()
                if dep:
                    deputado_id = dep.id

            db.add(ProposicaoAutor(
                proposicao_id=prop.id,
                deputado_id=deputado_id,
                nome_autor=autor.get("nome") or "Autor não identificado",
                tipo_autor=autor.get("tipo"),
                ordem_autoria=autor.get("ordemAssinatura") or (idx + 1),
                proponente=bool(autor.get("proponente")),
                uri_autor=uri_autor
            ))

    def sync_temas(self, db: Session, prop: Proposicao, temas_data: list[dict]):
        db.query(ProposicaoTema).filter(ProposicaoTema.proposicao_id == prop.id).delete()
        for t in temas_data:
            nome_tema = t.get("tema") or t.get("nome")
            if not nome_tema:
                continue
            tema = db.query(Tema).filter(Tema.nome == nome_tema).first()
            if not tema:
                tema = Tema(
                    camara_id=t.get("codTema"),
                    nome=nome_tema
                )
                db.add(tema)
                db.flush()

            db.add(ProposicaoTema(
                proposicao_id=prop.id,
                tema_id=tema.id,
                relevancia=t.get("relevancia") or 0
            ))

    def sync_tramitacoes(self, db: Session, prop: Proposicao, tramitacoes_data: list[dict]):
        db.query(Tramitacao).filter(Tramitacao.proposicao_id == prop.id).delete()
        for tr in tramitacoes_data:
            db.add(Tramitacao(
                proposicao_id=prop.id,
                data_hora=tr.get("dataHora"),
                sequencia=tr.get("sequencia") or 1,
                descricao_tramitacao=tr.get("descricaoTramitacao"),
                despacho=tr.get("despacho"),
                orgao=tr.get("siglaOrgao"),
                situacao=tr.get("descricaoSituacao"),
                regime=tr.get("regime"),
                url_documento=tr.get("url")
            ))

    def sync_proposicoes(self, db: Session, ano: int = 2024, limite: int = 50) -> int:
        """Sincroniza proposições recentes da API oficial."""
        logger.info(f"Sincronizando proposições do ano {ano}...")
        params = {
            "ano": ano,
            "siglaTipo": ["PL", "PEC", "MPV"],
            "ordem": "DESC",
            "ordenarPor": "id",
            "itens": min(limite, 100),
        }
        proposicoes_lista = self.client.get_proposicoes(params=params)
        count = 0

        for item in proposicoes_lista[:limite]:
            prop_id = item["id"]
            try:
                detalhe = self.client.get_proposicao(prop_id)
                raw = detalhe if detalhe else item
                prop = self.upsert_proposicao(db, raw)
                count += 1

                # Autores
                try:
                    autores = self.client.get_proposicao_autores(prop_id)
                    self.sync_autores(db, prop, autores)
                except Exception as ea:
                    logger.warning(f"Erro ao buscar autores da proposição {prop_id}: {ea}")

                # Temas
                try:
                    temas = self.client.get_proposicao_temas(prop_id)
                    self.sync_temas(db, prop, temas)
                except Exception as et:
                    logger.warning(f"Erro ao buscar temas da proposição {prop_id}: {et}")

                # Tramitações
                try:
                    tramitacoes = self.client.get_proposicao_tramitacoes(prop_id)
                    self.sync_tramitacoes(db, prop, tramitacoes)
                except Exception as etr:
                    logger.warning(f"Erro ao buscar tramitações da proposição {prop_id}: {etr}")

            except Exception as e:
                logger.error(f"Erro ao processar proposição {prop_id}: {e}")

        db.commit()
        logger.info(f"{count} proposições sincronizadas com sucesso.")
        return count
