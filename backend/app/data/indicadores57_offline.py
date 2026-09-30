"""Leitura do snapshot oficial offline de indicadores da 57ª Legislatura."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

SNAPSHOT_PATH = Path(__file__).with_name("indicadores57_offline.json")


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    if not SNAPSHOT_PATH.exists():
        return {}
    try:
        return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def get_offline_indicators(camara_id: int, ano: int, mes: int) -> dict[str, Any]:
    data = _load()
    result: dict[str, Any] = {
        "ano": None,
        "mes": None,
        "votacoes_amostra": None,
        "retrieved_at": (data.get("_meta") or {}).get("retrieved_at"),
    }

    year_data = ((data.get("anos") or {}).get(str(ano)) or {}).get("deputados") or {}
    if str(camara_id) in year_data:
        result["ano"] = year_data[str(camara_id)]

    month_key = f"{ano:04d}-{mes:02d}"
    month_data = ((data.get("meses") or {}).get(month_key) or {}).get("deputados") or {}
    if str(camara_id) in month_data:
        result["mes"] = month_data[str(camara_id)]
        result["mes_retrieved_at"] = ((data.get("meses") or {}).get(month_key) or {}).get("retrieved_at")

    votes = ((data.get("votacoes_amostra") or {}).get(str(ano)) or {})
    if str(camara_id) in votes:
        result["votacoes_amostra"] = int(votes[str(camara_id)])

    return result


def clear_offline_cache() -> None:
    _load.cache_clear()
