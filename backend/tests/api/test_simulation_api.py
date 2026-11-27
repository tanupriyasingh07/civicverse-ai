from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_city_and_zones_endpoints():
    city_resp = client.get("/api/city")
    assert city_resp.status_code == 200
    assert city_resp.json()["city_name"] == "Aurelia Metro"

    zone_resp = client.get("/api/zones/Z6")
    assert zone_resp.status_code == 200
    assert zone_resp.json()["zone_id"] == "Z6"


def test_run_persist_history_compare_and_replay_flow():
    run_resp = client.post(
        "/api/simulations/run",
        json={
            "scenario": {"base_temperature_c": 46.5, "duration_hours": 48, "random_seed": 42},
            "strategy": "balanced_priority",
        },
    )
    assert run_resp.status_code == 200
    sim_data = run_resp.json()
    sim_id = sim_data["simulation_id"]

    # Fetch persisted simulation & decisions
    get_resp = client.get(f"/api/simulations/{sim_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["simulation_id"] == sim_id

    dec_resp = client.get(f"/api/simulations/{sim_id}/decisions")
    assert dec_resp.status_code == 200
    assert len(dec_resp.json()) == 8

    # History check
    hist_resp = client.get("/api/simulations/history")
    assert hist_resp.status_code == 200
    assert any(r["simulation_id"] == sim_id for r in hist_resp.json()["runs"])

    # Replay check
    replay_resp = client.post(f"/api/simulations/{sim_id}/replay")
    assert replay_resp.status_code == 200
    assert len(replay_resp.json()["timeline_events"]) == 5

    # Compare all 4 strategies
    comp_resp = client.post(
        "/api/simulations/compare",
        json={"scenario": {"base_temperature_c": 46.5, "duration_hours": 48, "random_seed": 42}},
    )
    assert comp_resp.status_code == 200
    assert len(comp_resp.json()["results_by_strategy"]) == 4
