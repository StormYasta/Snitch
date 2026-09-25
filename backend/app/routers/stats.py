import secrets
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Header
from app.config import settings
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.schemas import StatsResponse, SyncStatusResponse
from app.models import SyncRun
from app import crud
from app.sync import run_sync

router = APIRouter(prefix="/api", tags=["Estatísticas e Sincronização"])

@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    return crud.get_platform_stats(db)

@router.get("/sync/status", response_model=SyncStatusResponse)
def get_sync_status(db: Session = Depends(get_db)):
    last_run = db.query(SyncRun).order_by(desc(SyncRun.iniciado_em)).first()
    if not last_run:
        return SyncStatusResponse(
            status="NEVER_RUN",
            registros_processados=0
        )

    return SyncStatusResponse(
        id=last_run.id,
        tipo=last_run.tipo,
        iniciado_em=last_run.iniciado_em,
        finalizado_em=last_run.finalizado_em,
        status=last_run.status,
        registros_processados=last_run.registros_processados,
        erro=last_run.erro
    )

@router.post("/sync/trigger")
def trigger_sync(
    background_tasks: BackgroundTasks,
    tipo: str = "deputados",
    x_snitch_sync_token: str | None = Header(default=None),
):
    if not settings.sync_admin_token or not secrets.compare_digest(
        x_snitch_sync_token or "", settings.sync_admin_token
    ):
        raise HTTPException(status_code=403, detail="Operação administrativa não autorizada.")
    allowed = {
        "deputados", "proposicoes", "votacoes", "eventos", "historico",
        "legislaturas", "deputados_historicos", "enriquecer_deputados",
        "estrutura_governo", "siorg", "mvp2",
    }
    if tipo not in allowed:
        raise HTTPException(status_code=422, detail="Tipo de sincronização não autorizado.")
    background_tasks.add_task(run_sync, tipo)
    return {"message": f"Sincronização '{tipo}' iniciada em segundo plano."}
