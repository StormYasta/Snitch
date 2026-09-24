from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    PageResponse, InstituicaoSimple, InstituicaoDetail,
    EstruturaGovernoGraph, LegislaturaItem
)
from app import crud

router = APIRouter(tags=["Governo"])

@router.get("/api/governo/estrutura", response_model=EstruturaGovernoGraph)
def get_estrutura_governo(db: Session = Depends(get_db)):
    """Retorna o grafo completo da estrutura institucional canônica do Estado brasileiro."""
    return crud.get_estrutura_governo(db)

@router.get("/api/governo/instituicoes", response_model=PageResponse[InstituicaoSimple])
def list_instituicoes(
    esfera: Optional[str] = Query(None, description="Esfera: Federal, Estadual, Distrital, Municipal"),
    poder: Optional[str] = Query(None, description="Poder: Executivo, Legislativo, Judiciário, Instituição Autônoma / Controle"),
    tipo: Optional[str] = Query(None, description="Tipo: PODER, MINISTERIO, SECRETARIA, AUTARQUIA, FUNDACAO, CASA_LEGISLATIVA, TRIBUNAL"),
    nivel_federativo: Optional[str] = Query(None, description="Nível federativo: União, Estados, Distrito Federal, Municípios"),
    busca: Optional[str] = Query(None, description="Busca textual por nome ou sigla"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Consulta pública e paginada de instituições dos Três Poderes e níveis federativos."""
    return crud.get_instituicoes(
        db, esfera=esfera, poder=poder, tipo=tipo,
        nivel_federativo=nivel_federativo, busca=busca,
        page=page, page_size=page_size
    )

@router.get("/api/governo/busca", response_model=list[InstituicaoSimple])
def search_instituicoes(
    q: str = Query(..., min_length=1, description="Termo para busca rápida de órgãos e instituições"),
    db: Session = Depends(get_db)
):
    """Busca rápida de instituições públicas por nome ou sigla."""
    return crud.search_instituicoes(db, query=q)

@router.get("/api/governo/instituicoes/{id}", response_model=InstituicaoDetail)
def get_instituicao_detail(id: int, db: Session = Depends(get_db)):
    """Retorna detalhes da instituição com seus superiores, subordinados, vinculados e relações."""
    inst = crud.get_instituicao_by_id(db, id)
    if not inst:
        raise HTTPException(status_code=404, detail="Instituição não encontrada")
    return inst

@router.get("/api/legislaturas", response_model=list[LegislaturaItem])
def list_legislaturas(db: Session = Depends(get_db)):
    """Retorna a lista de legislaturas da Câmara dos Deputados cadastradas no sistema."""
    return crud.get_legislaturas(db)
