"""Comparação factual de 2–3 deputados em um mesmo ano de referência.

Somente registros efetivamente sincronizados entram nas métricas. Um voto Sim/Não
não implica apoio/oposição ao objetivo de uma política: o registro pode tratar
de emendas, destaques ou requerimentos associados à proposição.
"""
from collections import Counter, defaultdict
from datetime import date
from typing import Optional
import unicodedata

from fastapi import HTTPException
from sqlalchemy import func, distinct, desc
from sqlalchemy.orm import Session

from app.models import (
    Deputado, Evento, EventoDeputado, Legislatura, Proposicao,
    ProposicaoAutor, ProposicaoTema, SyncRun, Tema, Votacao,
    VotacaoProposicao, Voto,
)
from app.schemas import (
    ComparativoAtividade, ComparativoDeputado, ComparativoParlamentar,
    ComparativoResponse, ComparativoTema, ComparativoVotos, PageResponse,
    VotacaoComparada,
)


NOTA = (
    "Dados do ano selecionado conforme os registros sincronizados no Snitch. "
    "Dias de atividade consideram datas de votos, eventos e proposições cadastradas, "
    "não toda a atividade profissional. O radar representa apenas votos nominais "
    "Sim e Não em votações vinculadas a proposições que possuem temas registrados; "
    "uma mesma votação pode integrar mais de um tema. Abstenções e obstruções "
    "não entram no denominador dos percentuais. Voto Sim/Não não é inferência "
    "de apoio/oposição ao mérito de uma política pública."
)


def validar_ids(ids: str) -> list[int]:
    try:
        parsed = [int(item.strip()) for item in ids.split(",")]
    except ValueError:
        raise HTTPException(status_code=422, detail="Informe 2 ou 3 IDs separados por vírgula.")
    if len(parsed) not in (2, 3) or any(value <= 0 for value in parsed):
        raise HTTPException(status_code=422, detail="Selecione 2 ou 3 deputados distintos.")
    if len(set(parsed)) != len(parsed):
        raise HTTPException(status_code=422, detail="Não é possível comparar o mesmo deputado duas vezes.")
    return parsed


def validar_periodo(db: Session, ano: int, legislatura: Optional[int]) -> None:
    if legislatura is None:
        return
    leg = db.query(Legislatura).filter(Legislatura.numero == legislatura).first()
    if not leg:
        raise HTTPException(status_code=404, detail="Legislatura não encontrada.")
    inicio = leg.ano_inicio or (int(leg.data_inicio[:4]) if leg.data_inicio else None)
    fim = leg.ano_fim or (int(leg.data_fim[:4]) if leg.data_fim else None)
    if (inicio is not None and ano < inicio) or (fim is not None and ano > fim):
        raise HTTPException(status_code=422, detail="Ano fora do período da legislatura selecionada.")


def _ano_votacao(ano: int):
    # Usa a data oficial da votação; em bases antigas, recorre à data do voto.
    return func.substr(
        func.coalesce(Votacao.data_hora_registro, Voto.data_hora), 1, 4
    ) == str(ano)


def _tipo_voto(value: str) -> str:
    texto = unicodedata.normalize("NFKD", (value or "").strip().lower())
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return {
        "sim": "sim",
        "nao": "nao",
        "abstencao": "abstencao",
        "obstrucao": "obstrucao",
    }.get(texto, "outros")


def _dia(valor: Optional[str], ano: int) -> Optional[str]:
    if valor and len(valor) >= 10 and valor.startswith(f"{ano}-"):
        return valor[:10]
    return None


def _deputados(db: Session, ids: list[int]) -> list[Deputado]:
    rows = db.query(Deputado).filter(Deputado.id.in_(ids)).all()
    index = {dep.id: dep for dep in rows}
    if len(index) != len(ids):
        raise HTTPException(status_code=404, detail="Um ou mais deputados não foram encontrados.")
    return [index[dep_id] for dep_id in ids]


def obter_comparativo(
    db: Session, ids: list[int], ano: int, legislatura: Optional[int]
) -> ComparativoResponse:
    validar_periodo(db, ano, legislatura)
    deputies = _deputados(db, ids)
    votos = db.query(
        Voto.id, Voto.deputado_id, Voto.votacao_id, Voto.tipo_voto,
        Voto.data_hora, Votacao.data_hora_registro,
    ).join(Votacao, Voto.votacao_id == Votacao.id).filter(
        Voto.deputado_id.in_(ids), _ano_votacao(ano)
    ).all()

    distribuicao = {dep_id: Counter() for dep_id in ids}
    votacoes = {dep_id: set() for dep_id in ids}
    dias = {dep_id: set() for dep_id in ids}
    for voto in votos:
        distribuicao[voto.deputado_id][_tipo_voto(voto.tipo_voto)] += 1
        votacoes[voto.deputado_id].add(voto.votacao_id)
        dia = _dia(voto.data_hora or voto.data_hora_registro, ano)
        if dia:
            dias[voto.deputado_id].add(dia)

    participacoes = Counter()
    for dep_id, _evento_id, inicio in (
        db.query(EventoDeputado.deputado_id, Evento.id, Evento.data_inicio)
        .join(Evento, Evento.id == EventoDeputado.evento_id)
        .filter(
            EventoDeputado.deputado_id.in_(ids),
            Evento.data_inicio.like(f"{ano}%"),
        )
        .distinct()
        .all()
    ):
        participacoes[dep_id] += 1
        dia = _dia(inicio, ano)
        if dia:
            dias[dep_id].add(dia)

    autorias = {dep_id: set() for dep_id in ids}
    for dep_id, prop_id, data_apresentacao in (
        db.query(
            ProposicaoAutor.deputado_id, Proposicao.id, Proposicao.data_apresentacao
        ).join(Proposicao, Proposicao.id == ProposicaoAutor.proposicao_id)
        .filter(
            ProposicaoAutor.deputado_id.in_(ids),
            Proposicao.ano == ano,
        )
        .distinct()
        .all()
    ):
        autorias[dep_id].add(prop_id)
        dia = _dia(data_apresentacao, ano)
        if dia:
            dias[dep_id].add(dia)

    # DISTINCT impede duplicidade quando uma votação se relaciona com duas
    # proposições do mesmo tema (conta cada voto uma vez por tema).
    temas = {dep_id: {} for dep_id in ids}
    themed = (
        db.query(
            Voto.id, Voto.deputado_id, Voto.tipo_voto, Tema.id, Tema.nome
        )
        .join(Votacao, Votacao.id == Voto.votacao_id)
        .join(VotacaoProposicao, VotacaoProposicao.votacao_id == Votacao.id)
        .join(ProposicaoTema, ProposicaoTema.proposicao_id == VotacaoProposicao.proposicao_id)
        .join(Tema, Tema.id == ProposicaoTema.tema_id)
        .filter(Voto.deputado_id.in_(ids), _ano_votacao(ano))
        .distinct()
        .all()
    )
    for _voto_id, dep_id, tipo, tema_id, nome in themed:
        if tema_id not in temas[dep_id]:
            temas[dep_id][tema_id] = {"nome": nome, "count": Counter()}
        temas[dep_id][tema_id]["count"][_tipo_voto(tipo)] += 1

    items = []
    for dep in deputies:
        counts = distribuicao[dep.id]
        temas_items = []
        for tema_id, values in sorted(temas[dep.id].items(), key=lambda entry: entry[1]["nome"]):
            c = values["count"]
            validos = c["sim"] + c["nao"]
            total = sum(c.values())
            temas_items.append(ComparativoTema(
                id=tema_id,
                nome=values["nome"],
                sim=c["sim"],
                nao=c["nao"],
                abstencao=c["abstencao"],
                obstrucao=c["obstrucao"],
                outros=c["outros"],
                total_registrado=total,
                total_sim_nao=validos,
                percentual_sim=round(c["sim"] / validos * 100, 1) if validos else None,
                percentual_nao=round(c["nao"] / validos * 100, 1) if validos else None,
            ))
        items.append(ComparativoDeputado(
            deputado=ComparativoParlamentar(
                id=dep.id,
                nome_parlamentar=dep.nome_parlamentar,
                sigla_partido=dep.sigla_partido,
                uf=dep.uf,
                url_foto=dep.url_foto,
                dados_demonstrativos=bool(
                    isinstance(dep.dados_raw, dict) and dep.dados_raw.get("seed")
                ),
            ),
            atividade=ComparativoAtividade(
                votos_registrados=sum(counts.values()),
                votacoes_distintas=len(votacoes[dep.id]),
                dias_com_atividade=len(dias[dep.id]),
                presencas_eventos=participacoes[dep.id],
                proposicoes_autoria=len(autorias[dep.id]),
            ),
            votos=ComparativoVotos(
                sim=counts["sim"], nao=counts["nao"],
                abstencao=counts["abstencao"], obstrucao=counts["obstrucao"],
                outros=counts["outros"],
            ),
            temas=temas_items,
        ))

    latest = (
        db.query(SyncRun)
        .filter(SyncRun.status == "SUCCESS")
        .order_by(desc(SyncRun.finalizado_em))
        .first()
    )
    return ComparativoResponse(
        ano=ano,
        legislatura=legislatura,
        ultima_sincronizacao=latest.finalizado_em if latest else None,
        deputados=items,
        nota_metodologica=NOTA,
    )


def obter_votacoes_comuns(
    db: Session,
    ids: list[int],
    ano: int,
    legislatura: Optional[int],
    page: int,
    page_size: int,
) -> PageResponse[VotacaoComparada]:
    validar_periodo(db, ano, legislatura)
    _deputados(db, ids)

    common = (
        db.query(Voto.votacao_id)
        .join(Votacao, Votacao.id == Voto.votacao_id)
        .filter(Voto.deputado_id.in_(ids), _ano_votacao(ano))
        .group_by(Voto.votacao_id)
        .having(func.count(distinct(Voto.deputado_id)) == len(ids))
        .subquery()
    )
    query = db.query(Votacao).join(common, common.c.votacao_id == Votacao.id)
    total = query.count()
    rows = (
        query.order_by(desc(Votacao.data_hora_registro), desc(Votacao.id))
        .offset((page - 1) * page_size).limit(page_size).all()
    )
    vote_ids = [row.id for row in rows]
    votos = defaultdict(dict)
    main_props = {}
    if vote_ids:
        for votacao_id, dep_id, tipo_voto in (
            db.query(Voto.votacao_id, Voto.deputado_id, Voto.tipo_voto)
            .filter(Voto.votacao_id.in_(vote_ids), Voto.deputado_id.in_(ids))
            .all()
        ):
            votos[votacao_id][str(dep_id)] = tipo_voto

        for votacao_id, prop_id, sigla, numero, prop_ano in (
            db.query(
                VotacaoProposicao.votacao_id,
                Proposicao.id,
                Proposicao.sigla_tipo,
                Proposicao.numero,
                Proposicao.ano,
            )
            .join(Proposicao, Proposicao.id == VotacaoProposicao.proposicao_id)
            .filter(VotacaoProposicao.votacao_id.in_(vote_ids))
            .order_by(Proposicao.id)
            .all()
        ):
            main_props.setdefault(votacao_id, (prop_id, f"{sigla} {numero}/{prop_ano}"))

    items = []
    for row in rows:
        prop_id, prop_name = main_props.get(row.id, (None, None))
        items.append(VotacaoComparada(
            id=row.id,
            camara_id=row.camara_id,
            data_hora=row.data_hora_registro,
            descricao=row.descricao,
            uri=row.uri,
            proposicao_id=prop_id,
            proposicao_nome=prop_name,
            votos={str(dep_id): votos[row.id].get(str(dep_id), "Sem registro") for dep_id in ids},
        ))
    return PageResponse[VotacaoComparada](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max(1, (total + page_size - 1) // page_size),
    )
