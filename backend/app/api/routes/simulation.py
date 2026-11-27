import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.history.repository import (
    get_simulation_by_id,
    list_simulation_history,
    save_simulation_result,
)
from app.scenarios.heatwave import HeatwaveScenarioConfig
from app.schemas.agents import AllocationStrategy
from app.services.cache import cache_service
from app.simulation.city_generator import create_default_city
from app.simulation.engine import (
    CounterfactualComparisonReport,
    SimulationEngine,
    SimulationResult,
    StrategyComparisonReport,
    WhatIfModifications,
)

router = APIRouter()
ws_router = APIRouter()
engine = SimulationEngine()


class RunSimulationRequest(BaseModel):
    scenario: Optional[HeatwaveScenarioConfig] = None
    strategy: AllocationStrategy = AllocationStrategy.BALANCED_PRIORITY


class CompareStrategiesRequest(BaseModel):
    scenario: Optional[HeatwaveScenarioConfig] = None


class WhatIfRequest(BaseModel):
    scenario: Optional[HeatwaveScenarioConfig] = None
    strategy: AllocationStrategy = AllocationStrategy.BALANCED_PRIORITY
    modifications: WhatIfModifications


@router.get("/api/city")
def get_baseline_city():
    return create_default_city()


@router.get("/api/zones")
def get_city_zones():
    city = create_default_city()
    return {"city_id": city.city_id, "zones": city.zones}


@router.get("/api/zones/{zone_id}")
def get_single_zone(zone_id: str):
    city = create_default_city()
    for zone in city.zones:
        if zone.zone_id.lower() == zone_id.lower():
            return zone
    raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found")


@router.get("/api/scenarios")
def list_available_scenarios():
    return {
        "scenarios": [
            {
                "scenario_id": "heatwave_mvp_v1",
                "name": "Severe Urban Heatwave Crisis",
                "crisis_type": "urban_heatwave",
                "status": "active",
                "default_config": HeatwaveScenarioConfig().model_dump(),
            }
        ]
    }


@router.post("/api/simulations/run", response_model=SimulationResult)
def run_simulation(request: RunSimulationRequest, db: Session = Depends(get_db)):
    result = engine.run_simulation(scenario=request.scenario, strategy=request.strategy)
    save_simulation_result(db, result)
    cache_service.set_json(f"sim:{result.simulation_id}", result.model_dump(mode="json"))
    return result


@router.post("/api/simulations/what-if", response_model=CounterfactualComparisonReport)
def run_what_if_simulation(request: WhatIfRequest):
    cfg = request.scenario or HeatwaveScenarioConfig()
    return engine.run_what_if(
        base_scenario=cfg,
        base_strategy=request.strategy,
        modifications=request.modifications,
    )


@router.get("/api/simulations/history")
def get_simulation_history(limit: int = 25, db: Session = Depends(get_db)):
    return {"runs": list_simulation_history(db, limit=limit)}


@router.get("/api/simulations/{simulation_id}", response_model=SimulationResult)
def get_simulation_details(simulation_id: str, db: Session = Depends(get_db)):
    cached = cache_service.get_json(f"sim:{simulation_id}")
    if cached:
        return SimulationResult.model_validate(cached)

    record = get_simulation_by_id(db, simulation_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Simulation '{simulation_id}' not found")
    cache_service.set_json(f"sim:{simulation_id}", record.model_dump(mode="json"))
    return record


@router.get("/api/simulations/{simulation_id}/decisions")
def get_simulation_decisions(simulation_id: str, db: Session = Depends(get_db)):
    result = get_simulation_details(simulation_id, db)
    return result.council_report.authority_directives


@router.post("/api/simulations/compare", response_model=StrategyComparisonReport)
def compare_simulation_strategies(request: CompareStrategiesRequest, db: Session = Depends(get_db)):
    report = engine.compare_strategies(scenario=request.scenario)
    for sim_res in report.results_by_strategy.values():
        save_simulation_result(db, sim_res)
        cache_service.set_json(f"sim:{sim_res.simulation_id}", sim_res.model_dump(mode="json"))
    return report


@router.post("/api/simulations/{simulation_id}/replay")
def replay_simulation(simulation_id: str, db: Session = Depends(get_db)):
    result = get_simulation_details(simulation_id, db)
    return {
        "simulation_id": result.simulation_id,
        "scenario": result.scenario,
        "strategy": result.strategy,
        "timeline_events": result.timeline_events,
        "temporal_trajectory": result.temporal_trajectory,
        "metrics": result.metrics,
    }


@ws_router.websocket("/ws/simulation/{simulation_id}")
async def simulation_stream(websocket: WebSocket, simulation_id: str, db: Session = Depends(get_db)):
    await websocket.accept()
    try:
        result = get_simulation_details(simulation_id, db)
        for event in result.timeline_events:
            await websocket.send_json({"type": "timeline_event", "data": event.model_dump()})
            await asyncio.sleep(0.25)
        await websocket.send_json(
            {
                "type": "simulation_complete",
                "simulation_id": result.simulation_id,
                "metrics": result.metrics.model_dump(),
            }
        )
    except WebSocketDisconnect:
        pass
    finally:
        await websocket.close()
