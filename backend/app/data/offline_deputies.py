import json
import logging
from pathlib import Path
from sqlalchemy.orm import Session

from app.services.camara.deputados_service import DeputadosService

logger = logging.getLogger(__name__)
SNAPSHOT_PATH = Path(__file__).with_name("deputados_offline_100.json")


def load_offline_deputies(db: Session, path: Path = SNAPSHOT_PATH) -> int:
    """Carrega um snapshot oficial de 100 deputados sem acessar a internet."""
    if not path.exists():
        raise RuntimeError(
            "Snapshot offline não encontrado. Atualize a branch para obter "
            "backend/app/data/deputados_offline_100.json."
        )

    payload = json.loads(path.read_text(encoding="utf-8"))
    meta = payload.get("_meta") or {}
    rows = payload.get("dados") or []

    if len(rows) != 100:
        raise RuntimeError(
            f"Snapshot inválido: esperado 100 deputados, encontrado {len(rows)}."
        )

    unique_ids = {row.get("id") for row in rows}
    if None in unique_ids or len(unique_ids) != 100:
        raise RuntimeError("Snapshot inválido: IDs oficiais ausentes ou duplicados.")

    service = DeputadosService()
    count = 0
    for raw in rows:
        dep = service.upsert_deputado(db, raw)
        raw_saved = dict(dep.dados_raw or {})
        raw_saved["_snitch_snapshot"] = {
            "source": meta.get("source"),
            "retrieved_at": meta.get("retrieved_at"),
            "selection": meta.get("selection"),
            "legislatura": meta.get("legislatura"),
        }
        dep.dados_raw = raw_saved
        count += 1

    db.commit()
    logger.info(
        "Snapshot oficial offline carregado: %s deputados; acesso da fonte em %s.",
        count,
        meta.get("retrieved_at") or "data não informada",
    )
    return count
