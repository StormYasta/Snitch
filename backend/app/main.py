import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models import Deputado
from app.data.seed_data import load_seed_data
from app.routers import deputados, proposicoes, votacoes, stats, busca, governo

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria tabelas se não existirem
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Seed demonstrativo é opt-in. Em uso normal a base deve ser alimentada
        # exclusivamente pelos comandos de sincronização com fontes oficiais.
        total_deputados = db.query(Deputado).count()
        if total_deputados == 0 and settings.load_demo_seed:
            logger.warning("LOAD_DEMO_SEED ativo: carregando dados demonstrativos.")
            load_seed_data(db)
    except Exception as e:
        logger.error(f"Erro ao inicializar base de dados: {e}")
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.app_name,
    description="Plataforma de acompanhamento da atividade legislativa da Câmara dos Deputados do Brasil",
    version="1.0.0",
    lifespan=lifespan
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas
app.include_router(stats.router)
app.include_router(deputados.router)
app.include_router(proposicoes.router)
app.include_router(votacoes.router)
app.include_router(busca.router)
app.include_router(governo.router)

@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok", "app": settings.app_name}
