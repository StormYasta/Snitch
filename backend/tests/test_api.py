import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_deputados" in data
    assert "total_proposicoes" in data
    assert "total_votacoes" in data
    assert "total_votos" in data
    assert data["total_deputados"] > 0
    assert data["total_proposicoes"] > 0

def test_list_deputados():
    response = client.get("/api/deputados?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) > 0
    assert data["items"][0]["nome_parlamentar"] is not None

def test_deputado_detail_and_activity():
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

def test_list_proposicoes_and_detail():
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

def test_votacao_detail_and_votos():
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

def test_global_search():
    # Procura proposição
    res_prop = client.get("/api/busca?q=1234")
    assert res_prop.status_code == 200
    assert len(res_prop.json()["proposicoes"]) > 0

    # Procura deputado
    res_dep = client.get("/api/busca?q=Tabata")
    assert res_dep.status_code == 200
    assert len(res_dep.json()["deputados"]) > 0



def test_legislaturas_and_trajetoria():
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


def test_governo_structure_and_institution_detail():
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
