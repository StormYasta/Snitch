from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    PageResponse, ProposicaoSimple, ProposicaoDetail,
    AutorItem, TramitacaoItem, VotacaoResumoItem
)
from app import crud

router = APIRouter(prefix="/api/proposicoes", tags=["Proposições"])

@router.get("", response_model=PageResponse[ProposicaoSimple])
def list_proposicoes(
    busca: Optional[str] = Query(None, description="Busca textual na ementa ou por sigla e número (ex: PL 1234/2025)"),
    tipo: Optional[str] = Query(None, description="Tipo da proposição (PL, PEC, MPV, etc)"),
    ano: Optional[int] = Query(None, description="Ano de apresentação"),
    situacao: Optional[str] = Query(None, description="Situação da tramitação"),
    tema: Optional[str] = Query(None, description="Tema da proposição"),
    autor: Optional[str] = Query(None, description="Nome do autor"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return crud.get_proposicoes(
        db, busca=busca, tipo=tipo, ano=ano, situacao=situacao,
        tema=tema, autor=autor, page=page, page_size=page_size
    )

@router.get("/{id}", response_model=ProposicaoDetail)
def get_proposicao_detail(id: int, db: Session = Depends(get_db)):
    prop = crud.get_proposicao_by_id(db, id)
    if not prop:
        raise HTTPException(status_code=404, detail="Proposição não encontrada")

    temas = [pt.tema.nome for pt in prop.temas if pt.tema]

    autores = []
    for a in prop.autores:
        autores.append(AutorItem(
            id=a.id,
            nome_autor=a.nome_autor,
            tipo_autor=a.tipo_autor,
            ordem_autoria=a.ordem_autoria,
            proponente=a.proponente,
            deputado_id=a.deputado_id,
            sigla_partido=a.deputado.sigla_partido if a.deputado else None,
            uf=a.deputado.uf if a.deputado else None,
            url_foto=a.deputado.url_foto if a.deputado else None
        ))

    tramitacoes = []
    for tr in prop.tramitacoes:
        tramitacoes.append(TramitacaoItem(
            id=tr.id,
            data_hora=tr.data_hora,
            sequencia=tr.sequencia,
            descricao_tramitacao=tr.descricao_tramitacao,
            despacho=tr.despacho,
            orgao=tr.orgao,
            situacao=tr.situacao,
            regime=tr.regime,
            url_documento=tr.url_documento
        ))

    votacoes = []
    for vp in prop.votacoes_relacionadas:
        v = vp.votacao
        votacoes.append(VotacaoResumoItem(
            id=v.id,
            camara_id=v.camara_id,
            data_hora_registro=v.data_hora_registro,
            descricao=v.descricao,
            resultado=v.resultado,
            aprovada=v.aprovada,
            orgao=v.orgao,
            placar_sim=v.placar_sim,
            placar_nao=v.placar_nao,
            placar_abstencao=v.placar_abstencao,
            placar_obstrucao=v.placar_obstrucao,
            tipo_relacao=vp.tipo_relacao or "Votação relacionada à proposição"
        ))

    return ProposicaoDetail(
        id=prop.id,
        camara_id=prop.camara_id,
        sigla_tipo=prop.sigla_tipo,
        numero=prop.numero,
        ano=prop.ano,
        ementa=prop.ementa,
        ementa_detalhada=prop.ementa_detalhada,
        data_apresentacao=prop.data_apresentacao,
        situacao=prop.situacao,
        descricao_situacao=prop.descricao_situacao,
        regime=prop.regime,
        despacho=prop.despacho,
        orgao_atual=prop.orgao_atual,
        url_inteiro_teor=prop.url_inteiro_teor,
        uri=prop.uri,
        updated_at=prop.updated_at,
        temas=temas,
        autores=autores,
        tramitacoes=tramitacoes,
        votacoes=votacoes
    )

@router.get("/{id}/tramitacoes", response_model=list[TramitacaoItem])
def get_proposicao_tramitacoes(id: int, db: Session = Depends(get_db)):
    prop = crud.get_proposicao_by_id(db, id)
    if not prop:
        raise HTTPException(status_code=404, detail="Proposição não encontrada")
    return [
        TramitacaoItem(
            id=tr.id,
            data_hora=tr.data_hora,
            sequencia=tr.sequencia,
            descricao_tramitacao=tr.descricao_tramitacao,
            despacho=tr.despacho,
            orgao=tr.orgao,
            situacao=tr.situacao,
            regime=tr.regime,
            url_documento=tr.url_documento
        )
        for tr in prop.tramitacoes
    ]

@router.get("/{id}/votacoes", response_model=list[VotacaoResumoItem])
def get_proposicao_votacoes(id: int, db: Session = Depends(get_db)):
    prop = crud.get_proposicao_by_id(db, id)
    if not prop:
        raise HTTPException(status_code=404, detail="Proposição não encontrada")
    return [
        VotacaoResumoItem(
            id=vp.votacao.id,
            camara_id=vp.votacao.camara_id,
            data_hora_registro=vp.votacao.data_hora_registro,
            descricao=vp.votacao.descricao,
            resultado=vp.votacao.resultado,
            aprovada=vp.votacao.aprovada,
            orgao=vp.votacao.orgao,
            placar_sim=vp.votacao.placar_sim,
            placar_nao=vp.votacao.placar_nao,
            placar_abstencao=vp.votacao.placar_abstencao,
            placar_obstrucao=vp.votacao.placar_obstrucao,
            tipo_relacao=vp.tipo_relacao or "Votação relacionada à proposição"
        )
        for vp in prop.votacoes_relacionadas
    ]
