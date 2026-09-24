import os
os.environ["LOAD_DEMO_SEED"] = "true"

import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client

def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_stats(client):
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_deputados" in data
    assert "total_proposicoes" in data
    assert "total_votacoes" in data
    assert "total_votos" in data
    assert data["total_deputados"] > 0
    assert data["total_proposicoes"] > 0

def test_list_deputados(client):
    response = client.get("/api/deputados?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0
    assert data["items"][0]["nome_parlamentar"] is not None

def test_deputado_detail_and_activity(client):
    # Pega primeiro deputado
    deps = client.get("/api/deputados").json()["items"]
    dep_id = deps[0]["id"]

    # Detalhe
    detail_res = client.get(f"/api/deputados/{dep_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == dep_id
    assert "gabinete" in detail

    # Atividade
    ativ_res = client.get(f"/api/deputados/{dep_id}/atividade")
    assert ativ_res.status_code == 200
    ativ = ativ_res.json()
    assert "dias_com_atividade" in ativ
    assert "nota_metodologica" in ativ

    # Temporal
    temp_res = client.get(f"/api/deputados/{dep_id}/temporal?agrupamento=ano")
    assert temp_res.status_code == 200
    assert isinstance(temp_res.json(), list)

    # Distribuição de votos
    dist_res = client.get(f"/api/deputados/{dep_id}/distribuicao_votos")
    assert dist_res.status_code == 200

    # Histórico de votos
    votos_res = client.get(f"/api/deputados/{dep_id}/votos")
    assert votos_res.status_code == 200

def test_list_proposicoes_and_detail(client):
    response = client.get("/api/proposicoes")
    assert response.status_code == 200
    props = response.json()["items"]
    assert len(props) > 0

    prop_id = props[0]["id"]
    det_res = client.get(f"/api/proposicoes/{prop_id}")
    assert det_res.status_code == 200
    det = det_res.json()
    assert "autores" in det
    assert "tramitacoes" in det
    assert "votacoes" in det

def test_votacao_detail_and_votos(client):
    # Pega votações
    stats = client.get("/api/stats").json()
    vot_id = stats["votacoes_recentes"][0]["id"]

    det_res = client.get(f"/api/votacoes/{vot_id}")
    assert det_res.status_code == 200
    det = det_res.json()
    assert "orientacoes" in det

    votos_res = client.get(f"/api/votacoes/{vot_id}/votos")
    assert votos_res.status_code == 200
    votos_data = votos_res.json()
    assert "items" in votos_data
    assert len(votos_data["items"]) > 0

def test_global_search(client):
    # Procura proposição
    res_prop = client.get("/api/busca?q=1234")
    assert res_prop.status_code == 200
    assert len(res_prop.json()["proposicoes"]) > 0

    # Procura deputado
    res_dep = client.get("/api/busca?q=Tabata")
    assert res_dep.status_code == 200
    assert len(res_dep.json()["deputados"]) > 0



def test_legislaturas_and_trajetoria(client):
    legs_res = client.get("/api/legislaturas")
    assert legs_res.status_code == 200
    legs = legs_res.json()
    assert isinstance(legs, list)
    assert len(legs) > 0

    deps = client.get("/api/deputados?page=1&page_size=1").json()["items"]
    dep_id = deps[0]["id"]
    traj_res = client.get(f"/api/deputados/{dep_id}/trajetoria")
    assert traj_res.status_code == 200
    traj = traj_res.json()
    assert traj["deputado_id"] == dep_id
    assert "mandatos" in traj
    assert "timeline" in traj


def test_governo_structure_and_institution_detail(client):
    structure_res = client.get("/api/governo/estrutura")
    assert structure_res.status_code == 200
    structure = structure_res.json()
    assert len(structure["nodes"]) > 0
    assert "legenda" in structure

    search_res = client.get("/api/governo/busca?q=Câmara")
    assert search_res.status_code == 200
    results = search_res.json()
    assert len(results) > 0

    camara = next(
        (item for item in results if item.get("sigla") == "CD" or "Câmara dos Deputados" in item.get("nome", "")),
        results[0],
    )
    detail_res = client.get(f"/api/governo/instituicoes/{camara['id']}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert "relacoes" in detail
    if camara.get("sigla") == "CD":
        assert detail["integrado"] is True
        assert detail["estatisticas_camara"] is not None


def test_comparativo_validacao(client):
    deps = client.get("/api/deputados?page_size=3").json()["items"]
    first, second = deps[0]["id"], deps[1]["id"]
    assert client.get("/api/comparativo/deputados", params={"ids": str(first)}).status_code == 422
    assert client.get("/api/comparativo/deputados", params={"ids": f"{first},{first}"}).status_code == 422
    assert client.get("/api/comparativo/deputados", params={"ids": f"{first},{second},3,4"}).status_code == 422
    assert client.get("/api/comparativo/deputados", params={"ids": f"{first},99999999"}).status_code == 404


def test_comparativo_metricas_e_radar(client):
    deps = client.get("/api/deputados?page_size=3").json()["items"]
    ids = [deps[0]["id"], deps[1]["id"]]
    response = client.get("/api/comparativo/deputados", params={"ids": ",".join(map(str, ids)), "ano": 2025})
    assert response.status_code == 200, response.text
    data = response.json()
    assert [item["deputado"]["id"] for item in data["deputados"]] == ids
    assert data["ano"] == 2025
    assert "nota_metodologica" in data

    for item in data["deputados"]:
        counts = item["votos"]
        activity = item["atividade"]
        assert activity["votos_registrados"] == sum(counts.values())
        assert activity["votacoes_distintas"] <= activity["votos_registrados"]
        for tema in item["temas"]:
            assert tema["total_sim_nao"] == tema["sim"] + tema["nao"]
            assert tema["total_registrado"] == sum(tema[k] for k in ("sim","nao","abstencao","obstrucao","outros"))
            if tema["total_sim_nao"]:
                assert abs(tema["percentual_sim"] + tema["percentual_nao"] - 100) < 0.2
            else:
                assert tema["percentual_sim"] is None


def test_comparativo_votacoes_comuns(client):
    deps = client.get("/api/deputados?page_size=3").json()["items"]
    ids = [deps[0]["id"], deps[1]["id"]]
    res = client.get("/api/comparativo/votacoes", params={"ids": ",".join(map(str, ids)), "ano": 2025, "page_size": 2})
    assert res.status_code == 200, res.text
    payload = res.json()
    assert payload["page_size"] == 2
    assert payload["total_pages"] >= 1
    for votacao in payload["items"]:
        assert set(votacao["votos"]) == set(map(str, ids))
        assert all(value != "Sem registro" for value in votacao["votos"].values())
