#!/usr/bin/env python3
"""Gera indicadores offline oficiais para os 100 perfis da 57ª Legislatura.

O arquivo separa:
- PLs apresentados e situação registrada, por ano (2023 até o ano atual);
- presença de Plenário e CEAP apenas do mês corrente;
- quantidade de votações da *amostra offline*, quando o showcase já existe.

Não cria números sintéticos. Falhas ficam como null e são registradas na metadata.
"""
from __future__ import annotations

import argparse
import calendar
import gzip
import json
import re
import time
import unicodedata
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "https://dadosabertos.camara.leg.br/api/v2"
LEGACY_DEPUTIES = "https://www.camara.leg.br/SitCamaraWS/deputados.asmx/ObterDeputados"
LEGACY_PRESENCE = "https://www.camara.leg.br/SitCamaraWS/SessoesReunioes.asmx/ListarPresencasParlamentar"
UA = "Snitch-ObservatorioLegislativo/1.0 (+https://github.com/StormYasta/Snitch)"
YEARS = tuple(range(2023, date.today().year + 1))


def request(url: str, data: bytes | None = None, attempts: int = 4, timeout: int = 35) -> bytes:
    last = None
    for attempt in range(attempts):
        try:
            req = Request(
                url,
                data=data,
                headers={
                    "Accept": "application/json, application/xml, text/xml, */*",
                    "User-Agent": UA,
                    **({"Content-Type": "application/x-www-form-urlencoded"} if data is not None else {}),
                },
            )
            with urlopen(req, timeout=timeout) as response:
                return response.read()
        except Exception as exc:
            last = exc
            if attempt + 1 < attempts:
                time.sleep(min(8, 2 ** attempt))
    raise RuntimeError(f"Falha em {url}: {last}")


def get_json(path: str, params: dict | None = None) -> dict:
    url = f"{API}/{path.lstrip('/')}"
    if params:
        url += "?" + urlencode(params, doseq=True)
    return json.loads(request(url).decode("utf-8"))


def normalize(text: str | None) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in value if not unicodedata.combining(ch)).strip().lower()


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def desc(node: ET.Element, *names: str) -> str:
    wanted = {name.lower() for name in names}
    for child in node.iter():
        if local(child.tag) in wanted and child.text:
            return child.text.strip()
    return ""


def legacy_matriculas() -> dict[int, str]:
    root = ET.fromstring(request(LEGACY_DEPUTIES).decode("utf-8", errors="replace"))
    result: dict[int, str] = {}
    for node in root.iter():
        if local(node.tag) != "deputado":
            continue
        ident = desc(node, "ideCadastro", "idCadastro", "id")
        matricula = desc(node, "matricula")
        if ident.isdigit() and matricula:
            result[int(ident)] = matricula
    return result


def valid_justification(text: str) -> bool:
    value = normalize(text)
    if not value:
        return False
    return not any(term in value for term in (
        "sem justificativa", "nao justificada", "nao informado",
        "nao informada", "nenhuma",
    ))


def parse_presence(xml_bytes: bytes) -> dict:
    root = ET.fromstring(xml_bytes.decode("utf-8", errors="replace"))
    present = absent = justified = 0
    days = [node for node in root.iter() if local(node.tag) == "diadesessao"]
    for day in days:
        justification = desc(day, "justificativa", "motivoPresenca")
        sessions = [
            node for node in day.iter()
            if local(node.tag) in {"frequenciasessaodia", "sessao"}
        ]
        freqs = []
        for session in sessions:
            value = desc(session, "frequenciaSessao", "frequencia")
            if value:
                freqs.append(value)
        if not freqs:
            value = desc(day, "descricaoFrequenciaDia", "simboloPresenca", "frequencia")
            if value:
                try:
                    quantity = max(int(desc(day, "qtdeSessoesDia")), 1)
                except (TypeError, ValueError):
                    quantity = 1
                freqs = [value] * quantity
        for freq in freqs:
            value = normalize(freq)
            if "presen" in value:
                present += 1
                continue
            if not any(marker in value for marker in ("ausen", "falta", "nao compareceu", "nao esteve")):
                continue
            absent += 1
            status_justified = "justific" in value and "nao justific" not in value and "sem justific" not in value
            if status_justified or valid_justification(justification):
                justified += 1
    total = present + absent
    return {
        "presencas_plenario": present if total else None,
        "faltas_plenario": absent if total else None,
        "faltas_justificadas": justified if total else None,
        "faltas_nao_justificadas": absent - justified if total else None,
        "percentual_presenca": round(present / total * 100, 1) if total else None,
    }


def fetch_presence(matricula: str | None, year: int, month: int) -> dict:
    empty = {
        "presencas_plenario": None,
        "faltas_plenario": None,
        "faltas_justificadas": None,
        "faltas_nao_justificadas": None,
        "percentual_presenca": None,
    }
    if not matricula:
        return empty
    end_day = calendar.monthrange(year, month)[1]
    if year == date.today().year and month == date.today().month:
        end_day = date.today().day
    body = urlencode({
        "dataIni": f"01/{month:02d}/{year}",
        "dataFim": f"{end_day:02d}/{month:02d}/{year}",
        "numMatriculaParlamentar": matricula,
    }).encode()
    try:
        return parse_presence(request(LEGACY_PRESENCE, data=body))
    except Exception:
        return empty


def fetch_expenses(dep_id: int, year: int, month: int) -> float | None:
    total = 0.0
    saw_response = False
    for page in range(1, 21):
        payload = get_json(
            f"deputados/{dep_id}/despesas",
            {
                "ano": year, "mes": month, "pagina": page, "itens": 100,
                "ordem": "ASC", "ordenarPor": "dataDocumento",
            },
        )
        rows = payload.get("dados") or []
        saw_response = True
        for row in rows:
            try:
                total += float(row.get("valorLiquido"))
            except (TypeError, ValueError):
                pass
        if len(rows) < 100:
            break
    return round(total, 2) if saw_response else None


def approved_status(item: dict) -> bool:
    status = item.get("statusProposicao") or item.get("ultimoStatus") or {}
    text = " ".join(
        str(value) for value in (
            status.get("descricaoSituacao"),
            item.get("situacao"),
            item.get("descricaoSituacao"),
        ) if value
    ).lower()
    return any(term in text for term in (
        "aprovad", "sancionad", "transformad em norma",
        "transformada em norma", "convertid em lei",
    ))


def fetch_pls(dep_id: int, year: int) -> dict:
    rows: list[dict] = []
    page = 1
    while page <= 20:
        payload = get_json(
            "proposicoes",
            {
                "idDeputadoAutor": dep_id,
                "ano": year,
                "siglaTipo": "PL",
                "pagina": page,
                "itens": 100,
                "ordem": "DESC",
                "ordenarPor": "id",
            },
        )
        batch = payload.get("dados") or []
        rows.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    approved = sum(1 for item in rows if approved_status(item))
    return {
        "pls_apresentados": len({item.get("id") for item in rows if item.get("id") is not None}),
        "pls_aprovados_situacao": approved,
    }


def voting_sample(showcase: Path) -> dict[str, dict[str, int]]:
    if not showcase.exists():
        return {}
    with gzip.open(showcase, "rt", encoding="utf-8") as handle:
        data = json.load(handle)
    result: dict[str, dict[str, set[str]]] = {}
    for bundle in data.get("votacoes") or []:
        raw = bundle.get("dados") or {}
        stamp = raw.get("dataHoraRegistro") or raw.get("data") or ""
        year = stamp[:4]
        vid = str(raw.get("id") or "")
        if not year.isdigit() or not vid:
            continue
        year_map = result.setdefault(year, {})
        for vote in bundle.get("votos") or []:
            info = vote.get("deputado_") or vote.get("deputado") or {}
            dep_id = info.get("id")
            if dep_id is None:
                continue
            year_map.setdefault(str(dep_id), set()).add(vid)
    return {
        year: {dep_id: len(ids) for dep_id, ids in deputies.items()}
        for year, deputies in result.items()
    }


def load_existing(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deputados", default="backend/app/data/deputados_offline_100.json")
    parser.add_argument("--showcase", default="backend/app/data/base57_showcase.json.gz")
    parser.add_argument("--output", default="backend/app/data/indicadores57_offline.json")
    args = parser.parse_args()

    deps_payload = json.loads(Path(args.deputados).read_text(encoding="utf-8"))
    deputies = deps_payload.get("dados") or []
    if len(deputies) != 100:
        raise RuntimeError("São necessários exatamente 100 deputados no snapshot.")
    ids = [int(item["id"]) for item in deputies]

    output = Path(args.output)
    data = load_existing(output)
    data.setdefault("anos", {})
    data.setdefault("meses", {})
    failures: list[str] = []

    # PLs de toda a 57ª Legislatura até o ano corrente.
    for year in YEARS:
        year_rows: dict[str, dict] = {}
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {executor.submit(fetch_pls, dep_id, year): dep_id for dep_id in ids}
            for future in as_completed(futures):
                dep_id = futures[future]
                try:
                    year_rows[str(dep_id)] = future.result()
                except Exception as exc:
                    failures.append(f"PL/{year}/{dep_id}: {exc}")
        data["anos"][str(year)] = {
            "ano": year,
            "deputados": year_rows,
        }
        print(f"PLs {year}: {len(year_rows)}/100 deputados", flush=True)

    now = date.today()
    month_key = f"{now.year:04d}-{now.month:02d}"
    try:
        matriculas = legacy_matriculas()
    except Exception as exc:
        failures.append(f"matriculas: {exc}")
        matriculas = {}

    month_rows: dict[str, dict] = {}
    def month_bundle(dep_id: int) -> tuple[int, dict]:
        presence = fetch_presence(matriculas.get(dep_id), now.year, now.month)
        try:
            expense = fetch_expenses(dep_id, now.year, now.month)
        except Exception:
            expense = None
        return dep_id, {**presence, "uso_cota_mes": expense}

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(month_bundle, dep_id): dep_id for dep_id in ids}
        for future in as_completed(futures):
            dep_id = futures[future]
            try:
                key, payload = future.result()
                month_rows[str(key)] = payload
            except Exception as exc:
                failures.append(f"MES/{month_key}/{dep_id}: {exc}")

    retrieved = datetime.now(timezone.utc).isoformat()
    data["meses"][month_key] = {
        "ano": now.year,
        "mes": now.month,
        "retrieved_at": retrieved,
        "deputados": month_rows,
    }
    data["votacoes_amostra"] = voting_sample(Path(args.showcase))
    data["_meta"] = {
        "source": "Câmara dos Deputados — Dados Abertos + SitCamaraWS",
        "retrieved_at": retrieved,
        "legislatura": 57,
        "deputy_count": 100,
        "years": list(YEARS),
        "monthly_snapshot": month_key,
        "failures": failures[:50],
        "limitations": (
            "Presença e CEAP são snapshots do mês indicado. PLs são contados pela "
            "consulta oficial por autor e ano; 'aprovados' usa a situação textual "
            "registrada e não representa juízo sobre mérito. Votações nominais, quando "
            "presentes, correspondem somente à amostra offline do showcase."
        ),
    }

    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Indicadores salvos em {output}; mês {month_key}: {len(month_rows)}/100; "
        f"falhas={len(failures)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
