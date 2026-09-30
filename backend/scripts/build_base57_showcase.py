#!/usr/bin/env python3
"""Monta um snapshot neutro e reproduzível da 57ª Legislatura.

Critério de seleção:
- os mesmos 100 deputados do snapshot offline já versionado;
- até 20 votações com registros individuais por ano (2023-2026);
- as votações são distribuídas temporalmente em 20 faixas por ano;
- dentro de cada faixa, usa-se a primeira votação com ao menos 5 votos
  registrados entre os 100 perfis selecionados;
- não há escolha por partido, deputado, tema, resultado ou posição do voto.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "https://dadosabertos.camara.leg.br/api/v2"
USER_AGENT = "Snitch-ObservatorioLegislativo/1.0 (+https://github.com/StormYasta/Snitch)"
YEARS = (2023, 2024, 2025, 2026)
PER_YEAR = 20
MIN_SELECTED_VOTES = 5


def get_json(url: str, attempts: int = 5) -> dict:
    last_error = None
    for attempt in range(attempts):
        try:
            request = Request(
                url,
                headers={"Accept": "application/json", "User-Agent": USER_AGENT},
            )
            with urlopen(request, timeout=35) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(min(12, 2 ** attempt))
    raise RuntimeError(f"Falha ao consultar {url}: {last_error}")


def api(path: str, params: dict | None = None) -> dict:
    url = f"{API}/{path.lstrip('/')}"
    if params:
        url += "?" + urlencode(params, doseq=True)
    return get_json(url)


def list_votings(year: int) -> list[dict]:
    end = min(date(year, 12, 31), date.today()).isoformat()
    page = 1
    rows: list[dict] = []
    while True:
        payload = api(
            "votacoes",
            {
                "dataInicio": f"{year}-01-01",
                "dataFim": end,
                "pagina": page,
                "itens": 100,
            },
        )
        batch = payload.get("dados") or []
        if not batch:
            break
        rows.extend(batch)
        links = payload.get("links") or []
        if not any(
            isinstance(link, dict) and (link.get("rel") or "").lower() == "next"
            for link in links
        ):
            break
        page += 1
        if page > 50:
            raise RuntimeError(f"Paginação inesperada em votações/{year}.")
    rows.sort(
        key=lambda item: (
            item.get("dataHoraRegistro") or item.get("data") or "",
            str(item.get("id") or ""),
        )
    )
    return rows


def deputy_id(vote: dict) -> int | None:
    info = vote.get("deputado_") or vote.get("deputado") or {}
    value = info.get("id")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def candidate_indexes(length: int, buckets: int) -> list[list[int]]:
    """Índices próximos do centro de cada faixa, sem viés temático."""
    result = []
    for bucket in range(buckets):
        left = math.floor(bucket * length / buckets)
        right = max(left + 1, math.floor((bucket + 1) * length / buckets))
        center = (left + right - 1) // 2
        order = sorted(range(left, right), key=lambda idx: (abs(idx - center), idx))
        result.append(order)
    return result


def pick_year(year: int, selected_ids: set[int]) -> list[dict]:
    listings = list_votings(year)
    if not listings:
        return []

    picked: list[dict] = []
    used: set[str] = set()
    vote_cache: dict[str, list[dict]] = {}

    def votes_for(voting_id: str) -> list[dict]:
        if voting_id not in vote_cache:
            raw = api(f"votacoes/{voting_id}/votos").get("dados") or []
            vote_cache[voting_id] = [
                vote for vote in raw if deputy_id(vote) in selected_ids
            ]
        return vote_cache[voting_id]

    for indexes in candidate_indexes(len(listings), PER_YEAR):
        chosen = None
        for idx in indexes:
            item = listings[idx]
            voting_id = str(item.get("id"))
            if not voting_id or voting_id in used:
                continue
            selected_votes = votes_for(voting_id)
            if len(selected_votes) >= MIN_SELECTED_VOTES:
                chosen = (item, selected_votes)
                break
        if chosen is None:
            continue

        item, selected_votes = chosen
        voting_id = str(item["id"])
        used.add(voting_id)
        detail = api(f"votacoes/{voting_id}").get("dados") or item
        orientations = api(f"votacoes/{voting_id}/orientacoes").get("dados") or []
        picked.append({
            "dados": detail,
            "votos": selected_votes,
            "orientacoes": orientations,
        })
        print(
            f"{year}: {len(picked):02d}/{PER_YEAR} votação {voting_id} "
            f"({len(selected_votes)} votos da amostra)"
        )

    # Se alguma faixa só tinha votações sem registros individuais, completa
    # percorrendo o ano inteiro na ordem temporal.
    if len(picked) < PER_YEAR:
        for item in listings:
            if len(picked) >= PER_YEAR:
                break
            voting_id = str(item.get("id"))
            if not voting_id or voting_id in used:
                continue
            selected_votes = votes_for(voting_id)
            if len(selected_votes) < MIN_SELECTED_VOTES:
                continue
            detail = api(f"votacoes/{voting_id}").get("dados") or item
            orientations = api(f"votacoes/{voting_id}/orientacoes").get("dados") or []
            picked.append({
                "dados": detail,
                "votos": selected_votes,
                "orientacoes": orientations,
            })
            used.add(voting_id)
            print(
                f"{year}: {len(picked):02d}/{PER_YEAR} votação {voting_id} "
                f"({len(selected_votes)} votos da amostra; complemento)"
            )

    picked.sort(
        key=lambda bundle: (
            bundle["dados"].get("dataHoraRegistro")
            or bundle["dados"].get("data")
            or "",
            str(bundle["dados"].get("id")),
        )
    )
    return picked[:PER_YEAR]


def proposition_bundle(prop_id: int) -> dict:
    detail = api(f"proposicoes/{prop_id}").get("dados") or {"id": prop_id}
    authors = api(f"proposicoes/{prop_id}/autores").get("dados") or []
    themes = api(f"proposicoes/{prop_id}/temas").get("dados") or []
    return {"dados": detail, "autores": authors, "temas": themes}


def build(deputy_file: Path) -> dict:
    deputies_payload = json.loads(deputy_file.read_text(encoding="utf-8"))
    deputies = deputies_payload.get("dados") or []
    if len(deputies) != 100:
        raise RuntimeError("O snapshot de deputados precisa conter exatamente 100 registros.")
    ids = {int(item["id"]) for item in deputies}
    if len(ids) != 100:
        raise RuntimeError("O snapshot de deputados contém IDs repetidos.")

    votings: list[dict] = []
    today_year = date.today().year
    for year in YEARS:
        if year > today_year:
            continue
        votings.extend(pick_year(year, ids))

    props: dict[int, dict] = {}
    for bundle in votings:
        obj = (bundle.get("dados") or {}).get("proposicaoObjeto")
        prop_id = obj.get("id") if isinstance(obj, dict) else None
        if prop_id is None:
            bundle["proposicao_objeto_id"] = None
            continue
        prop_id = int(prop_id)
        bundle["proposicao_objeto_id"] = prop_id
        if prop_id not in props:
            try:
                props[prop_id] = proposition_bundle(prop_id)
                print(f"Proposição {prop_id}: detalhe, autores e temas")
            except Exception as exc:
                print(f"AVISO: proposição {prop_id} não enriquecida: {exc}")

    return {
        "_meta": {
            "source": "Câmara dos Deputados — Dados Abertos API v2",
            "source_url": API,
            "source_documentation": "https://dadosabertos.camara.leg.br/swagger/api.html",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "legislatura": 57,
            "period": {
                "from": "2023-02-01",
                "to": date.today().isoformat(),
            },
            "deputy_count": len(deputies),
            "voting_count": len(votings),
            "proposition_count": len(props),
            "years": sorted({
                int((bundle["dados"].get("dataHoraRegistro") or "0000")[:4])
                for bundle in votings
                if (bundle["dados"].get("dataHoraRegistro") or "")[:4].isdigit()
            }),
            "deputy_selection": deputies_payload.get("_meta", {}).get("selection"),
            "voting_selection": (
                "Até 20 votações por ano, distribuídas em faixas temporais. "
                "Cada votação precisa ter ao menos cinco registros individuais "
                "entre os 100 deputados do snapshot. Não há seleção por partido, "
                "parlamentar, tema, resultado ou tipo de voto."
            ),
            "limitations": (
                "Amostra de desenvolvimento. Não representa todas as votações da "
                "57ª Legislatura nem deve ser usada para inferir posição ideológica."
            ),
        },
        "deputados": deputies,
        "proposicoes": list(props.values()),
        "votacoes": votings,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--deputados",
        default="backend/app/data/deputados_offline_100.json",
    )
    parser.add_argument(
        "--output",
        default="backend/app/data/base57_showcase.json.gz",
    )
    args = parser.parse_args()
    data = build(Path(args.deputados))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(output, "wt", encoding="utf-8", compresslevel=9) as handle:
        json.dump(data, handle, ensure_ascii=False, separators=(",", ":"))
    meta = data["_meta"]
    print(
        f"Snapshot salvo: {meta['deputy_count']} deputados, "
        f"{meta['voting_count']} votações, {meta['proposition_count']} proposições."
    )


if __name__ == "__main__":
    main()
