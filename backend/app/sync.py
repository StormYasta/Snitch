import sys
import logging
from datetime import datetime, timezone
from app.database import SessionLocal, engine, Base
from app.models import SyncRun, utc_now
from app.services.camara.deputados_service import DeputadosService
from app.services.camara.proposicoes_service import ProposicoesService
from app.services.camara.votacoes_service import VotacoesService
from app.services.camara.eventos_service import EventosService
from app.data.seed_data import load_seed_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def run_sync(tipo: str):
    # Assegura que tabelas existem
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    sync_run = SyncRun(
        tipo=tipo,
        iniciado_em=utc_now(),
        status="RUNNING",
        registros_processados=0
    )
    db.add(sync_run)
    db.commit()
    db.refresh(sync_run)

    total_processados = 0

    try:
        if tipo in ["seed"]:
            res = load_seed_data(db)
            total_processados = sum(res.values())
            logger.info(f"Carga de dados de amostra concluída: {res}")

        elif tipo in ["deputados"]:
            service = DeputadosService()
            total_processados += service.sync_deputados(db)

        elif tipo in ["proposicoes"]:
            service = ProposicoesService()
            total_processados += service.sync_proposicoes(db)

        elif tipo in ["votacoes"]:
            service = VotacoesService()
            total_processados += service.sync_votacoes(db)

        elif tipo in ["eventos"]:
            service = EventosService()
            total_processados += service.sync_eventos(db)

        elif tipo in ["all"]:
            logger.info("Iniciando sincronização completa...")
            try:
                dep_srv = DeputadosService()
                total_processados += dep_srv.sync_deputados(db, limite=50)

                prop_srv = ProposicoesService()
                total_processados += prop_srv.sync_proposicoes(db, limite=30)

                vot_srv = VotacoesService()
                total_processados += vot_srv.sync_votacoes(db, limite=20)

                evt_srv = EventosService()
                total_processados += evt_srv.sync_eventos(db, limite=20)
            except Exception as e_api:
                logger.warning(f"Conexão com a API externa indisponível ({e_api}). Carregando amostra oficial de referência...")
                res = load_seed_data(db)
                total_processados = sum(res.values())

        else:
            raise ValueError(f"Comando de sincronização desconhecido: '{tipo}'. Use: deputados, proposicoes, votacoes, eventos, all ou seed.")

        sync_run.status = "SUCCESS"
        sync_run.finalizado_em = utc_now()
        sync_run.registros_processados = total_processados
        db.commit()
        logger.info(f"Sincronização '{tipo}' concluída com sucesso! Total processado: {total_processados}")

    except Exception as e:
        logger.error(f"Falha na sincronização '{tipo}': {e}", exc_info=True)
        sync_run.status = "FAILED"
        sync_run.finalizado_em = utc_now()
        sync_run.erro = str(e)
        db.commit()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "all"
    run_sync(action.lower())
