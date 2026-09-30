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
    query = urlencode(
        {
            "idLegislatura": legislatura,
            "itens": limit,
            "ordem": "ASC",
            "ordenarPor": "nome",
        }
    )
    listing_url = f"{API}/deputados?{query}"
    listing = get_json(listing_url).get("dados") or []
    if len(listing) != limit:
        raise RuntimeError(
            f"A API retornou {len(listing)} registros; eram esperados {limit}."
        )

    rows = []
    for index, item in enumerate(listing, start=1):
        dep_id = item.get("id")
        if not dep_id:
            raise RuntimeError(f"Item {index} sem ID oficial.")
        detail = get_json(f"{API}/deputados/{dep_id}").get("dados") or {}
        if not detail:
            # O item da listagem ainda é um registro oficial válido e contém
            # os dados básicos usados na tela de deputados.
            detail = item
        rows.append(detail)
        print(f"[{index:03d}/{limit}] {detail.get('nomeCivil') or detail.get('nome') or dep_id}")

    ids = [row.get("id") for row in rows]
    if len(set(ids)) != limit or any(value is None for value in ids):
        raise RuntimeError("A seleção contém IDs ausentes ou duplicados.")

    return {
        "_meta": {
            "source": listing_url,
            "source_documentation": "https://dadosabertos.camara.leg.br/swagger/api.html",
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "legislatura": legislatura,
            "count": limit,
            "selection": (
                "Primeiros 100 registros retornados pela API oficial para a "
                "57ª Legislatura, em ordem alfabética pelo parâmetro ordenarPor=nome. "
                "É uma amostra de desenvolvimento, não uma amostra representativa."
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
