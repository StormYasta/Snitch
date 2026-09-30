"""Carga offline de uma amostra temporal da 57ª Legislatura.

O snapshot é gerado no GitHub Actions a partir da API oficial da Câmara.
Ele contém 100 perfis, votações nominais distribuídas entre 2023 e 2026,
votos desses perfis, proposições-objeto, temas, autores e orientações.
"""
from __future__ import annotations

import gzip
import json
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Deputado, Proposicao, Votacao, Voto
from app.services.camara.deputados_service import DeputadosService
from app.services.camara.proposicoes_service import ProposicoesService
from app.services.camara.votacoes_service import VotacoesService

logger = logging.getLogger(__name__)
SNAPSHOT_PATH = Path(__file__).with_name("base57_showcase.json.gz")


def _dep_id(raw_vote: dict) -> int | None:
    info = raw_vote.get("deputado_") or raw_vote.get("deputado") or {}
    try:
        return int(info.get("id")) if info.get("id") is not None else None
    except (TypeError, ValueError):
        return None


def _upsert_snapshot_votes(
    db: Session,
    votacao: Votacao,
    votos_data: list[dict],
    deputados_map: dict[int, Deputado],
) -> int:
    """Atualiza apenas os 100 deputados do snapshot, sem apagar votos externos."""
    count = 0
    for raw in votos_data:
        camara_id = _dep_id(raw)
        dep = deputados_map.get(camara_id) if camara_id is not None else None
        if dep is None:
            continue
        tipo_voto = (raw.get("tipoVoto") or raw.get("voto") or "").strip()
        if not tipo_voto:
            continue

        vote = (
            db.query(Voto)
            .filter(Voto.votacao_id == votacao.id, Voto.deputado_id == dep.id)
            .first()
        )
        info = raw.get("deputado_") or raw.get("deputado") or {}
        values = {
            "tipo_voto": tipo_voto,
            "data_hora": raw.get("dataHoraVoto") or votacao.data_hora_registro,
            "sigla_partido_momento": info.get("siglaPartido"),
            "uf_momento": info.get("siglaUf"),
        }
        if vote is None:
            vote = Voto(votacao_id=votacao.id, deputado_id=dep.id, **values)
            db.add(vote)
        else:
            for field, value in values.items():
                if value is not None:
                    setattr(vote, field, value)
        count += 1
    return count


def load_base57_offline(db: Session, path: Path = SNAPSHOT_PATH) -> dict[str, int]:
    if not path.exists():
        raise RuntimeError(
            "Snapshot da 57ª Legislatura não encontrado. Execute git pull para obter "
            "backend/app/data/base57_showcase.json.gz."
        )

    with gzip.open(path, "rt", encoding="utf-8") as handle:
        payload = json.load(handle)

    meta = payload.get("_meta") or {}
    if int(meta.get("legislatura") or 0) != 57:
        raise RuntimeError("Snapshot inválido: legislatura diferente de 57.")

    deputies_raw = payload.get("deputados") or []
    propositions = payload.get("proposicoes") or []
    votings = payload.get("votacoes") or []
    if len(deputies_raw) != 100:
        raise RuntimeError(
            f"Snapshot inválido: esperado 100 deputados, encontrado {len(deputies_raw)}."
        )

    deputados_service = DeputadosService()
    proposicoes_service = ProposicoesService()
    votacoes_service = VotacoesService()

    deputados_map: dict[int, Deputado] = {}
    for raw in deputies_raw:
        dep = deputados_service.upsert_deputado(db, raw)
        saved = dict(dep.dados_raw or {})
        saved["_snitch_base57"] = {
            "retrieved_at": meta.get("retrieved_at"),
            "legislatura": 57,
            "selection": meta.get("deputy_selection"),
        }
        dep.dados_raw = saved
        deputados_map[dep.camara_id] = dep
    db.flush()

    proposicoes_map: dict[int, Proposicao] = {}
    temas_count = 0
    autores_count = 0
    for bundle in propositions:
        raw = bundle.get("dados") or {}
        if not raw.get("id"):
            continue
        prop = proposicoes_service.upsert_proposicao(db, raw)
        autores = bundle.get("autores") or []
        temas = bundle.get("temas") or []
        proposicoes_service.sync_autores(db, prop, autores)
        proposicoes_service.sync_temas(db, prop, temas)
        proposicoes_map[int(raw["id"])] = prop
        autores_count += len(autores)
        temas_count += len(temas)
    db.flush()

    votos_count = 0
    orientacoes_count = 0
    links_count = 0
    for bundle in votings:
        raw = bundle.get("dados") or {}
        if raw.get("id") is None:
            continue
        votacao = votacoes_service.upsert_votacao(db, raw)
        votos_count += _upsert_snapshot_votes(
            db, votacao, bundle.get("votos") or [], deputados_map
        )
        orientacoes = bundle.get("orientacoes") or []
        votacoes_service.sync_orientacoes(db, votacao, orientacoes)
        orientacoes_count += len(orientacoes)

        prop_id = bundle.get("proposicao_objeto_id")
        prop = proposicoes_map.get(int(prop_id)) if prop_id is not None else None
        if prop is not None:
            votacoes_service.link_proposicao(
                db,
                votacao,
                prop,
                "proposicao_objeto",
                raw.get("descricao"),
            )
            links_count += 1

    db.commit()
    result = {
        "deputados": len(deputados_map),
        "proposicoes": len(proposicoes_map),
        "temas_relacionados": temas_count,
        "autorias": autores_count,
        "votacoes": len(votings),
        "votos": votos_count,
        "orientacoes": orientacoes_count,
        "vinculos_votacao_proposicao": links_count,
    }
    logger.info(
        "Base offline 57ª carregada (%s; acesso oficial em %s).",
        result,
        meta.get("retrieved_at") or "data não informada",
    )
    return result
