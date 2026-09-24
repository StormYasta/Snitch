import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models import Evento, EventoDeputado, Deputado
from app.services.camara.camara_client import CamaraClient

logger = logging.getLogger(__name__)

class EventosService:
    def __init__(self, client: Optional[CamaraClient] = None):
        self.client = client or CamaraClient()

    def transform_evento(self, raw_data: dict) -> dict:
        local_camara = raw_data.get("localCamara") or {}
        local_str = local_camara.get("nome") or raw_data.get("local")
        if not local_str and local_camara.get("sala"):
            local_str = f"Sala {local_camara.get('sala')}, Prédio {local_camara.get('predio', '')}"

        return {
            "camara_id": raw_data.get("id"),
            "data_inicio": raw_data.get("dataHoraInicio"),
            "data_fim": raw_data.get("dataHoraFim"),
            "tipo": raw_data.get("descricaoTipo") or raw_data.get("tipo"),
            "descricao": raw_data.get("descricao") or "Evento na Câmara dos Deputados",
            "situacao": raw_data.get("situacao") or "Realizada",
            "local": local_str,
            "uri": raw_data.get("uri") or f"https://dadosabertos.camara.leg.br/api/v2/eventos/{raw_data.get('id')}",
            "dados_raw": raw_data,
        }

    def upsert_evento(self, db: Session, raw_data: dict) -> Evento:
        data = self.transform_evento(raw_data)
        camara_id = data["camara_id"]
        evento = db.query(Evento).filter(Evento.camara_id == camara_id).first()

        if evento:
            for k, v in data.items():
                if v is not None or getattr(evento, k) is None:
                    setattr(evento, k, v)
        else:
            evento = Evento(**data)
            db.add(evento)

        db.flush()
        return evento

    def sync_deputados_evento(self, db: Session, evento: Evento, deputados_data: list[dict]):
        db.query(EventoDeputado).filter(EventoDeputado.evento_id == evento.id).delete()
        for d in deputados_data:
            dep_camara_id = d.get("id")
            if not dep_camara_id:
                continue

            dep = db.query(Deputado).filter(Deputado.camara_id == dep_camara_id).first()
            if not dep:
                dep = Deputado(
                    camara_id=dep_camara_id,
                    nome_parlamentar=d.get("nome") or "Deputado",
                    sigla_partido=d.get("siglaPartido"),
                    uf=d.get("siglaUf"),
                    url_foto=d.get("urlFoto"),
                    legislatura=d.get("idLegislatura")
                )
                db.add(dep)
                db.flush()

            db.add(EventoDeputado(
                evento_id=evento.id,
                deputado_id=dep.id
            ))

    def sync_eventos(self, db: Session, limite: int = 30) -> int:
        """Sincroniza eventos recentes e presença de deputados."""
        logger.info("Sincronizando eventos...")
        params = {
            "ordem": "DESC",
            "ordenarPor": "dataHoraInicio",
            "itens": min(limite, 100),
        }
        eventos_lista = self.client.get_eventos(params=params)
        count = 0

        for item in eventos_lista[:limite]:
            evt_id = item["id"]
            try:
                detalhe = self.client.get_evento(evt_id)
                raw = detalhe if detalhe else item
                evento = self.upsert_evento(db, raw)
                count += 1

                # Deputados presentes no evento
                try:
                    deps = self.client.get_evento_deputados(evt_id)
                    self.sync_deputados_evento(db, evento, deps)
                except Exception as ed:
                    logger.warning(f"Erro ao buscar deputados do evento {evt_id}: {ed}")

            except Exception as e:
                logger.error(f"Erro ao processar evento {evt_id}: {e}")

        db.commit()
        logger.info(f"{count} eventos sincronizados com sucesso.")
        return count
