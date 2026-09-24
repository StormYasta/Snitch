import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models import (
    Votacao, Voto, VotacaoOrientacao, VotacaoProposicao, Deputado, Proposicao, utc_now
)
from app.services.camara.camara_client import CamaraClient

logger = logging.getLogger(__name__)

class VotacoesService:
    def __init__(self, client: Optional[CamaraClient] = None):
        self.client = client or CamaraClient()

    def transform_votacao(self, raw_data: dict) -> dict:
        camara_id = str(raw_data.get("id"))
        return {
            "camara_id": camara_id,
            "data_hora_registro": raw_data.get("dataHoraRegistro") or raw_data.get("data"),
            "descricao": raw_data.get("descricao") or "Votação em plenário",
            "resultado": raw_data.get("resultado"),
            "aprovada": bool(raw_data.get("aprovacao")) if raw_data.get("aprovacao") is not None else None,
            "orgao": raw_data.get("siglaOrgao") or "PLEN",
            "evento_camara_id": raw_data.get("idEvento"),
            "placar_sim": raw_data.get("placarSim") or 0,
            "placar_nao": raw_data.get("placarNao") or 0,
            "placar_abstencao": raw_data.get("placarAbstencao") or 0,
            "placar_obstrucao": raw_data.get("placarObstrucao") or 0,
            "uri": raw_data.get("uri") or f"https://dadosabertos.camara.leg.br/api/v2/votacoes/{camara_id}",
            "dados_raw": raw_data,
        }

    def upsert_votacao(self, db: Session, raw_data: dict) -> Votacao:
        data = self.transform_votacao(raw_data)
        camara_id = data["camara_id"]
        votacao = db.query(Votacao).filter(Votacao.camara_id == camara_id).first()

        if votacao:
            for k, v in data.items():
                if v is not None or getattr(votacao, k) is None:
                    setattr(votacao, k, v)
            votacao.updated_at = utc_now()
        else:
            votacao = Votacao(**data)
            db.add(votacao)

        db.flush()
        return votacao

    def sync_votos(self, db: Session, votacao: Votacao, votos_data: list[dict]):
        db.query(Voto).filter(Voto.votacao_id == votacao.id).delete()
        sim_count = 0
        nao_count = 0
        abst_count = 0
        obst_count = 0

        for v in votos_data:
            dep_info = v.get("deputado_") or v.get("deputado") or {}
            dep_camara_id = dep_info.get("id")
            if not dep_camara_id:
                continue

            # Encontra ou cria deputado básico se ainda não estiver sincronizado
            dep = db.query(Deputado).filter(Deputado.camara_id == dep_camara_id).first()
            if not dep:
                dep = Deputado(
                    camara_id=dep_camara_id,
                    nome_parlamentar=dep_info.get("nome") or "Deputado",
                    sigla_partido=dep_info.get("siglaPartido"),
                    uf=dep_info.get("siglaUf"),
                    url_foto=dep_info.get("urlFoto"),
                    legislatura=dep_info.get("idLegislatura")
                )
                db.add(dep)
                db.flush()

            tipo_voto = (v.get("tipoVoto") or v.get("voto") or "").strip()
            # Normalização de tipos oficiais
            tipo_voto_upper = tipo_voto.upper()
            if "SIM" in tipo_voto_upper:
                sim_count += 1
            elif "NÃO" in tipo_voto_upper or "NAO" in tipo_voto_upper:
                nao_count += 1
            elif "ABST" in tipo_voto_upper:
                abst_count += 1
            elif "OBST" in tipo_voto_upper:
                obst_count += 1

            db.add(Voto(
                votacao_id=votacao.id,
                deputado_id=dep.id,
                tipo_voto=tipo_voto,
                data_hora=v.get("dataHoraVoto") or votacao.data_hora_registro
            ))

        # Atualiza placar se não estiver preenchido originalmente
        if votacao.placar_sim == 0 and sim_count > 0:
            votacao.placar_sim = sim_count
        if votacao.placar_nao == 0 and nao_count > 0:
            votacao.placar_nao = nao_count
        if votacao.placar_abstencao == 0 and abst_count > 0:
            votacao.placar_abstencao = abst_count
        if votacao.placar_obstrucao == 0 and obst_count > 0:
            votacao.placar_obstrucao = obst_count

    def sync_orientacoes(self, db: Session, votacao: Votacao, orientacoes_data: list[dict]):
        db.query(VotacaoOrientacao).filter(VotacaoOrientacao.votacao_id == votacao.id).delete()
        for o in orientacoes_data:
            bancada = o.get("nomeBancada") or o.get("siglaBancada") or o.get("bancada")
            voto = o.get("orientacaoVoto") or o.get("voto")
            if bancada and voto:
                db.add(VotacaoOrientacao(
                    votacao_id=votacao.id,
                    bancada=bancada,
                    orientacao_voto=voto
                ))

    def link_proposicao(self, db: Session, votacao: Votacao, prop: Proposicao, tipo_relacao: str = "Votação relacionada à proposição", descricao: Optional[str] = None):
        link = db.query(VotacaoProposicao).filter(
            VotacaoProposicao.votacao_id == votacao.id,
            VotacaoProposicao.proposicao_id == prop.id
        ).first()

        if not link:
            db.add(VotacaoProposicao(
                votacao_id=votacao.id,
                proposicao_id=prop.id,
                tipo_relacao=tipo_relacao,
                descricao=descricao or votacao.descricao
            ))
            db.flush()

    def sync_votacoes(self, db: Session, limite: int = 30) -> int:
        """Sincroniza votações recentes e respectivos votos nominais."""
        logger.info("Sincronizando votações recentes...")
        params = {
            "ordem": "DESC",
            "ordenarPor": "dataHoraRegistro",
            "itens": min(limite, 100),
        }
        votacoes_lista = self.client.get_votacoes(params=params)
        count = 0

        for item in votacoes_lista[:limite]:
            vot_id = str(item["id"])
            try:
                detalhe = self.client.get_votacao(vot_id)
                raw = detalhe if detalhe else item
                votacao = self.upsert_votacao(db, raw)
                count += 1

                # Votos nominais
                try:
                    votos = self.client.get_votacao_votos(vot_id)
                    self.sync_votos(db, votacao, votos)
                except Exception as ev:
                    logger.warning(f"Erro ao buscar votos da votação {vot_id}: {ev}")

                # Orientações de bancada
                try:
                    orientacoes = self.client.get_votacao_orientacoes(vot_id)
                    self.sync_orientacoes(db, votacao, orientacoes)
                except Exception as eo:
                    logger.warning(f"Erro ao buscar orientações da votação {vot_id}: {eo}")

                # Proposições vinculadas
                proposicao_objeto = raw.get("proposicaoObjeto")
                if proposicao_objeto and isinstance(proposicao_objeto, dict):
                    prop_camara_id = proposicao_objeto.get("id")
                    if prop_camara_id:
                        prop = db.query(Proposicao).filter(Proposicao.camara_id == prop_camara_id).first()
                        if prop:
                            self.link_proposicao(db, votacao, prop, "proposicao_objeto", raw.get("descricao"))

            except Exception as e:
                logger.error(f"Erro ao processar votação {vot_id}: {e}")

        db.commit()
        logger.info(f"{count} votações sincronizadas com sucesso.")
        return count
