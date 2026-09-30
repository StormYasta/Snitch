import json
import logging
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
    """Cliente de leitura do SIORG.

    A API oficial expõe a estrutura organizacional do Poder Executivo Federal.
    O cliente normaliza variações de caixa/nome de chaves e mantém cache local
    para permitir inicialização degradada quando o serviço estiver indisponível.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = base_url or settings.siorg_api_url
        self.timeout = timeout or settings.siorg_timeout

    def _load_cache(self) -> Optional[list[dict[str, Any]]]:
        if not CACHE_FILE.exists():
            return None
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                payload = json.load(f)
                return payload if isinstance(payload, list) else None
        except Exception as exc:
            logger.warning("Erro ao ler cache do SIORG: %s", exc)
            return None

    def _save_cache(self, data: list[dict[str, Any]]) -> None:
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            logger.info("Cache do SIORG salvo em %s (%s unidades).", CACHE_FILE, len(data))
        except Exception as exc:
            logger.warning("Erro ao salvar cache do SIORG: %s", exc)

    @staticmethod
    def _value(raw: dict[str, Any], *keys: str) -> Any:
        lower_map = {str(k).lower(): v for k, v in raw.items()}
        for key in keys:
            if key in raw:
                return raw[key]
            value = lower_map.get(key.lower())
            if value is not None:
                return value
        return None

    def _normalize_unit(self, raw: dict[str, Any]) -> dict[str, Any]:
        return {
            "codigoUnidade": self._value(raw, "CodigoUnidade", "codigoUnidade"),
            "codigoUnidadePai": self._value(raw, "CodigoUnidadePai", "codigoUnidadePai"),
            "codigoOrgaoEntidade": self._value(raw, "CodigoOrgaoEntidade", "codigoOrgaoEntidade"),
            "codigoTipoUnidade": self._value(raw, "CodigoTipoUnidade", "codigoTipoUnidade"),
            "codigoEsfera": self._value(raw, "CodigoEsfera", "codigoEsfera"),
            "codigoPoder": self._value(raw, "CodigoPoder", "codigoPoder"),
            "codigoNaturezaJuridica": self._value(
                raw, "CodigoNaturezaJuridica", "codigoNaturezaJuridica"
            ),
            "nome": self._value(raw, "Nome", "nome"),
            "sigla": self._value(raw, "Sigla", "sigla"),
            "competencia": self._value(raw, "Competencia", "competencia"),
            "finalidade": self._value(raw, "Finalidade", "finalidade"),
            "missao": self._value(raw, "Missao", "missao"),
            "versaoConsulta": self._value(raw, "VersaoConsulta", "versaoConsulta"),
            "dataInicialVersaoConsulta": self._value(
                raw, "DataInicialVersaoConsulta", "dataInicialVersaoConsulta"
            ),
            "dataFinalVersaoConsulta": self._value(
                raw, "DataFinalVersaoConsulta", "dataFinalVersaoConsulta"
            ),
            "_raw": raw,
        }

    def _extract_units(self, payload: Any) -> list[dict[str, Any]]:
        """Localiza registros de unidade mesmo quando o envelope JSON varia."""
        found: dict[str, dict[str, Any]] = {}

        def walk(value: Any) -> None:
            if isinstance(value, dict):
                code = self._value(value, "CodigoUnidade", "codigoUnidade")
                name = self._value(value, "Nome", "nome")
                if code is not None and name:
                    normalized = self._normalize_unit(value)
                    found[str(code)] = normalized
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(payload)
        return list(found.values())

    def fetch_unidades(self, force_refresh: bool = False) -> list[dict[str, Any]]:
        """Busca a estrutura organizacional federal no SIORG e devolve unidades normalizadas."""
        if not force_refresh:
            cached = self._load_cache()
            if cached:
                logger.info("SIORG carregado do cache local (%s unidades).", len(cached))
                return cached

        logger.info("Consultando SIORG via endpoint oficial: %s", self.base_url)
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(
                    self.base_url,
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "Snitch-Observatorio/1.0",
                    },
                )
                response.raise_for_status()

                try:
                    payload = response.json()
                except Exception:
                    decoded = response.content.decode(response.encoding or "utf-8", errors="replace")
                    payload = json.loads(decoded)

                unidades = self._extract_units(payload)
                if unidades:
                    self._save_cache(unidades)
                    return unidades

                raise SiorgClientError("Resposta do SIORG não contém unidades reconhecíveis.")
        except Exception as exc:
            logger.warning("Falha ao consultar o SIORG (%s). Tentando cache local.", exc)
            cached = self._load_cache()
            if cached:
                return cached

        return []
