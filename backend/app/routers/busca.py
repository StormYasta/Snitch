from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import GlobalSearchResult
from app import crud

router = APIRouter(prefix="/api/busca", tags=["Busca Global"])

@router.get("", response_model=GlobalSearchResult)
def search_global(
    q: str = Query(..., min_length=1, description="Termo de busca (ex: 'PL 1234/2025' ou 'Tabata')"),
    db: Session = Depends(get_db)
):
    return crud.global_search(db, q)
