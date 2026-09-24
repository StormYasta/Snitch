from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    PageResponse, DeputadoSimple, DeputadoDetail, DeputadoGabinete,
    DeputadoAtividade, AtividadeTemporalItem, DistribuicaoVotosItem,
    DeputadoVotoItem, ProposicaoSimple, DeputadoHistoricoItem, DeputadoTrajetoriaResponse
)
from app import crud

router = APIRouter(prefix="/api/deputados", tags=["Deputados"])

@router.get("", response_model=PageResponse[DeputadoSimple])
def list_deputados(
    busca: Optional[str] = Query(None, description="Busca textual por nome ou partido"),
    partido: Optional[str] = Query(None, description="Sigla do partido (ex: PT, PL)"),
    uf: Optional[str] = Query(None, description="Sigla da UF (ex: SP, RJ)"),
    situacao: Optional[str] = Query(None, description="Situação do mandato (ex: Exercício)"),
    legislatura: Optional[int] = Query(None, description="Número da legislatura (ex: 57)"),
    ordenar_por: str = Query("nome", description="Ordenação objetiva: 'nome'"),
    ordem: str = Query("asc", description="'asc' ou 'desc'"),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return crud.get_deputados(
        db, busca=busca, partido=partido, uf=uf, situacao=situacao,
        legislatura=legislatura, ordenar_por=ordenar_por, ordem=ordem,
        page=page, page_size=page_size
    )

@router.get("/{id}", response_model=DeputadoDetail)
def get_deputado_detail(id: int, db: Session = Depends(get_db)):
    dep = crud.get_deputado_by_id(db, id)
    if not dep:
        raise HTTPException(status_code=404, detail="Deputado não encontrado")

    gabinete = DeputadoGabinete(
        predio=dep.gabinete_predio,
        sala=dep.gabinete_sala,
        andar=dep.gabinete_andar,
        telefone=dep.gabinete_telefone
    )

    rede_social_list = dep.rede_social if isinstance(dep.rede_social, list) else []

    return DeputadoDetail(
        id=dep.id,
        camara_id=dep.camara_id,
        nome_parlamentar=dep.nome_parlamentar,
        nome_civil=dep.nome_civil,
        sigla_partido=dep.sigla_partido,
        uf=dep.uf,
        url_foto=dep.url_foto,
        situacao=dep.situacao,
        condicao_eleitoral=dep.condicao_eleitoral,
        descricao_status=dep.descricao_status,
        email=dep.email,
        legislatura=dep.legislatura,
        gabinete=gabinete,
        data_nascimento=dep.data_nascimento,
        municipio_nascimento=dep.municipio_nascimento,
        uf_nascimento=dep.uf_nascimento,
        escolaridade=dep.escolaridade,
        rede_social=rede_social_list,
        url_website=dep.url_website,
        uri=dep.uri,
        updated_at=dep.updated_at
    )

@router.get("/{id}/atividade", response_model=DeputadoAtividade)
def get_deputado_atividade(id: int, db: Session = Depends(get_db)):
    dep = crud.get_deputado_by_id(db, id)
    if not dep:
        raise HTTPException(status_code=404, detail="Deputado não encontrado")
    return crud.get_deputado_atividade(db, id)

@router.get("/{id}/temporal", response_model=list[AtividadeTemporalItem])
def get_deputado_temporal(
    id: int,
    agrupamento: str = Query("mes", regex="^(mes|ano)$"),
    legislatura: Optional[int] = Query(None, description="Filtrar por número de legislatura"),
    ano: Optional[int] = Query(None, description="Filtrar por ano específico"),
    db: Session = Depends(get_db)
):
    dep = crud.get_deputado_by_id(db, id)
    if not dep:
        raise HTTPException(status_code=404, detail="Deputado não encontrado")
    return crud.get_deputado_temporal(db, id, agrupamento=agrupamento, legislatura=legislatura, ano=ano)

@router.get("/{id}/trajetoria", response_model=DeputadoTrajetoriaResponse)
def get_deputado_trajetoria(id: int, db: Session = Depends(get_db)):
    trajetoria = crud.get_deputado_trajetoria(db, id)
    if not trajetoria:
        raise HTTPException(status_code=404, detail="Deputado não encontrado")
    return trajetoria

@router.get("/{id}/distribuicao_votos", response_model=list[DistribuicaoVotosItem])
def get_deputado_distribuicao_votos(id: int, db: Session = Depends(get_db)):
    dep = crud.get_deputado_by_id(db, id)
    if not dep:
        raise HTTPException(status_code=404, detail="Deputado não encontrado")
    return crud.get_deputado_distribuicao_votos(db, id)

@router.get("/{id}/votos", response_model=PageResponse[DeputadoVotoItem])
def get_deputado_votos(
    id: int,
    tipo_voto: Optional[str] = Query(None, description="Filtro de voto (Sim, Não, etc)"),
    tipo_proposicao: Optional[str] = Query(None, description="Tipo da proposição (PL, PEC)"),
    ano: Optional[int] = Query(None, description="Ano da votação"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    dep = crud.get_deputado_by_id(db, id)
    if not dep:
        raise HTTPException(status_code=404, detail="Deputado não encontrado")
    return crud.get_deputado_votos(
        db, id, tipo_voto=tipo_voto, tipo_proposicao=tipo_proposicao,
        ano=ano, page=page, page_size=page_size
    )

@router.get("/{id}/proposicoes", response_model=PageResponse[ProposicaoSimple])
def get_deputado_proposicoes(
    id: int,
    relacao: str = Query("autoria", regex="^(autoria|votacao)$", description="'autoria' ou 'votacao'"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    dep = crud.get_deputado_by_id(db, id)
    if not dep:
        raise HTTPException(status_code=404, detail="Deputado não encontrado")
    return crud.get_deputado_proposicoes(db, id, relacao=relacao, page=page, page_size=page_size)

@router.get("/{id}/eventos")
def get_deputado_eventos(id: int, db: Session = Depends(get_db)):
    dep = crud.get_deputado_by_id(db, id)
    if not dep:
        raise HTTPException(status_code=404, detail="Deputado não encontrado")
    eventos = crud.get_deputado_eventos(db, id)
    return [
        {
            "id": e.id,
            "camara_id": e.camara_id,
            "data_inicio": e.data_inicio,
            "data_fim": e.data_fim,
            "tipo": e.tipo,
            "descricao": e.descricao,
            "situacao": e.situacao,
            "local": e.local,
            "uri": e.uri
        }
        for e in eventos
    ]

@router.get("/{id}/historico", response_model=list[DeputadoHistoricoItem])
def get_deputado_historico(id: int, db: Session = Depends(get_db)):
    dep = crud.get_deputado_by_id(db, id)
    if not dep:
        raise HTTPException(status_code=404, detail="Deputado não encontrado")
    return crud.get_deputado_historico(db, id)
