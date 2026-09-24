import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models import Deputado, DeputadoHistorico, utc_now
from app.services.camara.camara_client import CamaraClient

logger = logging.getLogger(__name__)

class DeputadosService:
    def __init__(self, client: Optional[CamaraClient] = None):
        self.client = client or CamaraClient()

    def transform_deputado(self, raw_data: dict) -> dict:
        """Converte o retorno da API (/deputados/{id} ou item de lista) para o modelo interno."""
        ultimo_status = raw_data.get("ultimoStatus") or {}
        gabinete = ultimo_status.get("gabinete") or {}
        rede_social = raw_data.get("redeSocial")
        if isinstance(rede_social, list):
            rede_social_list = rede_social
        elif isinstance(rede_social, str):
            rede_social_list = [rede_social]
        else:
            rede_social_list = []

        return {
            "camara_id": raw_data.get("id"),
            "nome_parlamentar": ultimo_status.get("nomeEleitoral") or raw_data.get("nome") or "Deputado(a)",
            "nome_civil": raw_data.get("nomeCivil") or raw_data.get("nome"),
            "sigla_partido": ultimo_status.get("siglaPartido") or raw_data.get("siglaPartido"),
            "uf": ultimo_status.get("siglaUf") or raw_data.get("siglaUf"),
            "url_foto": ultimo_status.get("urlFoto") or raw_data.get("urlFoto"),
            "situacao": ultimo_status.get("situacao") or raw_data.get("situacao"),
            "condicao_eleitoral": ultimo_status.get("condicaoEleitoral"),
            "descricao_status": ultimo_status.get("descricaoStatus"),
            "email": ultimo_status.get("email") or raw_data.get("email") or gabinete.get("email"),
            "legislatura": ultimo_status.get("idLegislatura") or raw_data.get("idLegislatura"),
            "gabinete_predio": gabinete.get("predio"),
            "gabinete_sala": gabinete.get("sala"),
            "gabinete_andar": gabinete.get("andar"),
            "gabinete_telefone": gabinete.get("telefone"),
            "data_nascimento": raw_data.get("dataNascimento"),
            "municipio_nascimento": raw_data.get("municipioNascimento"),
            "uf_nascimento": raw_data.get("ufNascimento"),
            "escolaridade": raw_data.get("escolaridade"),
            "rede_social": rede_social_list,
            "url_website": raw_data.get("urlWebsite"),
            "uri": raw_data.get("uri") or f"https://dadosabertos.camara.leg.br/api/v2/deputados/{raw_data.get('id')}",
            "dados_raw": raw_data,
        }

    def upsert_deputado(self, db: Session, raw_data: dict) -> Deputado:
        data = self.transform_deputado(raw_data)
        camara_id = data["camara_id"]
        deputado = db.query(Deputado).filter(Deputado.camara_id == camara_id).first()

        if deputado:
            for k, v in data.items():
                if v is not None or getattr(deputado, k) is None:
                    setattr(deputado, k, v)
            deputado.updated_at = utc_now()
        else:
            deputado = Deputado(**data)
            db.add(deputado)

        db.flush()
        return deputado

    def sync_deputados(self, db: Session, legislatura: int = 57, limite: int = 100) -> int:
        """Sincroniza deputados da API oficial."""
        logger.info(f"Sincronizando deputados da legislatura {legislatura}...")
        params = {
            "idLegislatura": legislatura,
            "ordem": "ASC",
            "ordenarPor": "nome",
            "itens": min(limite, 100),
        }
        deputados_lista = self.client.get_deputados(params=params)
        count = 0

        for item in deputados_lista[:limite]:
            dep_id = item["id"]
            try:
                detalhe = self.client.get_deputado(dep_id)
                raw = detalhe if detalhe else item
                dep = self.upsert_deputado(db, raw)
                count += 1

                # Sincroniza histórico
                try:
                    historico = self.client.get_deputado_historico(dep_id)
                    db.query(DeputadoHistorico).filter(DeputadoHistorico.deputado_id == dep.id).delete()
                    for h in historico:
                        db.add(DeputadoHistorico(
                            deputado_id=dep.id,
                            data_hora=h.get("dataHora"),
                            sigla_partido=h.get("siglaPartido"),
                            situacao=h.get("situacao"),
                            condicao_eleitoral=h.get("condicaoEleitoral"),
                            descricao_status=h.get("descricaoStatus"),
                            legislatura=h.get("idLegislatura")
                        ))
                except Exception as eh:
                    logger.warning(f"Erro ao buscar histórico do deputado {dep_id}: {eh}")

            except Exception as e:
                logger.error(f"Erro ao processar deputado {dep_id}: {e}")

        db.commit()
        logger.info(f"{count} deputados sincronizados com sucesso.")
        return count
