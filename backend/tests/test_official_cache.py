from datetime import datetime, timedelta, timezone
from app.database import Base, SessionLocal, engine
from app.models import OfficialCache
from app.services.official_cache import cached_official


def test_cache_avoids_second_network_request():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        key = "test:cache:sample"
        db.query(OfficialCache).filter_by(cache_key=key).delete()
        db.commit()
        invoked = []
        def loader():
            invoked.append(1)
            return {"valor": 30.5}
        first = cached_official(db, key, "despesas", "https://example.gov", 24, loader, bool)
        second = cached_official(db, key, "despesas", "https://example.gov", 24, loader, bool)
        assert first.status == "atualizado"
        assert second.status == "cache"
        assert second.value["valor"] == 30.5
        assert len(invoked) == 1
        db.query(OfficialCache).filter_by(cache_key=key).delete()
        db.commit()


def test_stale_cache_survives_unavailable_source():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        key = "test:cache:stale"
        db.query(OfficialCache).filter_by(cache_key=key).delete()
        db.commit()
        cached_official(db, key, "presencas", "https://example.gov", 6,
                        lambda: {"presencas": 12}, lambda x: x is not None)
        saved = db.get(OfficialCache, key)
        saved.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()
        stale = cached_official(db, key, "presencas", "https://example.gov", 6,
                                lambda: None, lambda x: x is not None)
        assert stale.status == "desatualizado"
        assert stale.value == {"presencas": 12}
        db.query(OfficialCache).filter_by(cache_key=key).delete()
        db.commit()
