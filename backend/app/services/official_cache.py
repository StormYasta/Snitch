"""Cache em Postgres dos agregados pontuais consultados nas fontes oficiais."""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Generic, TypeVar

from sqlalchemy.orm import Session
from app.models import OfficialCache

logger = logging.getLogger(__name__)
T = TypeVar("T")


def _aware(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


@dataclass
class CachedResult(Generic[T]):
    value: T
    status: str  # atualizado | cache | desatualizado | indisponivel
    source_url: str
    fetched_at: datetime | None = None
    expires_at: datetime | None = None

    def metadata(self) -> dict:
        return {
            "status": self.status,
            "fonte": self.source_url,
            "consultado_em": self.fetched_at,
            "expira_em": self.expires_at,
        }


def cached_official(
    db: Session,
    key: str,
    source: str,
    url: str,
    ttl_hours: int,
    loader: Callable[[], T],
    usable: Callable[[T], bool],
) -> CachedResult[T | None]:
    now = datetime.now(timezone.utc)
    saved = db.get(OfficialCache, key)

    if saved is not None and _aware(saved.expires_at) > now:
        return CachedResult(saved.payload, "cache", saved.source_url,
                            _aware(saved.fetched_at), _aware(saved.expires_at))
    try:
        value = loader()
        if usable(value):
            expires_at = now + timedelta(hours=ttl_hours)
            if saved is None:
                saved = OfficialCache(cache_key=key, source=source, source_url=url)
                db.add(saved)
            saved.source_url = url
            saved.payload = value
            saved.fetched_at = now
            saved.expires_at = expires_at
            try:
                db.commit()
            except Exception:
                db.rollback()
                logger.exception("Erro ao persistir cache oficial: %s", key)
            return CachedResult(value, "atualizado", url, now, expires_at)
    except Exception:
        logger.exception("Fonte externa indisponível: %s", key)
    if saved is not None and saved.payload is not None:
        # Última leitura válida: mostrar a data real e sinalizar dado antigo.
        return CachedResult(saved.payload, "desatualizado", saved.source_url,
                            _aware(saved.fetched_at), _aware(saved.expires_at))
    return CachedResult(None, "indisponivel", url)
