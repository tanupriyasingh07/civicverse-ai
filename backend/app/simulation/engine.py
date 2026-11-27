import uuid
from datetime import datetime, timezone
from typing import Dict, List
from pydantic import BaseModel
from app.agents.city_authority import CityAuthorityAgent
from app.allocation.allocator import allocate_constrained_resources
from app.evaluation.metrics import (
    SimulationMetrics,
    apply_intervention_effects,
    evaluate_simulation_outcomes,
)
from app.scenarios.heatwave import HeatwaveScenarioConfig, apply_heatwave_conditions
from app.schemas.agents import AllocationStrategy, MultiAgentCouncilReport
from app.schemas.city import CityState, ResourceBundle
from app.simulation.city_generator import create_default_city
from app.simulation.risk_engine import evaluate_city_risk


class SimulationTimelineEvent(BaseModel):
    step: int
    phase: str
    title: str
    detail: str


class SimulationResult(BaseModel):
    simulation_id: str
    created_at: str
    scenario: HeatwaveScenarioConfig
    strategy: AllocationStrategy
    initial_crisis_city: CityState
    final_city: CityState
    unallocated_resources: ResourceBundle
    council_report: MultiAgentCouncilReport
    metrics: SimulationMetrics
    timeline_events: List[SimulationTimelineEvent]


class StrategyComparisonReport(BaseModel):
    scenario: HeatwaveScenarioConfig
    results_by_strategy: Dict[str, SimulationResult]
    recommended_strategy: AllocationStrategy
    comparison_summary: str


class SimulationEngine:
    def __init__(self) -> None:
        self.authority_agent = CityAuthorityAgent()

    def run_simulation(
        self,
        scenario: HeatwaveScenarioConfig | None = None,
        strategy: AllocationStrategy = AllocationStrategy.BALANCED_PRIORITY,
        simulation_id: str | None = None,
    ) -> SimulationResult:
        cfg = scenario or HeatwaveScenarioConfig()
        sim_id = simulation_id or f"SIM-{uuid.uuid4().hex[:10].upper()}"
        events: List[SimulationTimelineEvent] = []

        # 1. Load baseline city
        base_city = create_default_city()
        events.append(
            SimulationTimelineEvent(
                step=1,
                phase="INITIALIZATION",
                title="Digital Twin Loaded",
                detail=f"Loaded {base_city.city_name} with {len(base_city.zones)} zones ({base_city.total_population:,} residents).",
            )
        )

        # 2-4. Apply crisis & evaluate initial risk
        stressed_city = apply_heatwave_conditions(base_city, cfg)
        crisis_city = evaluate_city_risk(stressed_city)
        events.append(
            SimulationTimelineEvent(
                step=2,
                phase="CRISIS_ASSESSMENT",
                title="Heatwave Impact & Risk Computed",
                detail=f"Applied {cfg.base_temperature_c}°C heatwave ({cfg.duration_hours}h). City mean risk: {crisis_city.average_risk_score}/100.",
            )
        )

        # 5-7. Multi-agent analysis & City Authority deliberation
        council_report = self.authority_agent.deliberate(crisis_city, strategy=strategy)
        events.append(
            SimulationTimelineEvent(
                step=3,
                phase="MULTI_AGENT_COUNCIL",
                title="Agent Council Deliberation Complete",
                detail=council_report.city_wide_summary,
            )
        )

        # 8. Constrained resource allocation
        allocated_city, unallocated, _ = allocate_constrained_resources(
            crisis_city, council_report.authority_directives, strategy
        )
        events.append(
            SimulationTimelineEvent(
                step=4,
                phase="RESOURCE_ALLOCATION",
                title="Constrained Resource Dispatch",
                detail=f"Dispatched emergency units under '{strategy.value}' respecting finite inventory & safety floors.",
            )
        )

        # 9-11. Apply intervention effects & compute evaluation metrics
        final_city = apply_intervention_effects(allocated_city)
        metrics = evaluate_simulation_outcomes(crisis_city, final_city, unallocated)
        events.append(
            SimulationTimelineEvent(
                step=5,
                phase="OUTCOME_EVALUATION",
                title="Post-Intervention Impact Evaluated",
                detail=(
                    f"Risk reduced by {metrics.risk_reduction_pct}% "
                    f"({metrics.initial_avg_risk} -> {metrics.final_avg_risk}); "
                    f"composite score: {metrics.composite_score}/100."
                ),
            )
        )

        return SimulationResult(
            simulation_id=sim_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            scenario=cfg,
            strategy=strategy,
            initial_crisis_city=crisis_city,
            final_city=final_city,
            unallocated_resources=unallocated,
            council_report=council_report,
            metrics=metrics,
            timeline_events=events,
        )

    def compare_strategies(
        self,
        scenario: HeatwaveScenarioConfig | None = None,
        strategies: List[AllocationStrategy] | None = None,
    ) -> StrategyComparisonReport:
        cfg = scenario or HeatwaveScenarioConfig()
        target_strategies = strategies or list(AllocationStrategy)
        results: Dict[str, SimulationResult] = {}

        for strat in target_strategies:
            results[strat.value] = self.run_simulation(scenario=cfg, strategy=strat)

        best_key = max(results.keys(), key=lambda k: results[k].metrics.composite_score)
        best_res = results[best_key]

        summary = (
            f"Under {cfg.base_temperature_c}°C ({cfg.duration_hours}h), '{best_key}' achieved the highest "
            f"composite score ({best_res.metrics.composite_score}/100) with {best_res.metrics.risk_reduction_pct}% "
            f"risk reduction, {best_res.metrics.population_protected:,} residents protected, and "
            f"{best_res.metrics.allocation_fairness_jain} Jain fairness index."
        )

        return StrategyComparisonReport(
            scenario=cfg,
            results_by_strategy=results,
            recommended_strategy=AllocationStrategy(best_key),
            comparison_summary=summary,
        )
