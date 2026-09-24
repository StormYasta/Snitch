import logging
from typing import Optional, Any
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

class CamaraClientError(Exception):
    pass

class CamaraClient:
    """Cliente oficial para consumo da API v2 da Câmara dos Deputados.
    Fonte oficial: https://dadosabertos.camara.leg.br/api/v2
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None
    ):
        self.base_url = (base_url or settings.camara_api_url).rstrip("/")
        self.timeout = timeout or settings.camara_timeout
        self.max_retries = max_retries or settings.camara_max_retries
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Accept": "application/json",
                "User-Agent": "Snitch-ObservatorioLegislativo/1.0"
            }
        )

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get(self, endpoint: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Executa GET com retries e tratamento de erros."""
        clean_endpoint = "/" + endpoint.lstrip("/")
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._client.get(clean_endpoint, params=params)
                if response.status_code == 404:
                    return {"dados": None}
                response.raise_for_status()
                return response.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                last_error = e
                logger.warning(
                    f"Tentativa {attempt}/{self.max_retries} falhou para {clean_endpoint}: {e}"
                )

        raise CamaraClientError(f"Erro ao consultar {clean_endpoint} após {self.max_retries} tentativas: {last_error}")

    # Deputados
    def get_deputados(self, params: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        res = self.get("/deputados", params=params)
        return res.get("dados", []) or []

    def get_deputado(self, id: int) -> Optional[dict[str, Any]]:
        res = self.get(f"/deputados/{id}")
        return res.get("dados")

    def get_deputado_historico(self, id: int) -> list[dict[str, Any]]:
        res = self.get(f"/deputados/{id}/historico")
        return res.get("dados", []) or []

    def get_deputado_eventos(self, id: int, params: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        res = self.get(f"/deputados/{id}/eventos", params=params)
        return res.get("dados", []) or []

    def get_deputado_orgaos(self, id: int) -> list[dict[str, Any]]:
        res = self.get(f"/deputados/{id}/orgaos")
        return res.get("dados", []) or []

    # Proposicoes
    def get_proposicoes(self, params: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        res = self.get("/proposicoes", params=params)
        return res.get("dados", []) or []

    def get_proposicao(self, id: int) -> Optional[dict[str, Any]]:
        res = self.get(f"/proposicoes/{id}")
        return res.get("dados")

    def get_proposicao_autores(self, id: int) -> list[dict[str, Any]]:
        res = self.get(f"/proposicoes/{id}/autores")
        return res.get("dados", []) or []

    def get_proposicao_temas(self, id: int) -> list[dict[str, Any]]:
        res = self.get(f"/proposicoes/{id}/temas")
        return res.get("dados", []) or []

    def get_proposicao_tramitacoes(self, id: int) -> list[dict[str, Any]]:
        res = self.get(f"/proposicoes/{id}/tramitacoes")
        return res.get("dados", []) or []

    def get_proposicao_votacoes(self, id: int) -> list[dict[str, Any]]:
        res = self.get(f"/proposicoes/{id}/votacoes")
        return res.get("dados", []) or []

    # Votacoes
    def get_votacoes(self, params: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        res = self.get("/votacoes", params=params)
        return res.get("dados", []) or []

    def get_votacao(self, id: str) -> Optional[dict[str, Any]]:
        res = self.get(f"/votacoes/{id}")
        return res.get("dados")

    def get_votacao_votos(self, id: str) -> list[dict[str, Any]]:
        res = self.get(f"/votacoes/{id}/votos")
        return res.get("dados", []) or []

    def get_votacao_orientacoes(self, id: str) -> list[dict[str, Any]]:
        res = self.get(f"/votacoes/{id}/orientacoes")
        return res.get("dados", []) or []

    # Eventos
    def get_eventos(self, params: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        res = self.get("/eventos", params=params)
        return res.get("dados", []) or []

    def get_evento(self, id: int) -> Optional[dict[str, Any]]:
        res = self.get(f"/eventos/{id}")
        return res.get("dados")

    def get_evento_deputados(self, id: int) -> list[dict[str, Any]]:
        res = self.get(f"/eventos/{id}/deputados")
        return res.get("dados", []) or []

    def get_evento_votacoes(self, id: int) -> list[dict[str, Any]]:
        res = self.get(f"/eventos/{id}/votacoes")
        return res.get("dados", []) or []
