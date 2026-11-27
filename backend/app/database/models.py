from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text
from app.database.session import Base


class SimulationRunRecord(Base):
    __tablename__ = "simulation_runs"

    simulation_id = Column(String(64), primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    scenario_id = Column(String(64), nullable=False)
    scenario_name = Column(String(128), nullable=False)
    crisis_type = Column(String(64), nullable=False)
    strategy = Column(String(64), nullable=False)
    base_temperature_c = Column(Float, nullable=False)
    duration_hours = Column(Integer, nullable=False)
    initial_avg_risk = Column(Float, nullable=False)
    final_avg_risk = Column(Float, nullable=False)
    risk_reduction_pct = Column(Float, nullable=False)
    population_protected = Column(Integer, nullable=False)
    allocation_fairness_jain = Column(Float, nullable=False)
    composite_score = Column(Float, nullable=False)
    summary_text = Column(Text, nullable=False)
    full_payload = Column(JSON, nullable=False)
