#!/usr/bin/env python3
"""Gera uma base offline neutra da 57ª Legislatura usando arquivos anuais oficiais.

Arquivos de votação e votos são baixados em CSV, que é o formato recomendado
pela própria Câmara para processamento em lote. Somente os detalhes/temas das
proposições selecionadas são consultados pela API REST.
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


def request(url: str, attempts: int = 5):
    last_error = None
    for attempt in range(attempts):
        try:
            return urlopen(
                Request(url, headers={"Accept": "*/*", "User-Agent": USER_AGENT}),
                timeout=60,
            )
        except HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", errors="replace")[:800]
            except Exception:
                detail = ""
            last_error = RuntimeError(f"HTTP {exc.code}: {detail}")
        except Exception as exc:
            last_error = exc
        if attempt + 1 < attempts:
            time.sleep(min(15, 2 ** attempt))
    raise RuntimeError(f"Falha ao consultar {url}: {last_error}")


def get_json(url: str) -> dict:
    with request(url) as response:
        return json.loads(response.read().decode("utf-8"))


def api(path: str) -> dict:
    return get_json(f"{API}/{path.lstrip('/')}")


def download_csv(dataset: str, year: int) -> list[dict[str, str]]:
    url = f"{FILES}/{dataset}/csv/{dataset}-{year}.csv"
    print(f"Baixando {url}")
    with request(url) as response:
        text = io.TextIOWrapper(response, encoding="utf-8-sig", errors="replace", newline="")
        reader = csv.DictReader(text, delimiter=";")
        rows = list(reader)
    if not rows:
        raise RuntimeError(f"Arquivo oficial vazio: {url}")
    print(f"{dataset}/{year}: {len(rows)} linhas; colunas: {list(rows[0])[:12]}")
    return rows


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


def vote_deputy_id(row: dict) -> int | None:
    return as_int(field(row, "deputado_id", "deputado_.id", "idDeputado"))


def voting_id(row: dict) -> str | None:
    return field(row, "idVotacao", "votacao_id", "id")


def voting_date(row: dict) -> str:
    return field(row, "dataHoraRegistro", "data", "dataHoraVoto") or ""


def raw_vote(row: dict) -> dict:
    return {
        "tipoVoto": field(row, "voto", "tipoVoto") or "",
        "dataHoraVoto": field(row, "dataHoraVoto", "dataRegistroVoto"),
        "deputado_": {
            "id": vote_deputy_id(row),
            "uri": field(row, "deputado_uri", "deputado_.uri"),
            "nome": field(row, "deputado_nome", "deputado_.nome"),
            "siglaPartido": field(row, "deputado_siglaPartido", "deputado_.siglaPartido"),
            "uriPartido": field(row, "deputado_uriPartido", "deputado_.uriPartido"),
            "siglaUf": field(row, "deputado_siglaUf", "deputado_.siglaUf"),
            "idLegislatura": as_int(field(row, "deputado_idLegislatura", "deputado_.idLegislatura")),
            "urlFoto": field(row, "deputado_urlFoto", "deputado_.urlFoto"),
            "email": field(row, "deputado_email", "deputado_.email"),
        },
    }


def raw_voting(row: dict) -> dict:
    return {
        "id": field(row, "id", "idVotacao"),
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


def raw_orientation(row: dict) -> dict:
    return {
        "nomeBancada": field(row, "siglaPartidoBloco", "nomeBancada", "siglaBancada"),
        "siglaBancada": field(row, "siglaPartidoBloco", "siglaBancada"),
        "orientacaoVoto": field(row, "orientacaoVoto", "voto", "orientacao"),
    }


def candidate_indexes(length: int, buckets: int) -> list[list[int]]:
    result = []
    for bucket in range(buckets):
        left = math.floor(bucket * length / buckets)
        right = max(left + 1, math.floor((bucket + 1) * length / buckets))
        center = (left + right - 1) // 2
        result.append(sorted(range(left, right), key=lambda idx: (abs(idx - center), idx)))
    return result


def object_map(rows: list[dict]) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for row in rows:
        vid = field(row, "idVotacao", "votacao_id")
        pid = as_int(field(row, "proposicao_id", "idProposicao", "proposicaoObjeto_id"))
        if vid and pid is not None and vid not in mapping:
            mapping[vid] = pid
    return mapping


def choose_year(
    year: int,
    selected_ids: set[int],
) -> list[dict]:
    basic_rows = download_csv("votacoes", year)
    vote_rows = download_csv("votacoesVotos", year)

    by_voting: dict[str, list[dict]] = {}
    for row in vote_rows:
        dep_id = vote_deputy_id(row)
        vid = voting_id(row)
        if dep_id in selected_ids and vid:
            by_voting.setdefault(vid, []).append(row)

    eligible = [
        row for row in basic_rows
        if field(row, "id") in by_voting
        and len(by_voting[field(row, "id")]) >= MIN_SELECTED_VOTES
    ]
    eligible.sort(key=lambda row: (voting_date(row), field(row, "id") or ""))
    if not eligible:
        raise RuntimeError(f"Nenhuma votação com votos da amostra encontrada em {year}.")

    selected: list[dict] = []
    used: set[str] = set()
    for indexes in candidate_indexes(len(eligible), min(PER_YEAR, len(eligible))):
        for idx in indexes:
            row = eligible[idx]
            vid = field(row, "id")
            if not vid or vid in used:
                continue
            used.add(vid)
            selected.append({
                "dados": raw_voting(row),
                "votos": [raw_vote(item) for item in by_voting[vid]],
                "orientacoes": [],
                "proposicao_objeto_id": None,
            })
            break

    # Relações e orientações são conjuntos menores e enriquecem a tela.
    try:
        objects = object_map(download_csv("votacoesObjetos", year))
    except Exception as exc:
        print(f"AVISO: votacoesObjetos/{year} indisponível: {exc}")
        objects = {}
    try:
        orientation_rows = download_csv("votacoesOrientacoes", year)
        orientations: dict[str, list[dict]] = {}
        for row in orientation_rows:
            vid = field(row, "idVotacao", "votacao_id")
            if vid:
                orientations.setdefault(vid, []).append(raw_orientation(row))
    except Exception as exc:
        print(f"AVISO: votacoesOrientacoes/{year} indisponível: {exc}")
        orientations = {}

    for bundle in selected:
        vid = str(bundle["dados"]["id"])
        bundle["proposicao_objeto_id"] = objects.get(vid)
        bundle["orientacoes"] = [
            item for item in orientations.get(vid, [])
            if item.get("nomeBancada") and item.get("orientacaoVoto")
        ]

    print(
        f"{year}: {len(selected)} votações escolhidas entre {len(eligible)} "
        f"com registros dos 100 deputados."
    )
    return selected[:PER_YEAR]


def proposition_bundle(prop_id: int) -> tuple[int, dict | None]:
    try:
        detail = api(f"proposicoes/{prop_id}").get("dados") or {"id": prop_id}
        authors = api(f"proposicoes/{prop_id}/autores").get("dados") or []
        themes = api(f"proposicoes/{prop_id}/temas").get("dados") or []
        return prop_id, {"dados": detail, "autores": authors, "temas": themes}
    except Exception as exc:
        print(f"AVISO: proposição {prop_id} não enriquecida: {exc}")
        return prop_id, None


def build(deputy_file: Path) -> dict:
    deputies_payload = json.loads(deputy_file.read_text(encoding="utf-8"))
    deputies = deputies_payload.get("dados") or []
    if len(deputies) != 100 or len({int(item["id"]) for item in deputies}) != 100:
        raise RuntimeError("O snapshot de deputados precisa conter 100 IDs distintos.")
    ids = {int(item["id"]) for item in deputies}

    votings: list[dict] = []
    for year in YEARS:
        if year <= date.today().year:
            votings.extend(choose_year(year, ids))

    prop_ids = sorted({
        int(bundle["proposicao_objeto_id"])
        for bundle in votings
        if bundle.get("proposicao_objeto_id") is not None
    })
    props: dict[int, dict] = {}
    # Poucas conexões simultâneas para não pressionar a API oficial.
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(proposition_bundle, pid): pid for pid in prop_ids}
        for future in as_completed(futures):
            pid, bundle = future.result()
            if bundle is not None:
                props[pid] = bundle
                print(f"Proposição {pid}: detalhe, autores e temas")

    retrieved = datetime.now(timezone.utc).isoformat()
    return {
        "_meta": {
            "source": "Câmara dos Deputados — Dados Abertos",
            "source_url": "https://dadosabertos.camara.leg.br",
            "source_documentation": "https://dadosabertos.camara.leg.br/swagger/api.html",
            "retrieved_at": retrieved,
            "legislatura": 57,
            "period": {"from": "2023-02-01", "to": date.today().isoformat()},
            "deputy_count": 100,
            "voting_count": len(votings),
            "vote_count": sum(len(item["votos"]) for item in votings),
            "proposition_count": len(props),
            "years": sorted({
                int((item["dados"].get("dataHoraRegistro") or item["dados"].get("data") or "0000")[:4])
                for item in votings
                if (item["dados"].get("dataHoraRegistro") or item["dados"].get("data") or "")[:4].isdigit()
            }),
            "deputy_selection": deputies_payload.get("_meta", {}).get("selection"),
            "voting_selection": (
                "Até 20 votações por ano, distribuídas temporalmente entre as "
                "votações que possuem ao menos cinco registros individuais dos "
                "100 perfis. Sem seleção por partido, parlamentar, tema, resultado "
                "ou posição de voto."
            ),
            "limitations": (
                "Amostra de desenvolvimento; não representa todas as votações da "
                "57ª Legislatura. Ausentes não aparecem nos arquivos de votos. "
                "Relações votação-proposição podem ser incompletas na fonte oficial."
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
    print(json.dumps(data["_meta"], ensure_ascii=False, indent=2))
    print(f"Snapshot salvo em {output} ({output.stat().st_size / 1024:.1f} KiB).")


if __name__ == "__main__":
    main()
