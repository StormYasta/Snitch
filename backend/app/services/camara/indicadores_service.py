import calendar
import logging
import unicodedata
import xml.etree.ElementTree as ET
from datetime import date
from typing import Optional

import httpx
from sqlalchemy import distinct, func, or_
from sqlalchemy.orm import Session

from app.models import Deputado, Proposicao, ProposicaoAutor, Votacao, Voto
from app.services.camara.camara_client import CamaraClient

logger = logging.getLogger(__name__)


class IndicadoresService:
    """Calcula indicadores objetivos e consulta fontes oficiais complementares da Câmara."""

    PRESENCAS_URL = (
        "https://www.camara.leg.br/SitCamaraWS/SessoesReunioes.asmx/"
        "ListarPresencasParlamentar"
    )
    DEPUTADOS_LEGACY_URL = (
        "https://www.camara.leg.br/SitCamaraWS/deputados.asmx/ObterDeputados"
    )

    @staticmethod
    def _normalizar(texto: Optional[str]) -> str:
        if not texto:
            return ""
        normalized = unicodedata.normalize("NFKD", texto)
        return "".join(ch for ch in normalized if not unicodedata.combining(ch)).strip().lower()

    @staticmethod
    def _local_name(tag: str) -> str:
        return tag.rsplit("}", 1)[-1].lower()

    @classmethod
    def _desc_text(cls, node: ET.Element, *names: str) -> str:
        wanted = {name.lower() for name in names}
        for child in node.iter():
            if cls._local_name(child.tag) in wanted and child.text:
                return child.text.strip()
        return ""

    @classmethod
    def _find_matricula(cls, xml_text: str, camara_id: int) -> Optional[str]:
        root = ET.fromstring(xml_text)
        target = str(camara_id)
        for node in root.iter():
            if cls._local_name(node.tag) != "deputado":
                continue
            ide = cls._desc_text(node, "ideCadastro", "idCadastro", "id")
            if ide == target:
                matricula = cls._desc_text(node, "matricula")
                return matricula or None
        return None

    @classmethod
    def _justificativa_valida(cls, texto: str) -> bool:
        value = cls._normalizar(texto)
        if not value:
            return False
        invalid = (
            "sem justificativa",
            "nao justificada",
            "nao informado",
            "nao informada",
            "nenhuma",
        )
        return not any(term in value for term in invalid)

    @classmethod
    def _parse_presencas(cls, xml_text: str) -> dict:
        root = ET.fromstring(xml_text)
        presencas = 0
        faltas = 0
        justificadas = 0

        dias = [node for node in root.iter() if cls._local_name(node.tag) == "diadesessao"]
        for dia in dias:
            justificativa = cls._desc_text(dia, "justificativa", "motivoPresenca")
            sessoes = [
                node for node in dia.iter()
                if cls._local_name(node.tag) in {"frequenciasessaodia", "sessao"}
            ]

            frequencias = []
            for sessao in sessoes:
                freq = cls._desc_text(sessao, "frequenciaSessao", "frequencia")
                if freq:
                    frequencias.append(freq)

            if not frequencias:
                frequencia_dia = cls._desc_text(
                    dia,
                    "descricaoFrequenciaDia",
                    "simboloPresenca",
                    "frequencia",
                )
                if frequencia_dia:
                    qtd_text = cls._desc_text(dia, "qtdeSessoesDia")
                    try:
                        qtd = max(int(qtd_text), 1)
                    except (TypeError, ValueError):
                        qtd = 1
                    frequencias = [frequencia_dia] * qtd

            for freq in frequencias:
                normalized = cls._normalizar(freq)
                if "presen" in normalized:
                    presencas += 1
                    continue

                is_absence = any(
                    marker in normalized
                    for marker in ("ausen", "falta", "nao compareceu", "nao esteve")
                )
                if not is_absence:
                    continue

                faltas += 1
                justificativa_no_status = (
                    "justific" in normalized
                    and "nao justific" not in normalized
                    and "sem justific" not in normalized
                )
                if justificativa_no_status or cls._justificativa_valida(justificativa):
                    justificadas += 1

        total = presencas + faltas
        return {
            "presencas_plenario": presencas if total else None,
            "faltas_plenario": faltas if total else None,
            "faltas_justificadas": justificadas if total else None,
            "faltas_nao_justificadas": (faltas - justificadas) if total else None,
            "percentual_presenca": round((presencas / total) * 100, 1) if total else None,
        }

    def _buscar_presencas(self, camara_id: int, ano: int, mes: int) -> dict:
        empty = {
            "presencas_plenario": None,
            "faltas_plenario": None,
            "faltas_justificadas": None,
            "faltas_nao_justificadas": None,
            "percentual_presenca": None,
        }

        hoje = date.today()
        inicio = date(ano, mes, 1)
        fim = date(ano, mes, calendar.monthrange(ano, mes)[1])
        if inicio > hoje:
            return empty
        if ano == hoje.year and mes == hoje.month:
            fim = hoje

        try:
            with httpx.Client(
                timeout=4.0,
                follow_redirects=True,
                headers={"User-Agent": "Snitch-ObservatorioLegislativo/1.0"},
            ) as client:
                deputados_resp = client.get(self.DEPUTADOS_LEGACY_URL)
                deputados_resp.raise_for_status()
                matricula = self._find_matricula(deputados_resp.text, camara_id)
                if not matricula:
                    logger.warning("Matrícula não localizada para deputado Câmara ID %s", camara_id)
                    return empty

                presencas_resp = client.post(
                    self.PRESENCAS_URL,
                    data={
                        "dataIni": inicio.strftime("%d/%m/%Y"),
                        "dataFim": fim.strftime("%d/%m/%Y"),
                        "numMatriculaParlamentar": matricula,
                    },
                )
                presencas_resp.raise_for_status()
                return self._parse_presencas(presencas_resp.text)
        except (httpx.HTTPError, ET.ParseError, ValueError) as exc:
            logger.warning("Não foi possível consultar presença oficial de %s: %s", camara_id, exc)
            return empty

    def _buscar_cota(self, camara_id: int, ano: int, mes: int) -> Optional[float]:
        client = CamaraClient(timeout=4.0, max_retries=1)
        try:
            total = 0.0
            pagina = 1
            while pagina <= 20:
                response = client.get(
                    f"/deputados/{camara_id}/despesas",
                    params={
                        "ano": ano,
                        "mes": mes,
                        "itens": 100,
                        "pagina": pagina,
                        "ordem": "ASC",
                        "ordenarPor": "dataDocumento",
                    },
                )
                despesas = response.get("dados", []) or []
                for despesa in despesas:
                    valor = despesa.get("valorLiquido")
                    if valor is None:
                        continue
                    try:
                        total += float(valor)
                    except (TypeError, ValueError):
                        continue

                if len(despesas) < 100:
                    break
                pagina += 1
            return round(total, 2)
        except Exception as exc:
            logger.warning("Não foi possível consultar a cota de %s: %s", camara_id, exc)
            return None
        finally:
            client.close()

    @staticmethod
    def _proposicao_aprovada(proposicao: Proposicao) -> bool:
        texto = " ".join(
            part for part in (proposicao.situacao, proposicao.descricao_situacao) if part
        ).lower()
        return any(
            termo in texto
            for termo in (
                "aprovad",
                "sancionad",
                "transformad em norma",
                "transformada em norma",
                "convertid em lei",
            )
        )

    def get_indicadores(
        self,
        db: Session,
        deputado: Deputado,
        ano: Optional[int] = None,
        mes: Optional[int] = None,
    ) -> dict:
        hoje = date.today()
        ano_ref = ano or hoje.year
        mes_ref = mes or hoje.month

        pls = (
            db.query(Proposicao)
            .join(ProposicaoAutor, Proposicao.id == ProposicaoAutor.proposicao_id)
            .filter(
                ProposicaoAutor.deputado_id == deputado.id,
                func.upper(Proposicao.sigla_tipo) == "PL",
                Proposicao.ano == ano_ref,
            )
            .distinct()
            .all()
        )
        pls_apresentados = len(pls)
        pls_aprovados = sum(1 for proposicao in pls if self._proposicao_aprovada(proposicao))

        votacoes_nominais = (
            db.query(func.count(distinct(Voto.votacao_id)))
            .join(Votacao, Voto.votacao_id == Votacao.id)
            .filter(
                Voto.deputado_id == deputado.id,
                or_(
                    Voto.data_hora.like(f"{ano_ref}%"),
                    Votacao.data_hora_registro.like(f"{ano_ref}%"),
                ),
            )
            .scalar()
            or 0
        )

        percentual_pls = (
            round((pls_aprovados / pls_apresentados) * 100, 1)
            if pls_apresentados
            else 0.0
        )

        presencas = self._buscar_presencas(deputado.camara_id, ano_ref, mes_ref)
        uso_cota = self._buscar_cota(deputado.camara_id, ano_ref, mes_ref)

        return {
            "ano_referencia": ano_ref,
            "mes_referencia": mes_ref,
            **presencas,
            "pls_apresentados": pls_apresentados,
            "pls_aprovados": pls_aprovados,
            "percentual_pls_aprovados": percentual_pls,
            "uso_cota_mes": uso_cota,
            "votacoes_nominais": int(votacoes_nominais),
        }
