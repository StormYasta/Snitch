from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    PageResponse, VotacaoDetail, VotoDeputadoItem,
    OrientacaoItem, ProposicaoSimple
)
from app import crud

router = APIRouter(prefix="/api/votacoes", tags=["Votações"])

@router.get("/{id}", response_model=VotacaoDetail)
def get_votacao_detail(id: int, db: Session = Depends(get_db)):
    vot = crud.get_votacao_by_id(db, id)
    if not vot:
        raise HTTPException(status_code=404, detail="Votação não encontrada")

    orientacoes = [
        OrientacaoItem(id=o.id, bancada=o.bancada, orientacao_voto=o.orientacao_voto)
        for o in vot.orientacoes
    ]

    proposicoes = []
    for vp in vot.proposicoes_relacionadas:
        p = vp.proposicao
        temas = [pt.tema.nome for pt in p.temas if pt.tema]
        autor_p = p.autores[0].nome_autor if p.autores else None
        dep_id = p.autores[0].deputado_id if p.autores else None
        proposicoes.append(ProposicaoSimple(
            id=p.id,
            camara_id=p.camara_id,
            sigla_tipo=p.sigla_tipo,
            numero=p.numero,
            ano=p.ano,
            ementa=p.ementa,
            data_apresentacao=p.data_apresentacao,
            situacao=p.situacao,
            descricao_situacao=p.descricao_situacao,
            orgao_atual=p.orgao_atual,
            temas=temas,
            autor_principal=autor_p,
            autor_principal_deputado_id=dep_id
        ))

    return VotacaoDetail(
        id=vot.id,
        camara_id=vot.camara_id,
        data_hora_registro=vot.data_hora_registro,
        descricao=vot.descricao,
        resultado=vot.resultado,
        aprovada=vot.aprovada,
        orgao=vot.orgao,
        placar_sim=vot.placar_sim,
        placar_nao=vot.placar_nao,
        placar_abstencao=vot.placar_abstencao,
        placar_obstrucao=vot.placar_obstrucao,
        uri=vot.uri,
        orientacoes=orientacoes,
        proposicoes=proposicoes,
        total_votos=len(vot.votos)
    )

@router.get("/{id}/votos", response_model=PageResponse[VotoDeputadoItem])
def get_votacao_votos(
    id: int,
    voto: Optional[str] = Query(None, description="Filtro de voto (Sim, Não, etc)"),
    partido: Optional[str] = Query(None, description="Sigla do Partido"),
    uf: Optional[str] = Query(None, description="UF do Deputado"),
    busca: Optional[str] = Query(None, description="Busca por nome de deputado"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    vot = crud.get_votacao_by_id(db, id)
    if not vot:
        raise HTTPException(status_code=404, detail="Votação não encontrada")

    return crud.get_votos_by_votacao(
        db, id, tipo_voto=voto, partido=partido, uf=uf,
        busca=busca, page=page, page_size=page_size
    )
