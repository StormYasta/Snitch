import re
from typing import Optional
from collections import defaultdict
from sqlalchemy import or_, and_, func, desc, asc, distinct
from sqlalchemy.orm import Session
from app.models import (
    Deputado, DeputadoHistorico, Legislatura, Mandato, FiliacaoPartidaria,
    Proposicao, ProposicaoAutor, Tema, ProposicaoTema,
    Tramitacao, Votacao, VotacaoProposicao, VotacaoOrientacao, Voto, Evento, EventoDeputado,
    Instituicao, RelacaoInstitucional, Cargo, OcupacaoCargo, SyncRun
)

# ==================== DEPUTADOS ====================

def get_deputados(
    db: Session,
    busca: Optional[str] = None,
    partido: Optional[str] = None,
    uf: Optional[str] = None,
    situacao: Optional[str] = None,
    legislatura: Optional[int] = None,
    ordenar_por: str = "nome",
    ordem: str = "asc",
    page: int = 1,
    page_size: int = 12
):
    query = db.query(Deputado)

    if busca:
        busca_clean = f"%{busca.strip()}%"
        query = query.filter(
            or_(
                Deputado.nome_parlamentar.ilike(busca_clean),
                Deputado.nome_civil.ilike(busca_clean),
                Deputado.sigla_partido.ilike(busca_clean)
            )
        )

    if partido:
        query = query.filter(
            or_(
                Deputado.sigla_partido == partido.upper(),
                Deputado.mandatos.any(Mandato.sigla_partido == partido.upper()),
                Deputado.filiacoes.any(FiliacaoPartidaria.sigla_partido == partido.upper())
            )
        )

    if uf:
        query = query.filter(
            or_(
                Deputado.uf == uf.upper(),
                Deputado.mandatos.any(Mandato.uf == uf.upper())
            )
        )

    if situacao:
        sit_clean = situacao.strip().lower()
        if "exerc" in sit_clean:
            query = query.filter(
                or_(
                    Deputado.situacao.ilike("%exerc%"),
                    Deputado.mandatos.any(and_(Mandato.legislatura_numero == 57, Mandato.situacao.ilike("%exerc%")))
                )
            )
        elif "encerrad" in sit_clean:
            query = query.filter(
                or_(
                    Deputado.situacao.ilike("%encerrad%"),
                    Deputado.situacao.ilike("%afastad%"),
                    and_(Deputado.legislatura.isnot(None), Deputado.legislatura < 57)
                )
            )
        else:
            query = query.filter(Deputado.situacao.ilike(f"%{situacao}%"))

    if legislatura:
        query = query.filter(
            or_(
                Deputado.legislatura == legislatura,
                Deputado.mandatos.any(Mandato.legislatura_numero == legislatura)
            )
        )

    total = query.count()

    # Ordenação estritamente objetiva
    if ordenar_por == "nome":
        query = query.order_by(asc(Deputado.nome_parlamentar) if ordem == "asc" else desc(Deputado.nome_parlamentar))
    else:
        query = query.order_by(asc(Deputado.id))

    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    # Preenche métricas resumidas para cada item
    result_items = []
    for dep in items:
        tot_votos = db.query(func.count(Voto.id)).filter(Voto.deputado_id == dep.id).scalar() or 0
        tot_eventos = db.query(func.count(EventoDeputado.id)).filter(EventoDeputado.deputado_id == dep.id).scalar() or 0
        tot_props = db.query(func.count(ProposicaoAutor.id)).filter(ProposicaoAutor.deputado_id == dep.id).scalar() or 0

        result_items.append({
            "id": dep.id,
            "camara_id": dep.camara_id,
            "nome_parlamentar": dep.nome_parlamentar,
            "nome_civil": dep.nome_civil,
            "sigla_partido": dep.sigla_partido,
            "uf": dep.uf,
            "url_foto": dep.url_foto,
            "situacao": dep.situacao,
            "legislatura": dep.legislatura,
            "email": dep.email,
            "total_votos": tot_votos,
            "total_eventos": tot_eventos,
            "total_proposicoes": tot_props
        })

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return {
        "items": result_items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

def get_deputado_by_id(db: Session, deputado_id: int):
    return db.query(Deputado).filter(Deputado.id == deputado_id).first()

def get_deputado_atividade(db: Session, deputado_id: int):
    # 1. Total de votos
    tot_votos = db.query(func.count(Voto.id)).filter(Voto.deputado_id == deputado_id).scalar() or 0

    # 2. Votações distintas
    tot_votacoes = db.query(func.count(distinct(Voto.votacao_id))).filter(Voto.deputado_id == deputado_id).scalar() or 0

    # 3. Presenças em eventos
    tot_eventos = db.query(func.count(EventoDeputado.id)).filter(EventoDeputado.deputado_id == deputado_id).scalar() or 0

    # 4. Proposições de autoria
    tot_proposicoes = db.query(func.count(ProposicaoAutor.id)).filter(ProposicaoAutor.deputado_id == deputado_id).scalar() or 0

    # 5. Dias com atividade registrada (cálculo de datas únicas sem duplicidade)
    datas_unicas = set()

    # Votos: extrai substring da data YYYY-MM-DD
    votos_datas = db.query(Voto.data_hora).filter(Voto.deputado_id == deputado_id, Voto.data_hora.isnot(None)).all()
    for (dh,) in votos_datas:
        if dh:
            datas_unicas.add(str(dh)[:10])

    # Eventos: extrai data de início YYYY-MM-DD
    eventos_datas = (
        db.query(Evento.data_inicio)
        .join(EventoDeputado, Evento.id == EventoDeputado.evento_id)
        .filter(EventoDeputado.deputado_id == deputado_id, Evento.data_inicio.isnot(None))
        .all()
    )
    for (di,) in eventos_datas:
        if di:
            datas_unicas.add(str(di)[:10])

    # Autoria de proposições: extrai data de apresentação
    props_datas = (
        db.query(Proposicao.data_apresentacao)
        .join(ProposicaoAutor, Proposicao.id == ProposicaoAutor.proposicao_id)
        .filter(ProposicaoAutor.deputado_id == deputado_id, Proposicao.data_apresentacao.isnot(None))
        .all()
    )
    for (da,) in props_datas:
        if da:
            datas_unicas.add(str(da)[:10])

    return {
        "votos_registrados": tot_votos,
        "votacoes_distintas": tot_votacoes,
        "dias_com_atividade": len(datas_unicas),
        "presencas_eventos": tot_eventos,
        "proposicoes_autoria": tot_proposicoes
    }

def get_deputado_temporal(
    db: Session,
    deputado_id: int,
    agrupamento: str = "mes",
    legislatura: Optional[int] = None,
    ano: Optional[int] = None
):
    """Gera série temporal de votos, eventos e proposições agrupados por mês (YYYY-MM) ou ano (YYYY).
    Permite filtrar por toda a trajetória (padrão), por legislatura ou por ano específico.
    """
    serie = defaultdict(lambda: {"votos": 0, "eventos": 0, "proposicoes": 0})

    inicio_filtro = None
    fim_filtro = None
    if ano:
        inicio_filtro = f"{ano}-01-01"
        fim_filtro = f"{ano}-12-31"
    elif legislatura:
        leg = db.query(Legislatura).filter(Legislatura.numero == legislatura).first()
        if leg:
            inicio_filtro = str(leg.data_inicio)[:10] if leg.data_inicio else None
            fim_filtro = str(leg.data_fim)[:10] if leg.data_fim else None

    def in_range(date_str: str) -> bool:
        if not date_str:
            return False
        s = str(date_str)[:10]
        if inicio_filtro and s < inicio_filtro:
            return False
        if fim_filtro and s > fim_filtro:
            return False
        return True

    def format_periodo(date_str: str) -> str:
        s = str(date_str)[:10]
        if agrupamento == "ano":
            return s[:4]
        return s[:7]

    # Votos
    votos = db.query(Voto.data_hora).filter(Voto.deputado_id == deputado_id, Voto.data_hora.isnot(None)).all()
    for (dh,) in votos:
        if in_range(dh):
            p = format_periodo(dh)
            if len(p) >= 4:
                serie[p]["votos"] += 1

    # Eventos
    eventos = (
        db.query(Evento.data_inicio)
        .join(EventoDeputado, Evento.id == EventoDeputado.evento_id)
        .filter(EventoDeputado.deputado_id == deputado_id, Evento.data_inicio.isnot(None))
        .all()
    )
    for (di,) in eventos:
        if in_range(di):
            p = format_periodo(di)
            if len(p) >= 4:
                serie[p]["eventos"] += 1

    # Proposições
    props = (
        db.query(Proposicao.data_apresentacao)
        .join(ProposicaoAutor, Proposicao.id == ProposicaoAutor.proposicao_id)
        .filter(ProposicaoAutor.deputado_id == deputado_id, Proposicao.data_apresentacao.isnot(None))
        .all()
    )
    for (da,) in props:
        if in_range(da):
            p = format_periodo(da)
            if len(p) >= 4:
                serie[p]["proposicoes"] += 1

    resultado = []
    for periodo in sorted(serie.keys()):
        resultado.append({
            "periodo": periodo,
            "votos": serie[periodo]["votos"],
            "eventos": serie[periodo]["eventos"],
            "proposicoes": serie[periodo]["proposicoes"]
        })

    return resultado

def get_deputado_trajetoria(db: Session, deputado_id: int):
    """Retorna o histórico completo de mandatos, filiações partidárias e timeline de marcos do parlamentar."""
    dep = db.query(Deputado).filter(Deputado.id == deputado_id).first()
    if not dep:
        return None

    mandatos_db = db.query(Mandato).filter(Mandato.deputado_id == deputado_id).order_by(desc(Mandato.legislatura_numero)).all()
    filiacoes_db = db.query(FiliacaoPartidaria).filter(FiliacaoPartidaria.deputado_id == deputado_id).order_by(asc(FiliacaoPartidaria.data_inicio)).all()

    timeline = []

    # Milestones a partir de mandatos
    for m in mandatos_db:
        leg_str = f"{m.legislatura_numero}ª Legislatura" if m.legislatura_numero else "Legislatura"
        ano_inicio = int(m.data_inicio[:4]) if m.data_inicio and len(m.data_inicio) >= 4 else None
        timeline.append({
            "tipo": "MANDATO",
            "titulo": f"Mandato como {m.cargo or 'Deputado Federal'} ({leg_str})",
            "subtitulo": f"{m.sigla_partido}/{m.uf} - {m.situacao or 'Em exercício'}",
            "data": m.data_inicio,
            "ano": ano_inicio,
            "legislatura": m.legislatura_numero,
            "partido": m.sigla_partido,
            "uf": m.uf,
            "detalhes": f"Condição eleitoral: {m.condicao_eleitoral or 'Titular'}. Período: {m.data_inicio or ''} até {m.data_fim or 'atual'}."
        })

    # Milestones a partir de filiações partidárias
    for f in filiacoes_db:
        ano_f = int(f.data_inicio[:4]) if f.data_inicio and len(f.data_inicio) >= 4 else None
        periodo = f"a partir de {f.data_inicio}" if f.data_inicio else ""
        if f.data_fim:
            periodo += f" até {f.data_fim}"
        timeline.append({
            "tipo": "FILIACAO",
            "titulo": f"Filiação Partidária ao {f.sigla_partido}",
            "subtitulo": f.nome_partido or f.sigla_partido,
            "data": f.data_inicio,
            "ano": ano_f,
            "legislatura": None,
            "partido": f.sigla_partido,
            "uf": dep.uf,
            "detalhes": f"Filiação partidária oficial ({periodo}). Fonte: {f.fonte or 'Câmara dos Deputados'}."
        })

    # Se não houver mandatos no modelo Mandato, infere a partir do campo legislatura do próprio deputado
    if not mandatos_db and dep.legislatura:
        leg_num = dep.legislatura
        ano_ini = 2023 if leg_num == 57 else (2019 if leg_num == 56 else (2015 if leg_num == 55 else None))
        timeline.append({
            "tipo": "MANDATO",
            "titulo": f"Mandato como Deputado Federal ({leg_num}ª Legislatura)",
            "subtitulo": f"{dep.sigla_partido}/{dep.uf} - {dep.situacao or 'Em exercício'}",
            "data": f"{ano_ini}-02-01" if ano_ini else None,
            "ano": ano_ini,
            "legislatura": leg_num,
            "partido": dep.sigla_partido,
            "uf": dep.uf,
            "detalhes": f"Situação: {dep.descricao_status or dep.situacao}."
        })

    # Ordena timeline: mais recente primeiro
    def sort_key(item):
        return item.get("data") or (f"{item.get('ano')}-01-01" if item.get("ano") else "")

    timeline.sort(key=sort_key, reverse=True)

    return {
        "deputado_id": dep.id,
        "nome_parlamentar": dep.nome_parlamentar,
        "sigla_partido_atual": dep.sigla_partido,
        "uf_atual": dep.uf,
        "mandatos": mandatos_db,
        "filiacoes": filiacoes_db,
        "timeline": timeline
    }

def get_deputado_distribuicao_votos(db: Session, deputado_id: int):
    counts = (
        db.query(Voto.tipo_voto, func.count(Voto.id))
        .filter(Voto.deputado_id == deputado_id)
        .group_by(Voto.tipo_voto)
        .all()
    )
    total = sum(c for _, c in counts)
    res = []
    for tipo, qtd in counts:
        pct = round((qtd / total) * 100, 1) if total > 0 else 0.0
        res.append({
            "tipo_voto": tipo,
            "quantidade": qtd,
            "percentual": pct
        })
    return res

def get_deputado_votos(
    db: Session,
    deputado_id: int,
    tipo_voto: Optional[str] = None,
    tipo_proposicao: Optional[str] = None,
    ano: Optional[int] = None,
    page: int = 1,
    page_size: int = 10
):
    query = (
        db.query(Voto, Votacao)
        .join(Votacao, Voto.votacao_id == Votacao.id)
        .filter(Voto.deputado_id == deputado_id)
    )

    if tipo_voto:
        query = query.filter(Voto.tipo_voto.ilike(f"%{tipo_voto}%"))

    if ano:
        query = query.filter(Votacao.data_hora_registro.ilike(f"{ano}%"))

    total = query.count()
    offset = (page - 1) * page_size
    records = query.order_by(desc(Votacao.data_hora_registro)).offset(offset).limit(page_size).all()

    items = []
    for voto, votacao in records:
        # Busca proposição relacionada principal se houver
        vp = db.query(VotacaoProposicao).filter(VotacaoProposicao.votacao_id == votacao.id).first()
        prop = db.query(Proposicao).filter(Proposicao.id == vp.proposicao_id).first() if vp else None

        items.append({
            "id": voto.id,
            "votacao_id": votacao.id,
            "votacao_camara_id": votacao.camara_id,
            "data_hora": voto.data_hora or votacao.data_hora_registro,
            "descricao_votacao": votacao.descricao,
            "tipo_voto": voto.tipo_voto,
            "sigla_partido_momento": voto.sigla_partido_momento,
            "uf_momento": voto.uf_momento,
            "proposicao_id": prop.id if prop else None,
            "proposicao_sigla": prop.sigla_tipo if prop else None,
            "proposicao_numero": prop.numero if prop else None,
            "proposicao_ano": prop.ano if prop else None,
            "proposicao_ementa": prop.ementa if prop else None
        })

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

def get_deputado_proposicoes(
    db: Session,
    deputado_id: int,
    relacao: str = "autoria",
    page: int = 1,
    page_size: int = 10
):
    if relacao == "autoria":
        query = (
            db.query(Proposicao)
            .join(ProposicaoAutor, Proposicao.id == ProposicaoAutor.proposicao_id)
            .filter(ProposicaoAutor.deputado_id == deputado_id)
        )
    else:
        # Participação em votação nominal
        query = (
            db.query(Proposicao)
            .join(VotacaoProposicao, Proposicao.id == VotacaoProposicao.proposicao_id)
            .join(Votacao, VotacaoProposicao.votacao_id == Votacao.id)
            .join(Voto, Votacao.id == Voto.votacao_id)
            .filter(Voto.deputado_id == deputado_id)
            .distinct()
        )

    total = query.count()
    offset = (page - 1) * page_size
    props = query.order_by(desc(Proposicao.ano), desc(Proposicao.numero)).offset(offset).limit(page_size).all()

    items = []
    for p in props:
        temas = [pt.tema.nome for pt in p.temas if pt.tema]
        autor_p = p.autores[0].nome_autor if p.autores else None
        items.append({
            "id": p.id,
            "camara_id": p.camara_id,
            "sigla_tipo": p.sigla_tipo,
            "numero": p.numero,
            "ano": p.ano,
            "ementa": p.ementa,
            "data_apresentacao": p.data_apresentacao,
            "situacao": p.situacao,
            "descricao_situacao": p.descricao_situacao,
            "orgao_atual": p.orgao_atual,
            "temas": temas,
            "autor_principal": autor_p,
            "autor_principal_deputado_id": p.autores[0].deputado_id if p.autores else None
        })

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

def get_deputado_eventos(db: Session, deputado_id: int):
    eventos = (
        db.query(Evento)
        .join(EventoDeputado, Evento.id == EventoDeputado.evento_id)
        .filter(EventoDeputado.deputado_id == deputado_id)
        .order_by(desc(Evento.data_inicio))
        .all()
    )
    return eventos

def get_deputado_historico(db: Session, deputado_id: int):
    return (
        db.query(DeputadoHistorico)
        .filter(DeputadoHistorico.deputado_id == deputado_id)
        .order_by(desc(DeputadoHistorico.data_hora))
        .all()
    )

# ==================== PROPOSICOES ====================

def get_proposicoes(
    db: Session,
    busca: Optional[str] = None,
    tipo: Optional[str] = None,
    ano: Optional[int] = None,
    situacao: Optional[str] = None,
    tema: Optional[str] = None,
    autor: Optional[str] = None,
    page: int = 1,
    page_size: int = 12
):
    query = db.query(Proposicao)

    if busca:
        busca_clean = busca.strip()
        # Se for no formato "PL 1234/2025" ou "PL 1234"
        match = re.match(r"^([A-Za-z]+)\s*(\d+)(?:/(\d+))?", busca_clean)
        if match:
            s_tipo = match.group(1).upper()
            s_num = int(match.group(2))
            s_ano = int(match.group(3)) if match.group(3) else None
            cond = and_(
                Proposicao.sigla_tipo.ilike(s_tipo),
                Proposicao.numero == s_num
            )
            if s_ano:
                cond = and_(cond, Proposicao.ano == s_ano)
            query = query.filter(cond)
        elif busca_clean.isdigit():
            s_num = int(busca_clean)
            query = query.filter(
                or_(
                    Proposicao.numero == s_num,
                    Proposicao.ano == s_num,
                    Proposicao.ementa.ilike(f"%{busca_clean}%")
                )
            )
        else:
            query = query.filter(
                or_(
                    Proposicao.ementa.ilike(f"%{busca_clean}%"),
                    Proposicao.ementa_detalhada.ilike(f"%{busca_clean}%"),
                    Proposicao.sigla_tipo.ilike(f"%{busca_clean}%")
                )
            )

    if tipo:
        query = query.filter(Proposicao.sigla_tipo == tipo.upper())

    if ano:
        query = query.filter(Proposicao.ano == ano)

    if situacao:
        query = query.filter(Proposicao.situacao.ilike(f"%{situacao}%"))

    if tema:
        query = query.join(ProposicaoTema, Proposicao.id == ProposicaoTema.proposicao_id).join(Tema, ProposicaoTema.tema_id == Tema.id).filter(Tema.nome.ilike(f"%{tema}%"))

    if autor:
        query = query.join(ProposicaoAutor, Proposicao.id == ProposicaoAutor.proposicao_id).filter(ProposicaoAutor.nome_autor.ilike(f"%{autor}%"))

    total = query.count()
    offset = (page - 1) * page_size
    props = query.order_by(desc(Proposicao.ano), desc(Proposicao.numero)).offset(offset).limit(page_size).all()

    items = []
    for p in props:
        temas = [pt.tema.nome for pt in p.temas if pt.tema]
        autor_p = p.autores[0].nome_autor if p.autores else None
        dep_id = p.autores[0].deputado_id if p.autores else None
        items.append({
            "id": p.id,
            "camara_id": p.camara_id,
            "sigla_tipo": p.sigla_tipo,
            "numero": p.numero,
            "ano": p.ano,
            "ementa": p.ementa,
            "data_apresentacao": p.data_apresentacao,
            "situacao": p.situacao,
            "descricao_situacao": p.descricao_situacao,
            "orgao_atual": p.orgao_atual,
            "temas": temas,
            "autor_principal": autor_p,
            "autor_principal_deputado_id": dep_id
        })

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

def get_proposicao_by_id(db: Session, proposicao_id: int):
    return db.query(Proposicao).filter(Proposicao.id == proposicao_id).first()

# ==================== VOTACOES ====================

def get_votacao_by_id(db: Session, votacao_id: int):
    return db.query(Votacao).filter(Votacao.id == votacao_id).first()

def get_votos_by_votacao(
    db: Session,
    votacao_id: int,
    tipo_voto: Optional[str] = None,
    partido: Optional[str] = None,
    uf: Optional[str] = None,
    busca: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    query = (
        db.query(Voto, Deputado)
        .join(Deputado, Voto.deputado_id == Deputado.id)
        .filter(Voto.votacao_id == votacao_id)
    )

    if tipo_voto:
        query = query.filter(Voto.tipo_voto.ilike(f"%{tipo_voto}%"))

    if partido:
        query = query.filter(
            or_(
                Voto.sigla_partido_momento == partido.upper(),
                and_(Voto.sigla_partido_momento.is_(None), Deputado.sigla_partido == partido.upper())
            )
        )

    if uf:
        query = query.filter(
            or_(
                Voto.uf_momento == uf.upper(),
                and_(Voto.uf_momento.is_(None), Deputado.uf == uf.upper())
            )
        )

    if busca:
        query = query.filter(Deputado.nome_parlamentar.ilike(f"%{busca}%"))

    total = query.count()
    offset = (page - 1) * page_size
    records = query.order_by(asc(Deputado.nome_parlamentar)).offset(offset).limit(page_size).all()

    items = []
    for voto, dep in records:
        sigla_momento = voto.sigla_partido_momento or dep.sigla_partido
        uf_momento = voto.uf_momento or dep.uf
        items.append({
            "id": voto.id,
            "deputado_id": dep.id,
            "camara_id": dep.camara_id,
            "nome_parlamentar": dep.nome_parlamentar,
            "sigla_partido": sigla_momento,
            "sigla_partido_momento": sigla_momento,
            "sigla_partido_atual": dep.sigla_partido,
            "uf": uf_momento,
            "uf_momento": uf_momento,
            "url_foto": dep.url_foto,
            "tipo_voto": voto.tipo_voto,
            "data_hora": voto.data_hora
        })

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

# ==================== STATS & BUSCA ====================

def get_platform_stats(db: Session):
    tot_deps = db.query(func.count(Deputado.id)).scalar() or 0
    tot_props = db.query(func.count(Proposicao.id)).scalar() or 0
    tot_vots = db.query(func.count(Votacao.id)).scalar() or 0
    tot_votos = db.query(func.count(Voto.id)).scalar() or 0

    last_sync = db.query(SyncRun).filter(SyncRun.status == "SUCCESS").order_by(desc(SyncRun.finalizado_em)).first()
    sync_str = last_sync.finalizado_em.strftime("%d/%m/%Y às %H:%M") if last_sync and last_sync.finalizado_em else None

    # Votações recentes
    vots_recentes = db.query(Votacao).order_by(desc(Votacao.data_hora_registro)).limit(5).all()
    vots_list = []
    for v in vots_recentes:
        vots_list.append({
            "id": v.id,
            "camara_id": v.camara_id,
            "data_hora_registro": v.data_hora_registro,
            "descricao": v.descricao,
            "resultado": v.resultado,
            "aprovada": v.aprovada,
            "orgao": v.orgao,
            "placar_sim": v.placar_sim,
            "placar_nao": v.placar_nao,
            "placar_abstencao": v.placar_abstencao,
            "placar_obstrucao": v.placar_obstrucao,
            "tipo_relacao": "Votação relacionada à proposição"
        })

    # Proposições recentes
    props_recentes = db.query(Proposicao).order_by(desc(Proposicao.ano), desc(Proposicao.numero)).limit(5).all()
    props_list = []
    for p in props_recentes:
        temas = [pt.tema.nome for pt in p.temas if pt.tema]
        autor_p = p.autores[0].nome_autor if p.autores else None
        dep_id = p.autores[0].deputado_id if p.autores else None
        props_list.append({
            "id": p.id,
            "camara_id": p.camara_id,
            "sigla_tipo": p.sigla_tipo,
            "numero": p.numero,
            "ano": p.ano,
            "ementa": p.ementa,
            "data_apresentacao": p.data_apresentacao,
            "situacao": p.situacao,
            "descricao_situacao": p.descricao_situacao,
            "orgao_atual": p.orgao_atual,
            "temas": temas,
            "autor_principal": autor_p,
            "autor_principal_deputado_id": dep_id
        })

    return {
        "total_deputados": tot_deps,
        "total_proposicoes": tot_props,
        "total_votacoes": tot_vots,
        "total_votos": tot_votos,
        "ultima_sincronizacao": sync_str,
        "votacoes_recentes": vots_list,
        "proposicoes_recentes": props_list
    }

def global_search(db: Session, query: str):
    q_clean = query.strip()
    res_deps = []
    res_props = []
    res_vots = []

    # Procura proposição por número/tipo
    match_prop = re.match(r"^([A-Za-z]+)\s*(\d+)(?:/(\d+))?", q_clean)
    if match_prop:
        s_tipo = match_prop.group(1).upper()
        s_num = int(match_prop.group(2))
        s_ano = int(match_prop.group(3)) if match_prop.group(3) else None
        cond = and_(Proposicao.sigla_tipo.ilike(s_tipo), Proposicao.numero == s_num)
        if s_ano:
            cond = and_(cond, Proposicao.ano == s_ano)
        props = db.query(Proposicao).filter(cond).limit(10).all()
    elif q_clean.isdigit():
        s_num = int(q_clean)
        props = db.query(Proposicao).filter(
            or_(
                Proposicao.numero == s_num,
                Proposicao.ano == s_num,
                Proposicao.ementa.ilike(f"%{q_clean}%")
            )
        ).limit(10).all()
    else:
        props = db.query(Proposicao).filter(
            or_(
                Proposicao.ementa.ilike(f"%{q_clean}%"),
                Proposicao.sigla_tipo.ilike(f"%{q_clean}%")
            )
        ).limit(10).all()

    for p in props:
        temas = [pt.tema.nome for pt in p.temas if pt.tema]
        autor_p = p.autores[0].nome_autor if p.autores else None
        dep_id = p.autores[0].deputado_id if p.autores else None
        res_props.append({
            "id": p.id,
            "camara_id": p.camara_id,
            "sigla_tipo": p.sigla_tipo,
            "numero": p.numero,
            "ano": p.ano,
            "ementa": p.ementa,
            "data_apresentacao": p.data_apresentacao,
            "situacao": p.situacao,
            "descricao_situacao": p.descricao_situacao,
            "orgao_atual": p.orgao_atual,
            "temas": temas,
            "autor_principal": autor_p,
            "autor_principal_deputado_id": dep_id
        })

    # Procura deputados por nome ou partido
    deps = db.query(Deputado).filter(
        or_(
            Deputado.nome_parlamentar.ilike(f"%{q_clean}%"),
            Deputado.nome_civil.ilike(f"%{q_clean}%"),
            Deputado.sigla_partido.ilike(f"%{q_clean}%")
        )
    ).limit(10).all()

    for d in deps:
        res_deps.append({
            "id": d.id,
            "camara_id": d.camara_id,
            "nome_parlamentar": d.nome_parlamentar,
            "nome_civil": d.nome_civil,
            "sigla_partido": d.sigla_partido,
            "uf": d.uf,
            "url_foto": d.url_foto,
            "situacao": d.situacao,
            "legislatura": d.legislatura,
            "email": d.email,
            "total_votos": 0,
            "total_eventos": 0,
            "total_proposicoes": 0
        })

    # Procura votações por descrição
    vots = db.query(Votacao).filter(Votacao.descricao.ilike(f"%{q_clean}%")).limit(10).all()
    for v in vots:
        res_vots.append({
            "id": v.id,
            "camara_id": v.camara_id,
            "data_hora_registro": v.data_hora_registro,
            "descricao": v.descricao,
            "resultado": v.resultado,
            "aprovada": v.aprovada,
            "orgao": v.orgao,
            "placar_sim": v.placar_sim,
            "placar_nao": v.placar_nao,
            "placar_abstencao": v.placar_abstencao,
            "placar_obstrucao": v.placar_obstrucao,
            "tipo_relacao": "Votação relacionada à proposição"
        })

    return {
        "query": q_clean,
        "deputados": res_deps,
        "proposicoes": res_props,
        "votacoes": res_vots
    }


# ==================== LEGISLATURAS ====================

def get_legislaturas(db: Session):
    """Retorna todas as legislaturas cadastradas ordenadas de forma decrescente."""
    return db.query(Legislatura).order_by(desc(Legislatura.numero)).all()


# ==================== ENTENDA O GOVERNO: DIMENSÃO INSTITUCIONAL ====================

def get_estrutura_governo(db: Session):
    """Retorna um mapa institucional compacto para navegação.

    Unidades internas muito profundas do SIORG continuam disponíveis na página de
    detalhe da instituição, mas não são despejadas todas de uma vez no mapa.
    """
    tipos_mapa = {
        "ESTADO", "ENTE_FEDERATIVO", "PODER", "GRUPO_INSTITUCIONAL",
        "CASA_LEGISLATIVA", "TRIBUNAL", "ORGAO_CONTROLE", "ORGAO_AUTONOMO",
        "MINISTERIO", "AUTARQUIA", "FUNDACAO", "ORGAO", "NOTA_CONSTITUCIONAL"
    }
    instituicoes = (
        db.query(Instituicao)
        .filter(Instituicao.ativo == True, Instituicao.tipo.in_(tipos_mapa))
        .all()
    )
    visible_ids = {i.id for i in instituicoes}
    relacoes = (
        db.query(RelacaoInstitucional)
        .filter(
            RelacaoInstitucional.instituicao_origem_id.in_(visible_ids),
            RelacaoInstitucional.instituicao_destino_id.in_(visible_ids),
        )
        .all()
    )

    # Mapeia cada instituição para um nó navegável
    nodes = []
    inst_dict = {i.id: i for i in instituicoes}

    # Identifica o parentId para cada nó baseado na relação mais forte (HIERARQUIA ou COMPOSICAO)
    parent_map = {}
    for r in relacoes:
        if r.tipo_relacao in ["HIERARQUIA_ADMINISTRATIVA", "COMPOSICAO"]:
            # origem_id -> destino_id (origem é subordinada / componente de destino)
            if r.instituicao_origem_id not in parent_map:
                parent_map[r.instituicao_origem_id] = r.instituicao_destino_id

    for i in instituicoes:
        is_camara = (i.codigo_externo == "CAMARA_DEPUTADOS" or i.sigla == "CD")
        nodes.append({
            "id": i.id,
            "nome": i.nome,
            "sigla": i.sigla,
            "tipo": i.tipo,
            "poder": i.poder,
            "esfera": i.esfera,
            "nivel_federativo": i.nivel_federativo,
            "codigo_externo": i.codigo_externo,
            "natureza_juridica": i.natureza_juridica,
            "descricao": i.descricao,
            "site_oficial": i.site_oficial,
            "integrado": is_camara,
            "parentId": parent_map.get(i.id)
        })

    edges = []
    for r in relacoes:
        edges.append({
            "id": f"rel-{r.id}",
            "source": r.instituicao_origem_id,
            "target": r.instituicao_destino_id,
            "tipo_relacao": r.tipo_relacao,
            "descricao": r.descricao
        })

    return {
        "nodes": nodes,
        "edges": edges,
        "legenda": {
            "HIERARQUIA_ADMINISTRATIVA": "Linha contínua: Subordinação hierárquica e administrativa direta",
            "VINCULACAO": "Linha tracejada: Vinculação administrativa / supervisão ministerial (DL 200/1967)",
            "COMPOSICAO": "Linha sólida de estrutura: Ente componente ou câmara de poder",
            "CONTROLE": "Linha pontilhada: Controle externo ou fiscalização de legalidade e contas",
            "FISCALIZACAO": "Linha pontilhada: Fiscalização constitucional"
        }
    }

def get_instituicoes(
    db: Session,
    esfera: Optional[str] = None,
    poder: Optional[str] = None,
    tipo: Optional[str] = None,
    nivel_federativo: Optional[str] = None,
    busca: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """Consulta paginada de instituições públicas brasileiras com filtros objetivos."""
    query = db.query(Instituicao).filter(Instituicao.ativo == True)

    if esfera:
        query = query.filter(Instituicao.esfera.ilike(f"%{esfera}%"))

    if poder:
        query = query.filter(Instituicao.poder.ilike(f"%{poder}%"))

    if tipo:
        query = query.filter(Instituicao.tipo == tipo.upper())

    if nivel_federativo:
        query = query.filter(Instituicao.nivel_federativo.ilike(f"%{nivel_federativo}%"))

    if busca:
        busca_clean = f"%{busca.strip()}%"
        query = query.filter(
            or_(
                Instituicao.nome.ilike(busca_clean),
                Instituicao.sigla.ilike(busca_clean),
                Instituicao.descricao.ilike(busca_clean)
            )
        )

    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(asc(Instituicao.nome)).offset(offset).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

def get_instituicao_by_id(db: Session, instituicao_id: int):
    """Retorna detalhes completos de uma instituição com órgãos superiores, subordinados, vinculados e relações."""
    inst = db.query(Instituicao).filter(Instituicao.id == instituicao_id).first()
    if not inst:
        return None

    # Órgãos superiores (onde esta instituição é origem com HIERARQUIA ou COMPOSICAO)
    rels_origem = db.query(RelacaoInstitucional).filter(RelacaoInstitucional.instituicao_origem_id == inst.id).all()
    superiores = []
    for r in rels_origem:
        if r.tipo_relacao in ["HIERARQUIA_ADMINISTRATIVA", "COMPOSICAO"]:
            dest = db.query(Instituicao).filter(Instituicao.id == r.instituicao_destino_id).first()
            if dest and dest not in superiores:
                superiores.append(dest)

    # Órgãos subordinados e vinculados (onde esta instituição é destino)
    rels_destino = db.query(RelacaoInstitucional).filter(RelacaoInstitucional.instituicao_destino_id == inst.id).all()
    subordinados = []
    vinculados = []
    for r in rels_destino:
        orig = db.query(Instituicao).filter(Instituicao.id == r.instituicao_origem_id).first()
        if not orig:
            continue
        if r.tipo_relacao == "HIERARQUIA_ADMINISTRATIVA":
            subordinados.append(orig)
        elif r.tipo_relacao == "VINCULACAO":
            vinculados.append(orig)

    # Lista consolidada de todas as relações
    relacoes_items = []
    all_rels = list(rels_origem) + list(rels_destino)
    for r in all_rels:
        orig = db.query(Instituicao).filter(Instituicao.id == r.instituicao_origem_id).first()
        dest = db.query(Instituicao).filter(Instituicao.id == r.instituicao_destino_id).first()
        if orig and dest:
            relacoes_items.append({
                "id": r.id,
                "origem_id": orig.id,
                "origem_nome": orig.nome,
                "origem_sigla": orig.sigla,
                "origem_tipo": orig.tipo,
                "destino_id": dest.id,
                "destino_nome": dest.nome,
                "destino_sigla": dest.sigla,
                "destino_tipo": dest.tipo,
                "tipo_relacao": r.tipo_relacao,
                "descricao": r.descricao,
                "fonte": r.fonte
            })

    # Verifica se é a Câmara dos Deputados para injetar métricas ao vivo
    is_camara = (inst.codigo_externo == "CAMARA_DEPUTADOS" or inst.sigla == "CD")
    stats_camara = None
    if is_camara:
        stats_camara = {
            "total_deputados": db.query(func.count(Deputado.id)).scalar() or 0,
            "total_proposicoes": db.query(func.count(Proposicao.id)).scalar() or 0,
            "total_votacoes": db.query(func.count(Votacao.id)).scalar() or 0,
            "total_legislaturas": db.query(func.count(Legislatura.id)).scalar() or 0,
            "links": [
                {"label": "Consultar Deputados Federais", "url": "/deputados"},
                {"label": "Acompanhar Proposições", "url": "/proposicoes"},
                {"label": "Histórico de Votações", "url": "/votacoes"}
            ]
        }

    return {
        "id": inst.id,
        "nome": inst.nome,
        "sigla": inst.sigla,
        "tipo": inst.tipo,
        "poder": inst.poder,
        "esfera": inst.esfera,
        "nivel_federativo": inst.nivel_federativo,
        "codigo_externo": inst.codigo_externo,
        "natureza_juridica": inst.natureza_juridica,
        "descricao": inst.descricao,
        "site_oficial": inst.site_oficial,
        "fonte": inst.fonte,
        "url_fonte": inst.url_fonte,
        "ativo": inst.ativo,
        "superiores": superiores,
        "subordinados": subordinados,
        "vinculados": vinculados,
        "relacoes": relacoes_items,
        "integrado": is_camara,
        "estatisticas_camara": stats_camara
    }

def search_instituicoes(db: Session, query: str):
    """Busca rápida de instituições para autocomplete ou busca direta no mapa do governo."""
    q_clean = query.strip()
    if not q_clean:
        return []

    return (
        db.query(Instituicao)
        .filter(
            Instituicao.ativo == True,
            or_(
                Instituicao.nome.ilike(f"%{q_clean}%"),
                Instituicao.sigla.ilike(f"%{q_clean}%")
            )
        )
        .order_by(asc(Instituicao.nome))
        .limit(15)
        .all()
    )

