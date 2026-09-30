import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Legislatura, Mandato, Deputado, DeputadoHistorico, utc_now
from app.services.camara.camara_client import CamaraClient
from app.services.camara.deputados_service import DeputadosService

logger = logging.getLogger(__name__)


class HistoricoService:
    """Sincroniza legislaturas e a base histórica de parlamentares da Câmara.

    A carga histórica usa as listagens oficiais por legislatura para evitar milhares
    de chamadas de detalhe. Perfis atuais podem ser enriquecidos separadamente pelo
    DeputadosService.
    """

    def __init__(
        self,
        client: Optional[CamaraClient] = None,
        deputados_service: Optional[DeputadosService] = None,
    ):
        self.client = client or CamaraClient()
        self.deputados_service = deputados_service or DeputadosService(self.client)

    def sync_legislaturas(self, db: Session) -> int:
        logger.info("Sincronizando legislaturas da Câmara...")
        rows = self.client.get_legislaturas({"ordem": "DESC", "ordenarPor": "id"})
        count = 0

        for raw in rows:
            numero = raw.get("id")
            if numero is None:
                continue

            leg = db.query(Legislatura).filter(Legislatura.camara_id == numero).first()
            if not leg:
                leg = Legislatura(camara_id=numero, numero=numero)
                db.add(leg)

            leg.numero = numero
            leg.data_inicio = raw.get("dataInicio")
            leg.data_fim = raw.get("dataFim")
            try:
                leg.ano_inicio = int(str(leg.data_inicio)[:4]) if leg.data_inicio else None
                leg.ano_fim = int(str(leg.data_fim)[:4]) if leg.data_fim else None
            except ValueError:
                leg.ano_inicio = None
                leg.ano_fim = None
            count += 1

        db.commit()
        logger.info("%s legislaturas sincronizadas.", count)
        return count

    def _ensure_mandato(
        self,
        db: Session,
        deputado: Deputado,
        legislatura: Legislatura,
        raw: dict,
        current_legislatura: int,
    ) -> None:
        mandato = (
            db.query(Mandato)
            .filter(
                Mandato.deputado_id == deputado.id,
                Mandato.legislatura_numero == legislatura.numero,
            )
            .first()
        )
        if not mandato:
            mandato = Mandato(
                deputado_id=deputado.id,
                legislatura_id=legislatura.id,
                legislatura_numero=legislatura.numero,
                cargo="Deputado Federal",
            )
            db.add(mandato)

        mandato.legislatura_id = legislatura.id
        mandato.sigla_partido = raw.get("siglaPartido")
        mandato.uf = raw.get("siglaUf")
        mandato.data_inicio = legislatura.data_inicio
        mandato.data_fim = legislatura.data_fim
        # A listagem histórica não informa com segurança o estado funcional do
        # parlamentar ao longo de todo o mandato. Para a legislatura atual,
        # deixamos o enriquecimento de situação para /deputados/{id}.
        if legislatura.numero < current_legislatura:
            mandato.situacao = "Mandato encerrado"

    def sync_deputados_historicos(
        self,
        db: Session,
        legislatura_min: Optional[int] = None,
        legislatura_max: Optional[int] = None,
    ) -> int:
        """Importa todos os parlamentares listados oficialmente por legislatura.

        Retorna a quantidade de vínculos deputado-legislatura processados. Deputados
        repetidos em legislaturas diferentes são preservados como uma única pessoa,
        conectada a múltiplos mandatos.
        """
        if db.query(Legislatura).count() == 0:
            self.sync_legislaturas(db)

        legs_query = db.query(Legislatura)
        if legislatura_min is not None:
            legs_query = legs_query.filter(Legislatura.numero >= legislatura_min)
        if legislatura_max is not None:
            legs_query = legs_query.filter(Legislatura.numero <= legislatura_max)

        # Processa da mais antiga para a mais recente para que o registro principal
        # da pessoa termine refletindo sua participação parlamentar mais recente.
        legislaturas = legs_query.order_by(Legislatura.numero.asc()).all()
        if not legislaturas:
            logger.warning("Nenhuma legislatura disponível para a carga histórica.")
            return 0

        current_legislatura = max(l.numero for l in legislaturas)
        processed = 0

        for leg in legislaturas:
            logger.info("Importando deputados da %sª Legislatura...", leg.numero)
            rows = self.client.get_deputados_all(
                {
                    "idLegislatura": leg.numero,
                    "ordem": "ASC",
                    "ordenarPor": "nome",
                }
            )

            for raw in rows:
                if not raw.get("id"):
                    continue
                deputado = self.deputados_service.upsert_deputado(db, raw)
                self._ensure_mandato(db, deputado, leg, raw, current_legislatura)
                processed += 1

            db.commit()

        logger.info("%s vínculos históricos deputado-legislatura processados.", processed)
        return processed

    def enrich_current_deputies(
        self, db: Session, ids: Optional[set[int]] = None
    ) -> int:
        """Enriquece a legislatura mais recente, com commit e recuperação por deputado.

        Reexecuções são seguras: perfis e históricos são atualizados pelo ID oficial.
        Cada deputado é uma transação independente para não perder todo o progresso
        quando um registro ou uma conexão falha.
        """
        latest = db.query(Legislatura).order_by(Legislatura.numero.desc()).first()
        if not latest:
            self.sync_legislaturas(db)
            latest = db.query(Legislatura).order_by(Legislatura.numero.desc()).first()
        if not latest:
            db.rollback()
            return 0

        latest_numero = latest.numero
        # Libera a transação de leitura antes das chamadas HTTP potencialmente longas.
        db.rollback()
        if ids is None:
            rows = self.client.get_deputados_all(
                {
                    "idLegislatura": latest_numero,
                    "ordem": "ASC",
                    "ordenarPor": "nome",
                }
            )
        else:
            # --ids contém identificadores oficiais (Câmara), não chaves internas
            # da tabela deputados. Não carrega novamente a listagem inteira.
            known = {
                camara_id for (camara_id,) in (
                    db.query(Deputado.camara_id)
                    .join(Mandato, Mandato.deputado_id == Deputado.id)
                    .filter(
                        Mandato.legislatura_numero == latest_numero,
                        Deputado.camara_id.in_(ids),
                    )
                    .all()
                )
            }
            db.rollback()
            unknown = ids - known
            if unknown:
                raise ValueError(
                    "IDs Câmara sem mandato na legislatura atual: "
                    + ", ".join(str(value) for value in sorted(unknown))
                )
            rows = [{"id": value} for value in sorted(ids)]

        count = 0
        failures: list[tuple[int, str]] = []

        for item in rows:
            dep_id = item.get("id")
            if not dep_id:
                continue
            try:
                # Chama a API antes de abrir a transação de escrita.
                raw = self.client.get_deputado(dep_id) or item
                try:
                    historico = self.client.get_deputado_historico(dep_id)
                except Exception as exc:
                    logger.warning(
                        "Histórico de %s indisponível; preservando histórico existente: %s",
                        dep_id, exc,
                    )
                    historico = None

                dep = self.deputados_service.upsert_deputado(db, raw)
                mandato = (
                    db.query(Mandato)
                    .filter(
                        Mandato.deputado_id == dep.id,
                        Mandato.legislatura_numero == latest_numero,
                    )
                    .first()
                )
                if mandato:
                    mandato.sigla_partido = dep.sigla_partido
                    mandato.uf = dep.uf
                    mandato.situacao = dep.situacao
                    mandato.condicao_eleitoral = dep.condicao_eleitoral

                if historico is not None:
                    db.query(DeputadoHistorico).filter(
                        DeputadoHistorico.deputado_id == dep.id
                    ).delete()
                    for h in historico:
                        db.add(
                            DeputadoHistorico(
                                deputado_id=dep.id,
                                data_hora=h.get("dataHora"),
                                sigla_partido=h.get("siglaPartido"),
                                situacao=h.get("situacao"),
                                condicao_eleitoral=h.get("condicaoEleitoral"),
                                descricao_status=h.get("descricaoStatus"),
                                legislatura=h.get("idLegislatura"),
                            )
                        )

                dep.updated_at = utc_now()
                db.commit()
                count += 1
                if count % 25 == 0:
                    logger.info("%s deputados enriquecidos nesta execução.", count)
            except Exception as exc:
                failures.append((dep_id, f"{type(exc).__name__}: {exc}"))
                # PostgreSQL exige rollback depois de qualquer erro SQL.
                # Também permite reconectar após uma conexão invalidada.
                db.rollback()
                logger.exception("Falha ao enriquecer deputado %s; prosseguindo.", dep_id)

        logger.info(
            "Enriquecimento finalizado: %s concluídos, %s falhas.",
            count, len(failures),
        )
        if failures:
            details = "; ".join(
                f"{dep_id} ({reason[:250]})" for dep_id, reason in failures
            )
            raise RuntimeError(
                f"Enriquecimento incompleto: {count} concluídos e "
                f"{len(failures)} falhas; os registros concluídos foram preservados. "
                f"IDs Câmara com falhas: {details}. "
                "Use --ids para repetir apenas os registros pendentes."
            )
        return count
