import argparse
import sys
import logging
from datetime import date
from typing import Optional
from app.database import SessionLocal, engine, Base
from app.models import SyncRun, utc_now
from app.services.camara.deputados_service import DeputadosService
from app.services.camara.proposicoes_service import ProposicoesService
from app.services.camara.votacoes_service import VotacoesService
from app.services.camara.eventos_service import EventosService
from app.services.camara.historico_service import HistoricoService
from app.services.camara.historico_legislativo_service import HistoricoLegislativoService
from app.services.siorg.estrutura_service import EstruturaService
from app.services.siorg.orgaos_service import OrgaosService
from app.data.seed_data import load_seed_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def run_sync(
    tipo: str,
    ano: Optional[int] = None,
    limite: Optional[int] = None,
    camara_ids: Optional[set[int]] = None,
    ano_inicial: Optional[int] = None,
    ano_final: Optional[int] = None,
    somente: str = "todos",
    limite_paginas: Optional[int] = None,
):
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
    sync_run_id = sync_run.id

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
            total_processados += service.sync_proposicoes(
                db, ano=ano or 2024, limite=limite or 50
            )

        elif tipo in ["votacoes"]:
            service = VotacoesService()
            total_processados += service.sync_votacoes(db)

        elif tipo in ["eventos"]:
            service = EventosService()
            total_processados += service.sync_eventos(db)

        elif tipo in ["historico"]:
            total_processados += HistoricoLegislativoService().sync_periodo(
                db,
                ano_inicial=ano_inicial or 2018,
                ano_final=ano_final or date.today().year,
                somente=somente,
                limite_paginas=limite_paginas,
            )

        elif tipo in ["legislaturas"]:
            service = HistoricoService()
            total_processados += service.sync_legislaturas(db)

        elif tipo in ["deputados_historicos"]:
            service = HistoricoService()
            total_processados += service.sync_legislaturas(db)
            total_processados += service.sync_deputados_historicos(db)
            total_processados += service.enrich_current_deputies(db)

        elif tipo in ["enriquecer_deputados"]:
            # Retoma somente o enriquecimento: não recarrega milhares de mandatos.
            total_processados += HistoricoService().enrich_current_deputies(
                db, ids=camara_ids
            )

        elif tipo in ["estrutura_governo"]:
            total_processados += EstruturaService().sync_estrutura_canonica(db)

        elif tipo in ["siorg"]:
            total_processados += EstruturaService().sync_estrutura_canonica(db)
            total_processados += OrgaosService().sync_orgaos_executivo(db, use_live_siorg=True)

        elif tipo in ["mvp2"]:
            logger.info("Sincronizando segunda etapa do MVP...")
            hist = HistoricoService()
            total_processados += hist.sync_legislaturas(db)
            total_processados += hist.sync_deputados_historicos(db)
            total_processados += hist.enrich_current_deputies(db)
            total_processados += EstruturaService().sync_estrutura_canonica(db)
            total_processados += OrgaosService().sync_orgaos_executivo(db, use_live_siorg=True)

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
            raise ValueError(
                f"Comando de sincronização desconhecido: '{tipo}'. "
                "Use: deputados, proposicoes, votacoes, eventos, legislaturas, "
                "deputados_historicos, enriquecer_deputados, historico, estrutura_governo, "
                "siorg, mvp2, all ou seed."
            )

        sync_run.status = "SUCCESS"
        sync_run.finalizado_em = utc_now()
        sync_run.registros_processados = total_processados
        db.commit()
        logger.info(f"Sincronização '{tipo}' concluída com sucesso! Total processado: {total_processados}")

    except Exception as e:
        logger.error("Falha na sincronização '%s': %s", tipo, e, exc_info=True)
        # Depois de um erro SQL a sessão fica inutilizável até executar rollback.
        # O registro de auditoria é escrito em uma transação independente.
        db.rollback()
        try:
            with SessionLocal() as audit_db:
                run = audit_db.get(SyncRun, sync_run_id)
                if run is not None:
                    run.status = "FAILED"
                    run.finalizado_em = utc_now()
                    run.registros_processados = total_processados
                    run.erro = str(e)[:10000]
                    audit_db.commit()
        except Exception:
            logger.exception("Não foi possível atualizar a auditoria da sincronização.")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sincronização da base oficial do Snitch")
    parser.add_argument("tipo", nargs="?", default="all")
    parser.add_argument("--ano", type=int, help="Ano de referência (somente proposicoes)")
    parser.add_argument("--limite", type=int, help="Quantidade (1 a 100, somente proposicoes)")
    parser.add_argument(
        "--ids", type=str,
        help="IDs oficiais da Câmara separados por vírgula (somente enriquecer_deputados)",
    )
    parser.add_argument("--ano-inicial", type=int, help="Ano inicial da carga histórica")
    parser.add_argument("--ano-final", type=int, help="Ano final da carga histórica")
    parser.add_argument(
        "--somente", choices=["todos", "proposicoes", "votacoes", "eventos"],
        default="todos", help="Conjunto a importar no modo historico",
    )
    parser.add_argument(
        "--limite-paginas", type=int,
        help="Amostra de até N páginas por ano e tipo (modo historico)",
    )
    args = parser.parse_args()

    if (args.ano is not None or args.limite is not None) and args.tipo.lower() != "proposicoes":
        parser.error("--ano e --limite são parâmetros exclusivos de proposicoes")
    if args.ano is not None and not 2000 <= args.ano <= 2100:
        parser.error("--ano deve estar entre 2000 e 2100")
    if args.limite is not None and not 1 <= args.limite <= 100:
        parser.error("--limite deve estar entre 1 e 100")

    if args.tipo.lower() != "historico" and (
        args.ano_inicial is not None or args.ano_final is not None
        or args.somente != "todos" or args.limite_paginas is not None
    ):
        parser.error("--ano-inicial, --ano-final, --somente e --limite-paginas exigem historico")
    if args.tipo.lower() == "historico":
        inicio = args.ano_inicial if args.ano_inicial is not None else 2018
        fim = args.ano_final if args.ano_final is not None else date.today().year
        if not 2000 <= inicio <= fim <= date.today().year:
            parser.error("O intervalo deve estar entre 2000 e o ano atual")
        if args.limite_paginas is not None and args.limite_paginas < 1:
            parser.error("--limite-paginas deve ser positivo")

    camara_ids = None
    if args.ids is not None:
        if args.tipo.lower() != "enriquecer_deputados":
            parser.error("--ids é exclusivo de enriquecer_deputados")
        try:
            raw_ids = [part.strip() for part in args.ids.split(",")]
            if not 1 <= len(raw_ids) <= 100 or any(
                not part.isdecimal() or int(part) <= 0 for part in raw_ids
            ):
                raise ValueError()
            camara_ids = {int(part) for part in raw_ids}
            if len(camara_ids) != len(raw_ids):
                raise ValueError()
        except ValueError:
            parser.error("--ids exige entre 1 e 100 IDs Câmara positivos, sem repetições")

    run_sync(
        args.tipo.lower(),
        ano=args.ano,
        limite=args.limite,
        camara_ids=camara_ids,
        ano_inicial=args.ano_inicial,
        ano_final=args.ano_final,
        somente=args.somente,
        limite_paginas=args.limite_paginas,
    )
