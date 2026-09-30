"""Endpoints para comparação factual, sem ordenação avaliativa."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ComparativoResponse, PageResponse, VotacaoComparada
from app.services.comparativo_service import (
    obter_comparativo, obter_votacoes_comuns, validar_ids,
)

router = APIRouter(prefix="/api/comparativo", tags=["Comparativo"])


@router.get("/deputados", response_model=ComparativoResponse)
def comparar_deputados(
    ids: str = Query(..., description="2 ou 3 IDs distintos, separados por vírgula"),
    ano: int = Query(default=date.today().year, ge=2008, le=2100),
    legislatura: Optional[int] = Query(default=None, ge=1),
    db: Session = Depends(get_db),
):
    return obter_comparativo(db, validar_ids(ids), ano, legislatura)


@router.get("/votacoes", response_model=PageResponse[VotacaoComparada])
def comparar_votacoes(
    ids: str = Query(..., description="2 ou 3 IDs distintos, separados por vírgula"),
    ano: int = Query(default=date.today().year, ge=2008, le=2100),
    legislatura: Optional[int] = Query(default=None, ge=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=15, ge=1, le=50),
    db: Session = Depends(get_db),
):
    return obter_votacoes_comuns(
        db, validar_ids(ids), ano, legislatura, page, page_size
    )
