from fastapi.testclient import TestClient
from app.main import app
from app.scenarios.heatwave import HeatwaveScenarioConfig
from app.schemas.agents import AllocationStrategy
from app.simulation.engine import SimulationEngine, WhatIfModifications

client = TestClient(app)


def test_temporal_trajectory_progression_across_duration():
    engine = SimulationEngine()
    res = engine.run_simulation(
        scenario=HeatwaveScenarioConfig(base_temperature_c=47.0, duration_hours=48, random_seed=42),
        strategy=AllocationStrategy.BALANCED_PRIORITY,
    )
    # 48h / 6h = 8 steps -> 9 snapshots (hour 0 to hour 48)
    assert len(res.temporal_trajectory) == 9
    assert res.temporal_trajectory[0].hour == 0
    assert res.temporal_trajectory[-1].hour == 48
    assert res.temporal_trajectory[-1].avg_risk < res.temporal_trajectory[0].avg_risk


def test_counterfactual_what_if_inventory_and_outage():
    resp = client.post(
        "/api/simulations/what-if",
        json={
            "scenario": {"base_temperature_c": 46.5, "duration_hours": 48, "random_seed": 42},
            "strategy": "balanced_priority",
            "modifications": {
                "label": "+30% Fleet Capacity",
                "inventory_multiplier": 1.3,
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["final_risk_delta"] < 0
    assert data["protected_pop_delta"] > 0
    assert data["cost_delta_lakhs"] > 0
