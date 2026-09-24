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

        legislaturas = legs_query.order_by(Legislatura.numero.desc()).all()
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

    def enrich_current_deputies(self, db: Session) -> int:
        """Enriquece todos os deputados da legislatura mais recente com detalhe e histórico."""
        latest = db.query(Legislatura).order_by(Legislatura.numero.desc()).first()
        if not latest:
            self.sync_legislaturas(db)
            latest = db.query(Legislatura).order_by(Legislatura.numero.desc()).first()
        if not latest:
            return 0

        rows = self.client.get_deputados_all(
            {
                "idLegislatura": latest.numero,
                "ordem": "ASC",
                "ordenarPor": "nome",
            }
        )
        count = 0

        for item in rows:
            dep_id = item.get("id")
            if not dep_id:
                continue
            try:
                raw = self.client.get_deputado(dep_id) or item
                dep = self.deputados_service.upsert_deputado(db, raw)

                mandato = (
                    db.query(Mandato)
                    .filter(
                        Mandato.deputado_id == dep.id,
                        Mandato.legislatura_numero == latest.numero,
                    )
                    .first()
                )
                if mandato:
                    mandato.sigla_partido = dep.sigla_partido
                    mandato.uf = dep.uf
                    mandato.situacao = dep.situacao
                    mandato.condicao_eleitoral = dep.condicao_eleitoral

                historico = self.client.get_deputado_historico(dep_id)
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
                count += 1
            except Exception as exc:
                logger.warning("Falha ao enriquecer deputado %s: %s", dep_id, exc)

        db.commit()
        logger.info("%s deputados atuais enriquecidos.", count)
        return count
