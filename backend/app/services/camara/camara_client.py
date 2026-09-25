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

    def iter_paginated_pages(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        page_size: int = 100,
        max_pages: Optional[int] = None,
    ):
        """Itera por páginas sem manter uma listagem histórica inteira em memória."""
        page = 1
        base_params = dict(params or {})
        page_size = max(1, min(page_size, 100))

        while True:
            current_params = {**base_params, "pagina": page, "itens": page_size}
            payload = self.get(endpoint, params=current_params)
            dados = payload.get("dados", []) or []
            if not isinstance(dados, list):
                raise CamaraClientError(
                    f"Resposta inesperada em {endpoint} página {page}: dados não é lista."
                )
            if not dados:
                break
            yield page, dados

            links = payload.get("links", []) or []
            has_next = any(
                (link.get("rel") or "").lower() == "next"
                for link in links if isinstance(link, dict)
            )
            if not has_next or (max_pages is not None and page >= max_pages):
                break
            page += 1

    def get_paginated(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        page_size: int = 100,
        max_pages: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Agrega páginas para endpoints de detalhe com volume moderado."""
        return [
            item for _, dados in self.iter_paginated_pages(
                endpoint, params, page_size, max_pages
            )
            for item in dados
        ]

    # Deputados
    def get_deputados(self, params: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        res = self.get("/deputados", params=params)
        return res.get("dados", []) or []

    def get_deputados_all(self, params: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        return self.get_paginated("/deputados", params=params, page_size=100)

    def get_legislaturas(self, params: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        return self.get_paginated("/legislaturas", params=params, page_size=100)

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
        return self.get_paginated(f"/votacoes/{id}/votos")

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
        return self.get_paginated(f"/eventos/{id}/deputados")

    def get_evento_votacoes(self, id: int) -> list[dict[str, Any]]:
        res = self.get(f"/eventos/{id}/votacoes")
        return res.get("dados", []) or []
