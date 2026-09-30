#!/usr/bin/env python3
"""Gera um snapshot offline de 100 deputados a partir da API oficial da Câmara."""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "https://dadosabertos.camara.leg.br/api/v2"
USER_AGENT = "Snitch-ObservatorioLegislativo/1.0 (+https://github.com/StormYasta/Snitch)"


def get_json(url: str, attempts: int = 4) -> dict:
    last_error = None
    for attempt in range(attempts):
        try:
            req = Request(
                url,
                headers={
                    "Accept": "application/json",
                    "User-Agent": USER_AGENT,
                },
            )
            with urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Falha ao consultar {url}: {last_error}")


def build(limit: int = 100, legislatura: int = 57) -> dict:
    # A listagem por legislatura pode repetir o mesmo parlamentar em mais de
    # um registro de exercício. Percorremos páginas e deduplicamos por ID
    # oficial antes de escolher os 100 primeiros nomes distintos.
    unique_items: list[dict] = []
    seen_ids: set[int] = set()
    page = 1
    source_urls: list[str] = []

    while len(unique_items) < limit and page <= 20:
        query = urlencode(
            {
                "idLegislatura": legislatura,
                "itens": 100,
                "pagina": page,
                "ordem": "ASC",
                "ordenarPor": "nome",
            }
        )
        listing_url = f"{API}/deputados?{query}"
        source_urls.append(listing_url)
        batch = get_json(listing_url).get("dados") or []
        if not batch:
            break

        for item in batch:
            dep_id = item.get("id")
            if dep_id is None or dep_id in seen_ids:
                continue
            seen_ids.add(dep_id)
            unique_items.append(item)
            if len(unique_items) == limit:
                break

        if len(batch) < 100:
            break
        page += 1

    if len(unique_items) != limit:
        raise RuntimeError(
            f"A API forneceu somente {len(unique_items)} IDs distintos; "
            f"eram esperados {limit}."
        )

    rows = []
    for index, item in enumerate(unique_items, start=1):
        dep_id = item["id"]
        detail = get_json(f"{API}/deputados/{dep_id}").get("dados") or {}
        if not detail:
            detail = item
        rows.append(detail)
        print(f"[{index:03d}/{limit}] {detail.get('nomeCivil') or detail.get('nome') or dep_id}")

    ids = [row.get("id") for row in rows]
    if len(set(ids)) != limit or any(value is None for value in ids):
        raise RuntimeError("O snapshot final contém IDs ausentes ou duplicados.")

    return {
        "_meta": {
            "source": source_urls,
            "source_documentation": "https://dadosabertos.camara.leg.br/swagger/api.html",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "legislatura": legislatura,
            "count": limit,
            "selection": (
                "Primeiros 100 parlamentares com IDs oficiais distintos retornados "
                "pela API da 57ª Legislatura, preservando a ordenação alfabética "
                "solicitada por ordenarPor=nome. É uma amostra de desenvolvimento, "
                "não uma amostra representativa."
            ),
        },
        "dados": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="backend/app/data/deputados_offline_100.json",
    )
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--legislatura", type=int, default=57)
    args = parser.parse_args()
    if args.limit != 100:
        raise SystemExit("Este snapshot deve conter exatamente 100 registros.")

    data = build(args.limit, args.legislatura)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Snapshot salvo em {output} ({len(data['dados'])} deputados).")


if __name__ == "__main__":
    main()
