from typing import List, Optional
from sqlalchemy.orm import Session
from app.database.models import SimulationRunRecord
from app.simulation.engine import SimulationResult


def save_simulation_result(db: Session, result: SimulationResult) -> SimulationRunRecord:
    payload = result.model_dump(mode="json")
    record = SimulationRunRecord(
        simulation_id=result.simulation_id,
        scenario_id=result.scenario.scenario_id,
        scenario_name=result.scenario.name,
        crisis_type=result.scenario.crisis_type,
        strategy=result.strategy.value,
        base_temperature_c=result.scenario.base_temperature_c,
        duration_hours=result.scenario.duration_hours,
        initial_avg_risk=result.metrics.initial_avg_risk,
        final_avg_risk=result.metrics.final_avg_risk,
        risk_reduction_pct=result.metrics.risk_reduction_pct,
        population_protected=result.metrics.population_protected,
        allocation_fairness_jain=result.metrics.allocation_fairness_jain,
        composite_score=result.metrics.composite_score,
        summary_text=result.council_report.city_wide_summary,
        full_payload=payload,
    )
    persisted = db.merge(record)
    db.commit()
    db.refresh(persisted)
    return persisted


def list_simulation_history(db: Session, limit: int = 25) -> List[dict]:
    rows = (
        db.query(SimulationRunRecord)
        .order_by(SimulationRunRecord.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "simulation_id": r.simulation_id,
            "created_at": r.created_at.isoformat() if r.created_at else "",
            "scenario_name": r.scenario_name,
            "strategy": r.strategy,
            "base_temperature_c": r.base_temperature_c,
            "duration_hours": r.duration_hours,
            "initial_avg_risk": r.initial_avg_risk,
            "final_avg_risk": r.final_avg_risk,
            "risk_reduction_pct": r.risk_reduction_pct,
            "population_protected": r.population_protected,
            "allocation_fairness_jain": r.allocation_fairness_jain,
            "composite_score": r.composite_score,
            "summary_text": r.summary_text,
        }
        for r in rows
    ]


def get_simulation_by_id(db: Session, simulation_id: str) -> Optional[SimulationResult]:
    row = (
        db.query(SimulationRunRecord)
        .filter(SimulationRunRecord.simulation_id == simulation_id)
        .first()
    )
    if not row:
        return None
    return SimulationResult.model_validate(row.full_payload)
