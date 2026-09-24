import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Snitch - Acompanhamento Legislativo"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./snitch.db")
    camara_api_url: str = os.getenv("CAMARA_API_URL", "https://dadosabertos.camara.leg.br/api/v2")
    camara_timeout: float = float(os.getenv("CAMARA_TIMEOUT", "10.0"))
    camara_max_retries: int = int(os.getenv("CAMARA_MAX_RETRIES", "3"))
    siorg_api_url: str = os.getenv(
        "SIORG_API_URL",
        "https://estruturaorganizacional.dados.gov.br/doc/estrutura-organizacional/completa.json"
    )
    siorg_timeout: float = float(os.getenv("SIORG_TIMEOUT", "15.0"))
    cors_origins: list[str] = ["*"]

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
