"""Rastreabilidade de acessos efetivos e importações concluídas."""
from fastapi import APIRouter, Depends
from sqlalchemy import func, desc
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import OfficialCache, SyncRun

router = APIRouter(prefix="/api/fontes", tags=["Fontes oficiais"])


@router.get("/status")
def get_status(db: Session = Depends(get_db)):
    cache = [
        {
            "fonte": item.source,
            "ultimo_acesso": item.ultimo_acesso,
            "registros_em_cache": item.registros,
        }
        for item in (
            db.query(
                OfficialCache.source,
                func.max(OfficialCache.fetched_at).label("ultimo_acesso"),
                func.count(OfficialCache.cache_key).label("registros"),
            )
            .group_by(OfficialCache.source)
            .all()
        )
    ]
    latest = {}
    for record in (
        db.query(SyncRun)
        .order_by(desc(SyncRun.iniciado_em))
        .limit(200)
        .all()
    ):
        if record.tipo not in latest:
            latest[record.tipo] = {
                "tipo": record.tipo,
                "status": record.status,
                "finalizado_em": record.finalizado_em,
                "registros_processados": record.registros_processados,
            }
    return {"cache": cache, "sincronizacoes": list(latest.values())}
