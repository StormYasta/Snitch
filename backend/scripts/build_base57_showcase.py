#!/usr/bin/env python3
"""Gera uma amostra offline factual da 57ª Legislatura sem baixar arquivos anuais grandes.

A Câmara fica lenta em downloads anuais completos. Para tornar o job robusto,
o gerador consulta /votacoes em janelas mensais pequenas e depois enriquece
somente uma amostra temporal de votações com votos individuais.

Critério de seleção:
- 100 deputados do snapshot oficial já versionado;
- até 15 votações por ano, distribuídas ao longo do período;
- só entram votações com ao menos 5 votos registrados entre esses 100 perfis;
- nenhuma seleção por partido, deputado, tema, resultado ou sentido do voto.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import time
from calendar import monthrange
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "https://dadosabertos.camara.leg.br/api/v2"
USER_AGENT = "Snitch-ObservatorioLegislativo/1.0 (+https://github.com/StormYasta/Snitch)"
YEARS = (2023, 2024, 2025, 2026)
PER_YEAR = 15
MIN_SELECTED_VOTES = 5
MAX_CANDIDATES_PER_YEAR = 70


def request_json(path: str, params: dict | None = None, attempts: int = 4) -> dict:
    url = f"{API}/{path.lstrip('/')}"
    if params:
        url += "?" + urlencode(params, doseq=True)
    last_error = None
    for attempt in range(attempts):
        try:
            req = Request(
                url,
                headers={"Accept": "application/json", "User-Agent": USER_AGENT},
            )
            with urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            try:
                body = exc.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                body = ""
            last_error = RuntimeError(f"HTTP {exc.code}: {body}")
        except Exception as exc:
            last_error = exc
        if attempt + 1 < attempts:
            time.sleep(min(8, 2 ** attempt))
    raise RuntimeError(f"Falha em {url}: {last_error}")


def deputy_id(vote: dict) -> int | None:
    info = vote.get("deputado_") or vote.get("deputado") or {}
    value = info.get("id")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def month_windows(year: int):
    today = date.today()
    first_month = 2 if year == 2023 else 1
    for month in range(first_month, 13):
        start = date(year, month, 1)
        if start > today:
            break
        end = date(year, month, monthrange(year, month)[1])
        if end > today:
            end = today
        yield start, end


def list_month(year: int, start: date, end: date, errors: list[str]) -> list[dict]:
    rows: list[dict] = []
    page = 1
    while page <= 5:
        try:
            payload = request_json(
                "votacoes",
                {
                    "dataInicio": start.isoformat(),
                    "dataFim": end.isoformat(),
                    "pagina": page,
                    "itens": 100,
                },
            )
        except Exception as exc:
            errors.append(f"listagem/{year}/{start.month:02d}/p{page}: {exc}")
            break

        batch = payload.get("dados") or []
        rows.extend(batch)
        if len(batch) < 100:
            break

        links = payload.get("links") or []
        has_next = any(
            isinstance(link, dict) and (link.get("rel") or "").lower() == "next"
            for link in links
        )
        if not has_next:
            break
        page += 1
    return rows


def voting_stamp(item: dict) -> str:
    return item.get("dataHoraRegistro") or item.get("data") or ""


def voting_id(item: dict) -> str:
    value = item.get("id")
    return str(value) if value is not None else ""


def spread_candidates(rows: list[dict], maximum: int) -> list[dict]:
    if len(rows) <= maximum:
        return rows
    indexes = []
    for i in range(maximum):
        position = round(i * (len(rows) - 1) / max(maximum - 1, 1))
        indexes.append(position)
    return [rows[i] for i in dict.fromkeys(indexes)]


def fetch_candidate(item: dict, selected_ids: set[int]) -> dict | None:
    vid = voting_id(item)
    if not vid:
        return None
    try:
        votes = request_json(f"votacoes/{vid}/votos").get("dados") or []
    except Exception:
        return None

    filtered = [vote for vote in votes if deputy_id(vote) in selected_ids]
    if len(filtered) < MIN_SELECTED_VOTES:
        return None

    try:
        detail = request_json(f"votacoes/{vid}").get("dados") or item
    except Exception:
        detail = item
    try:
        orientations = request_json(f"votacoes/{vid}/orientacoes").get("dados") or []
    except Exception:
        orientations = []

    obj = detail.get("proposicaoObjeto")
    prop_id = obj.get("id") if isinstance(obj, dict) else None
    try:
        prop_id = int(prop_id) if prop_id is not None else None
    except (TypeError, ValueError):
        prop_id = None

    return {
        "dados": detail,
        "votos": filtered,
        "orientacoes": orientations,
        "proposicao_objeto_id": prop_id,
    }


def choose_year(year: int, selected_ids: set[int], errors: list[str]) -> list[dict]:
    listing: list[dict] = []
    for start, end in month_windows(year):
        rows = list_month(year, start, end, errors)
        print(f"{year}-{start.month:02d}: {len(rows)} votacoes listadas", flush=True)
        listing.extend(rows)

    unique: dict[str, dict] = {}
    for item in listing:
        vid = voting_id(item)
        if vid:
            unique[vid] = item
    rows = sorted(unique.values(), key=lambda item: (voting_stamp(item), voting_id(item)))
    if not rows:
        return []

    candidates = spread_candidates(rows, MAX_CANDIDATES_PER_YEAR)
    accepted: list[dict] = []

    for start in range(0, len(candidates), 8):
        if len(accepted) >= PER_YEAR:
            break
        chunk = candidates[start:start + 8]
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(fetch_candidate, item, selected_ids): item
                for item in chunk
            }
            batch: list[dict] = []
            for future in as_completed(futures):
                item = futures[future]
                try:
                    result = future.result()
                except Exception as exc:
                    errors.append(f"votacao/{voting_id(item)}: {exc}")
                    result = None
                if result is not None:
                    batch.append(result)

        batch.sort(
            key=lambda item: (
                voting_stamp(item.get("dados") or {}),
                voting_id(item.get("dados") or {}),
            )
        )
        for result in batch:
            if len(accepted) >= PER_YEAR:
                break
            accepted.append(result)

    accepted.sort(
        key=lambda item: (
            voting_stamp(item.get("dados") or {}),
            voting_id(item.get("dados") or {}),
        )
    )
    print(
        f"{year}: {len(accepted)} votacoes aceitas de {len(rows)} listadas "
        f"({len(candidates)} candidatas consultadas no maximo)",
        flush=True,
    )
    return accepted[:PER_YEAR]


def proposition_bundle(prop_id: int) -> tuple[int, dict | None]:
    try:
        detail = request_json(f"proposicoes/{prop_id}").get("dados") or {"id": prop_id}
        authors = request_json(f"proposicoes/{prop_id}/autores").get("dados") or []
        themes = request_json(f"proposicoes/{prop_id}/temas").get("dados") or []
        return prop_id, {"dados": detail, "autores": authors, "temas": themes}
    except Exception:
        return prop_id, None


def build(deputy_file: Path) -> dict:
    deputies_payload = json.loads(deputy_file.read_text(encoding="utf-8"))
    deputies = deputies_payload.get("dados") or []
    ids = {int(item["id"]) for item in deputies}
    if len(deputies) != 100 or len(ids) != 100:
        raise RuntimeError("O snapshot de deputados precisa conter 100 IDs distintos.")

    errors: list[str] = []
    votings: list[dict] = []
    for year in YEARS:
        if year <= date.today().year:
            votings.extend(choose_year(year, ids, errors))

    proposition_ids = sorted({
        int(bundle["proposicao_objeto_id"])
        for bundle in votings
        if bundle.get("proposicao_objeto_id") is not None
    })
    propositions: dict[int, dict] = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(proposition_bundle, prop_id): prop_id for prop_id in proposition_ids}
        for future in as_completed(futures):
            prop_id, bundle = future.result()
            if bundle is not None:
                propositions[prop_id] = bundle

    retrieved = datetime.now(timezone.utc).isoformat()
    return {
        "_meta": {
            "source": "Camara dos Deputados — Dados Abertos API v2",
            "source_url": API,
            "source_documentation": "https://dadosabertos.camara.leg.br/swagger/api.html",
            "retrieved_at": retrieved,
            "legislatura": 57,
            "period": {"from": "2023-02-01", "to": date.today().isoformat()},
            "deputy_count": 100,
            "voting_count": len(votings),
            "vote_count": sum(len(item.get("votos") or []) for item in votings),
            "proposition_count": len(propositions),
            "theme_relation_count": sum(len(item.get("temas") or []) for item in propositions.values()),
            "author_relation_count": sum(len(item.get("autores") or []) for item in propositions.values()),
            "years": sorted({
                int((voting_stamp(item.get("dados") or {}) or "0000")[:4])
                for item in votings
                if (voting_stamp(item.get("dados") or {}) or "")[:4].isdigit()
            }),
            "deputy_selection": deputies_payload.get("_meta", {}).get("selection"),
            "voting_selection": (
                "Ate 15 votacoes por ano, distribuidas temporalmente entre as "
                "votacoes retornadas em janelas mensais. Uma votacao entra apenas "
                "quando ha pelo menos cinco votos individuais entre os 100 perfis. "
                "Nao ha selecao por partido, parlamentar, tema, resultado ou sentido do voto."
            ),
            "errors": errors[:100],
            "limitations": (
                "Amostra de desenvolvimento, nao representativa de todas as votacoes "
                "da 57a Legislatura. Ausencia de registro individual nao equivale a voto Nao. "
                "O vinculo com proposicao depende do objeto informado no detalhe da votacao."
            ),
        },
        "deputados": deputies,
        "proposicoes": [propositions[key] for key in sorted(propositions)],
        "votacoes": votings,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deputados", default="backend/app/data/deputados_offline_100.json")
    parser.add_argument("--output", default="backend/app/data/base57_showcase.json.gz")
    args = parser.parse_args()

    data = build(Path(args.deputados))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(output, "wt", encoding="utf-8", compresslevel=9) as handle:
        json.dump(data, handle, ensure_ascii=False, separators=(",", ":"))

    print(json.dumps(data["_meta"], ensure_ascii=False, indent=2), flush=True)
    print(f"Snapshot salvo em {output}: {output.stat().st_size / 1024:.1f} KiB", flush=True)


if __name__ == "__main__":
    main()
