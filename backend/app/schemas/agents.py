from enum import Enum
from typing import Dict, List
from pydantic import BaseModel, Field
from app.schemas.city import ResourceBundle, RiskLevel


class AllocationStrategy(str, Enum):
    POPULATION_PRIORITY = "population_priority"
    RISK_PRIORITY = "risk_priority"
    VULNERABILITY_PRIORITY = "vulnerability_priority"
    BALANCED_PRIORITY = "balanced_priority"


class ZoneRecommendation(BaseModel):
    zone_id: str
    zone_name: str
    urgency_score: float = Field(ge=0.0, le=100.0)
    risk_level: RiskLevel
    immediate_threats: List[str]
    recommended_action: str
    requested_resources: ResourceBundle
    rationale: str


class AgentAssessment(BaseModel):
    agent_id: str
    agent_name: str
    domain: str
    city_severity_index: float = Field(ge=0.0, le=100.0)
    critical_zone_ids: List[str]
    identified_constraints: List[str]
    zone_recommendations: List[ZoneRecommendation]
    executive_summary: str


class AgentConflictRecord(BaseModel):
    zone_id: str
    zone_name: str
    fire_urgency: float
    infra_urgency: float
    divergence_delta: float
    winning_domain: str
    arbitration_reason: str


class ZoneDecisionRecord(BaseModel):
    decision_id: str
    zone_id: str
    zone_name: str
    priority_rank: int
    priority_score: float
    risk_score: float
    selected_action: str
    recommended_bundle: ResourceBundle
    relevant_factors: Dict[str, float]
    reasoning: str
    alternative_considered: str
    rejection_reason: str


class MultiAgentCouncilReport(BaseModel):
    strategy: AllocationStrategy
    fire_emergency_assessment: AgentAssessment
    infrastructure_assessment: AgentAssessment
    detected_conflicts: List[AgentConflictRecord]
    authority_directives: List[ZoneDecisionRecord]
    city_wide_summary: str
    strategy_tradeoff_explanation: str
