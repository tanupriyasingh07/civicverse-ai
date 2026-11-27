import asyncio
from typing import List, Optional
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
from app.schemas.agents import AllocationStrategy, ZoneDecisionRecord
from app.schemas.city import CityState, ZoneState
from app.services.cache import cache_service
from app.simulation.city_generator import create_default_city
from app.simulation.engine import (
    SimulationEngine,
    SimulationResult,
    StrategyComparisonReport,
)

router = APIRouter(prefix="/api", tags=["CivicVerse Simulation"])
engine = SimulationEngine()


class RunSimulationRequest(BaseModel):
    scenario: HeatwaveScenarioConfig = HeatwaveScenarioConfig()
    strategy: AllocationStrategy = AllocationStrategy.BALANCED_PRIORITY


class CompareStrategiesRequest(BaseModel):
    scenario: HeatwaveScenarioConfig = HeatwaveScenarioConfig()
    strategies: Optional[List[AllocationStrategy]] = None


@router.get("/city", response_model=CityState)
def get_city_baseline():
    return create_default_city()


@router.get("/zones", response_model=List[ZoneState])
def get_city_zones():
    return create_default_city().zones


@router.get("/zones/{zone_id}", response_model=ZoneState)
def get_zone_detail(zone_id: str):
    city = create_default_city()
    zone = next((z for z in city.zones if z.zone_id.upper() == zone_id.upper()), None)
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found")
    return zone


@router.get("/scenarios")
def list_available_scenarios():
    return [
        {
            "scenario_id": "heatwave_mvp_v1",
            "name": "Severe Urban Heatwave Crisis",
            "crisis_type": "urban_heatwave",
            "status": "active",
            "default_config": HeatwaveScenarioConfig().model_dump(),
        },
        {
            "scenario_id": "urban_flood_planned",
            "name": "Monsoon Flash Flood (Architecture Ready)",
            "crisis_type": "urban_flood",
            "status": "planned",
        },
    ]


@router.post("/simulations/run", response_model=SimulationResult)
def run_simulation(request: RunSimulationRequest, db: Session = Depends(get_db)):
    result = engine.run_simulation(scenario=request.scenario, strategy=request.strategy)
    save_simulation_result(db, result)
    cache_service.set_json(f"sim:{result.simulation_id}", result.model_dump(mode="json"))
    return result


@router.get("/simulations/history")
def fetch_simulation_history(limit: int = 25, db: Session = Depends(get_db)):
    return {"runs": list_simulation_history(db, limit=limit)}


@router.get("/simulations/{simulation_id}", response_model=SimulationResult)
def fetch_simulation(simulation_id: str, db: Session = Depends(get_db)):
    cached = cache_service.get_json(f"sim:{simulation_id}")
    if cached:
        return SimulationResult.model_validate(cached)
    result = get_simulation_by_id(db, simulation_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Simulation '{simulation_id}' not found")
    return result


@router.get("/simulations/{simulation_id}/decisions", response_model=List[ZoneDecisionRecord])
def fetch_simulation_decisions(simulation_id: str, db: Session = Depends(get_db)):
    result = fetch_simulation(simulation_id, db)
    return result.council_report.authority_directives


@router.post("/simulations/compare", response_model=StrategyComparisonReport)
def compare_strategies(request: CompareStrategiesRequest, db: Session = Depends(get_db)):
    comparison = engine.compare_strategies(
        scenario=request.scenario, strategies=request.strategies
    )
    for res in comparison.results_by_strategy.values():
        save_simulation_result(db, res)
    return comparison


@router.post("/simulations/{simulation_id}/replay")
def replay_simulation(simulation_id: str, db: Session = Depends(get_db)):
    result = fetch_simulation(simulation_id, db)
    return {
        "simulation_id": result.simulation_id,
        "scenario": result.scenario,
        "strategy": result.strategy,
        "timeline_events": result.timeline_events,
        "initial_crisis_city": result.initial_crisis_city,
        "final_city": result.final_city,
        "metrics": result.metrics,
    }


ws_router = APIRouter()


@ws_router.websocket("/ws/simulation/{simulation_id}")
async def simulation_replay_ws(websocket: WebSocket, simulation_id: str, db: Session = Depends(get_db)):
    await websocket.accept()
    try:
        result = get_simulation_by_id(db, simulation_id)
        if not result:
            await websocket.send_json({"type": "error", "message": "Simulation not found"})
            await websocket.close()
            return

        for event in result.timeline_events:
            await websocket.send_json({"type": "timeline_event", "data": event.model_dump()})
            await asyncio.sleep(0.35)

        await websocket.send_json({"type": "completed", "data": result.model_dump(mode="json")})
        await websocket.close()
    except WebSocketDisconnect:
        pass
