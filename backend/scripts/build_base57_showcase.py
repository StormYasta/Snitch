#!/usr/bin/env python3
"""Gera uma base offline factual e neutra da 57ª Legislatura.

Estratégia:
- usa o snapshot oficial de 100 deputados já versionado;
- baixa apenas os arquivos anuais *pequenos* de votações/objetos;
- distribui candidatos ao longo do ano por faixas temporais;
- consulta /votacoes/{id}/votos somente para candidatos necessários;
- seleciona até 20 votações por ano que tenham >= 5 votos dos 100 perfis;
- enriquece proposições-objeto com temas/autores quando a fonte permite.

A seleção não usa partido, deputado, tema, resultado nem conteúdo do voto.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API = "https://dadosabertos.camara.leg.br/api/v2"
FILES = "https://dadosabertos.camara.leg.br/arquivos"
USER_AGENT = "Snitch-ObservatorioLegislativo/1.0 (+https://github.com/StormYasta/Snitch)"
YEARS = (2023, 2024, 2025, 2026)
PER_YEAR = 20
MIN_SELECTED_VOTES = 5
MAX_VOTE_LOOKUPS_PER_YEAR = 120


def request(url: str, attempts: int = 5):
    last_error = None
    for attempt in range(attempts):
        try:
            return urlopen(
                Request(url, headers={"Accept": "*/*", "User-Agent": USER_AGENT}),
                timeout=45,
            )
        except HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                detail = ""
            last_error = RuntimeError(f"HTTP {exc.code}: {detail}")
        except Exception as exc:
            last_error = exc
        if attempt + 1 < attempts:
            time.sleep(min(10, 2 ** attempt))
    raise RuntimeError(f"Falha ao consultar {url}: {last_error}")


def get_json(url: str) -> dict:
    with request(url) as response:
        return json.loads(response.read().decode("utf-8"))


def api(path: str) -> dict:
    return get_json(f"{API}/{path.lstrip('/')}")


def download_csv(dataset: str, year: int, optional: bool = False) -> list[dict[str, str]]:
    url = f"{FILES}/{dataset}/csv/{dataset}-{year}.csv"
    try:
        print(f"Baixando {url}", flush=True)
        with request(url) as response:
            text = io.TextIOWrapper(
                response, encoding="utf-8-sig", errors="replace", newline=""
            )
            rows = list(csv.DictReader(text, delimiter=";"))
        if not rows and not optional:
            raise RuntimeError(f"Arquivo oficial vazio: {url}")
        if rows:
            print(
                f"{dataset}/{year}: {len(rows)} linhas; "
                f"colunas={list(rows[0].keys())[:10]}",
                flush=True,
            )
        return rows
    except Exception:
        if optional:
            return []
        raise


def field(row: dict, *names: str) -> str | None:
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return None


def as_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(float(value.replace(",", ".")))
    except (ValueError, TypeError):
        return None


def as_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    text = value.strip().lower()
    if text in {"1", "true", "sim", "yes"}:
        return True
    if text in {"0", "false", "não", "nao", "no"}:
        return False
    return None


def deputy_id(vote: dict) -> int | None:
    info = vote.get("deputado_") or vote.get("deputado") or {}
    return as_int(str(info.get("id"))) if info.get("id") is not None else None


def voting_id(row: dict) -> str | None:
    return field(row, "id", "idVotacao", "votacao_id")


def voting_date(row: dict) -> str:
    return field(row, "dataHoraRegistro", "data", "dataHoraVoto") or ""


def raw_voting(row: dict) -> dict:
    return {
        "id": voting_id(row),
        "uri": field(row, "uri", "uriVotacao"),
        "data": field(row, "data"),
        "dataHoraRegistro": field(row, "dataHoraRegistro"),
        "idOrgao": as_int(field(row, "idOrgao")),
        "siglaOrgao": field(row, "siglaOrgao"),
        "idEvento": as_int(field(row, "idEvento")),
        "descricao": field(row, "descricao") or "Votação registrada pela Câmara",
        "aprovacao": as_bool(field(row, "aprovacao")),
        "placarSim": as_int(field(row, "votosSim", "placarSim")) or 0,
        "placarNao": as_int(field(row, "votosNao", "placarNao")) or 0,
        "placarAbstencao": as_int(field(row, "votosAbstencao", "placarAbstencao")) or 0,
        "placarObstrucao": as_int(field(row, "votosObstrucao", "placarObstrucao")) or 0,
    }


def candidate_order(rows: list[dict], buckets: int) -> list[int]:
    """Intercala faixas temporais para espalhar a amostra pelo ano."""
    result: list[int] = []
    for bucket in range(buckets):
        left = math.floor(bucket * len(rows) / buckets)
        right = max(left + 1, math.floor((bucket + 1) * len(rows) / buckets))
        center = (left + right - 1) // 2
        result.extend(
            sorted(range(left, right), key=lambda idx: (abs(idx - center), idx))
        )
    # evita índices repetidos em faixas degeneradas
    return list(dict.fromkeys(result))


def object_candidates(rows: list[dict]) -> dict[str, list[int]]:
    result: dict[str, list[int]] = {}
    for row in rows:
        vid = field(row, "idVotacao", "votacao_id")
        pid = as_int(field(row, "proposicao_id", "idProposicao", "proposicaoObjeto_id"))
        if vid and pid is not None:
            bucket = result.setdefault(vid, [])
            if pid not in bucket:
                bucket.append(pid)
    return result


def fetch_voting_bundle(
    row: dict,
    selected_ids: set[int],
    prop_candidates: dict[str, list[int]],
) -> dict | None:
    vid = voting_id(row)
    if not vid:
        return None
    try:
        votes = api(f"votacoes/{vid}/votos").get("dados") or []
    except Exception as exc:
        print(f"AVISO votos {vid}: {exc}", flush=True)
        return None

    sample_votes = [vote for vote in votes if deputy_id(vote) in selected_ids]
    if len(sample_votes) < MIN_SELECTED_VOTES:
        return None

    try:
        orientations = api(f"votacoes/{vid}/orientacoes").get("dados") or []
    except Exception:
        orientations = []

    # O arquivo votacoesObjetos pode trazer mais de um possível objeto.
    # Guardamos o primeiro ID apenas para a relação principal usada hoje pelo
    # schema, mas preservamos todos em metadata do bundle.
    candidates = prop_candidates.get(vid, [])
    return {
        "dados": raw_voting(row),
        "votos": sample_votes,
        "orientacoes": orientations,
        "proposicao_objeto_id": candidates[0] if candidates else None,
        "proposicoes_objeto_possiveis": candidates,
    }


def choose_year(year: int, selected_ids: set[int]) -> list[dict]:
    rows = download_csv("votacoes", year)
    rows = [row for row in rows if voting_id(row)]
    rows.sort(key=lambda row: (voting_date(row), voting_id(row) or ""))

    object_rows = download_csv("votacoesObjetos", year, optional=True)
    prop_candidates = object_candidates(object_rows)

    if not rows:
        return []

    # Testamos os centros das faixas primeiro; se alguma não tiver votação
    # nominal suficiente, seguimos pelas demais posições, sem usar conteúdo.
    order = candidate_order(rows, max(PER_YEAR, 1))
    selected: list[dict] = []
    looked_up = 0

    # Lotes pequenos preservam a fonte oficial e reduzem tempo de execução.
    for start in range(0, len(order), 8):
        if len(selected) >= PER_YEAR or looked_up >= MAX_VOTE_LOOKUPS_PER_YEAR:
            break
        indexes = order[start:start + 8]
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(
                    fetch_voting_bundle, rows[idx], selected_ids, prop_candidates
                ): idx
                for idx in indexes
            }
            batch: list[tuple[int, dict]] = []
            for future in as_completed(futures):
                looked_up += 1
                bundle = future.result()
                if bundle is not None:
                    batch.append((futures[future], bundle))
        # Reordena pelo índice temporal para tornar a seleção reprodutível.
        for _, bundle in sorted(batch, key=lambda item: item[0]):
            if len(selected) >= PER_YEAR:
                break
            selected.append(bundle)

    selected.sort(
        key=lambda bundle: (
            bundle["dados"].get("dataHoraRegistro")
            or bundle["dados"].get("data")
            or "",
            str(bundle["dados"].get("id") or ""),
        )
    )
    print(
        f"{year}: {len(selected)} votações selecionadas; "
        f"{looked_up} votações consultadas para votos.",
        flush=True,
    )
    return selected[:PER_YEAR]


def proposition_bundle(prop_id: int) -> tuple[int, dict | None]:
    try:
        detail = api(f"proposicoes/{prop_id}").get("dados") or {"id": prop_id}
        authors = api(f"proposicoes/{prop_id}/autores").get("dados") or []
        themes = api(f"proposicoes/{prop_id}/temas").get("dados") or []
        return prop_id, {"dados": detail, "autores": authors, "temas": themes}
    except Exception as exc:
        print(f"AVISO proposição {prop_id}: {exc}", flush=True)
        return prop_id, None


def build(deputy_file: Path) -> dict:
    deputies_payload = json.loads(deputy_file.read_text(encoding="utf-8"))
    deputies = deputies_payload.get("dados") or []
    ids = {int(item["id"]) for item in deputies}
    if len(deputies) != 100 or len(ids) != 100:
        raise RuntimeError("O snapshot de deputados precisa conter 100 IDs distintos.")

    votings: list[dict] = []
    for year in YEARS:
        if year <= date.today().year:
            votings.extend(choose_year(year, ids))

    prop_ids = sorted({
        int(pid)
        for voting in votings
        for pid in (voting.get("proposicoes_objeto_possiveis") or [])
    })
    props: dict[int, dict] = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(proposition_bundle, pid): pid for pid in prop_ids}
        for future in as_completed(futures):
            pid, bundle = future.result()
            if bundle is not None:
                props[pid] = bundle

    return {
        "_meta": {
            "source": "Câmara dos Deputados — Dados Abertos",
            "source_url": "https://dadosabertos.camara.leg.br",
            "source_documentation": "https://dadosabertos.camara.leg.br/swagger/api.html",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "legislatura": 57,
            "period": {"from": "2023-02-01", "to": date.today().isoformat()},
            "deputy_count": 100,
            "voting_count": len(votings),
            "vote_count": sum(len(item["votos"]) for item in votings),
            "proposition_count": len(props),
            "theme_relation_count": sum(len(item.get("temas") or []) for item in props.values()),
            "author_relation_count": sum(len(item.get("autores") or []) for item in props.values()),
            "years": sorted({
                int((item["dados"].get("dataHoraRegistro") or item["dados"].get("data") or "0000")[:4])
                for item in votings
                if (item["dados"].get("dataHoraRegistro") or item["dados"].get("data") or "")[:4].isdigit()
            }),
            "deputy_selection": deputies_payload.get("_meta", {}).get("selection"),
            "voting_selection": (
                "Até 20 votações por ano, espalhadas temporalmente. Uma votação só "
                "entra quando há pelo menos cinco votos individuais registrados entre "
                "os 100 perfis. Não há seleção por partido, parlamentar, tema, "
                "resultado ou posição do voto."
            ),
            "limitations": (
                "Amostra de desenvolvimento, não representativa do conjunto da 57ª "
                "Legislatura. O endpoint de votos não lista parlamentares sem registro "
                "individual naquela votação. A relação entre votação e proposição pode "
                "ser incompleta ou conter mais de um possível objeto na fonte oficial."
            ),
        },
        "deputados": deputies,
        "proposicoes": [props[key] for key in sorted(props)],
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
    print(
        f"Snapshot salvo em {output}: {output.stat().st_size / 1024:.1f} KiB.",
        flush=True,
    )


if __name__ == "__main__":
    main()
