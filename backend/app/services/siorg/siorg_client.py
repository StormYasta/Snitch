import json
import logging
import os
from pathlib import Path
from typing import Optional, Any
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent.parent / "data"
CACHE_FILE = CACHE_DIR / "siorg_cache.json"

class SiorgClientError(Exception):
    pass

class SiorgClient:
    """Cliente oficial para consumo do SIORG (Sistema de Organização e Inovação Institucional do Governo Federal).
    Fonte oficial: dados.gov.br / estruturaorganizacional.dados.gov.br
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        self.base_url = base_url or settings.siorg_api_url
        self.timeout = timeout or settings.siorg_timeout

    def _load_cache(self) -> Optional[list[dict[str, Any]]]:
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Erro ao ler cache do SIORG: {e}")
        return None

    def _save_cache(self, data: list[dict[str, Any]]):
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            logger.info(f"Cache do SIORG salvo em {CACHE_FILE} ({len(data)} unidades).")
        except Exception as e:
            logger.warning(f"Erro ao salvar cache do SIORG: {e}")

    def fetch_unidades(self, force_refresh: bool = False) -> list[dict[str, Any]]:
        """Busca todas as unidades organizacionais do SIORG, utilizando cache se disponível."""
        if not force_refresh:
            cached = self._load_cache()
            if cached:
                logger.info(f"SIORG carregado do cache local ({len(cached)} unidades).")
                return cached

        logger.info(f"Consultando SIORG via API oficial: {self.base_url}...")
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    self.base_url,
                    headers={"Accept": "application/json", "User-Agent": "Snitch-Observatorio/1.0"}
                )
                response.raise_for_status()

                # SIORG dados.gov.br costuma vir codificado em ISO-8859-1 / Latin-1
                try:
                    payload = json.loads(response.content.decode("iso-8859-1"))
                except Exception:
                    payload = response.json()

                unidades = payload.get("unidades", [])
                if unidades:
                    self._save_cache(unidades)
                    return unidades
        except Exception as e:
            logger.warning(f"Falha ao consultar API online do SIORG: {e}. Tentando fallback em cache...")
            cached = self._load_cache()
            if cached:
                return cached
            logger.error("Nenhum dado do SIORG disponível (nem online, nem cache).")

        return []
