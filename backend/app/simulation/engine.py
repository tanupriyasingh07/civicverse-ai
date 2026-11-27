import uuid
from datetime import datetime, timezone
from math import sin, pi
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.agents.city_authority import CityAuthorityAgent
from app.allocation.allocator import allocate_constrained_resources
from app.evaluation.metrics import (
    SimulationMetrics,
    apply_intervention_effects,
    evaluate_simulation_outcomes,
)
from app.scenarios.heatwave import HeatwaveScenarioConfig, apply_heatwave_conditions
from app.schemas.agents import AllocationStrategy, MultiAgentCouncilReport
from app.schemas.city import CityState, ResourceBundle, RiskLevel
from app.simulation.city_generator import create_default_city
from app.simulation.risk_engine import classify_risk_level, evaluate_city_risk


class SimulationTimelineEvent(BaseModel):
    step: int
    phase: str
    title: str
    detail: str


class SimulationTickSnapshot(BaseModel):
    tick_index: int
    hour: int
    avg_risk: float
    max_temp_c: float
    critical_zone_count: int
    protected_population: int
    avg_water_availability_pct: float


class WhatIfModifications(BaseModel):
    label: str = "Alternative Policy / Inventory Scenario"
    inventory_multiplier: float = Field(default=1.0, ge=0.0, le=3.0)
    temperature_offset_c: float = Field(default=0.0, ge=-8.0, le=8.0)
    water_scarcity_offset: float = Field(default=0.0, ge=-0.4, le=0.4)
    grid_stress_offset: float = Field(default=0.0, ge=-0.4, le=0.4)
    disable_asset_id: Optional[str] = None
    override_strategy: Optional[AllocationStrategy] = None


class CounterfactualComparisonReport(BaseModel):
    baseline: "SimulationResult"
    alternative: "SimulationResult"
    modifications: WhatIfModifications
    risk_reduction_delta: float
    final_risk_delta: float
    protected_pop_delta: int
    fairness_delta: float
    vuln_equity_delta: float
    cost_delta_lakhs: float
    tradeoff_verdict: str


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
    temporal_trajectory: List[SimulationTickSnapshot] = Field(default_factory=list)


class StrategyComparisonReport(BaseModel):
    scenario: HeatwaveScenarioConfig
    results_by_strategy: Dict[str, SimulationResult]
    recommended_strategy: AllocationStrategy
    comparison_summary: str


class SimulationEngine:
    def __init__(self) -> None:
        self.authority_agent = CityAuthorityAgent()

    def _build_temporal_trajectory(
        self,
        crisis_city: CityState,
        final_city: CityState,
        duration_hours: int,
    ) -> List[SimulationTickSnapshot]:
        step_hours = 6
        total_steps = max(2, duration_hours // step_hours)
        snapshots: List[SimulationTickSnapshot] = []

        pre_zones = {z.zone_id: z for z in crisis_city.zones}
        post_zones = {z.zone_id: z for z in final_city.zones}

        for idx in range(total_steps + 1):
            hour = idx * step_hours
            progress = idx / total_steps
            # Diurnal thermal wave peaks mid-horizon before intervention cooling dampens it
            diurnal_pulse = sin(progress * pi) * 1.15
            # Deployment ramp begins after tick 1 (hour 6)
            relief_factor = 0.0 if idx == 0 else min(1.0, (progress ** 0.85))

            step_risks: List[float] = []
            step_temps: List[float] = []
            step_waters: List[float] = []
            crit_count = 0
            protected_est = 0

            for z_id, pre_z in pre_zones.items():
                post_z = post_zones[z_id]
                interp_risk = pre_z.risk_score + (post_z.risk_score - pre_z.risk_score) * relief_factor
                interp_risk = round(max(5.0, min(100.0, interp_risk + (diurnal_pulse * (1.0 - relief_factor)))), 2)
                interp_temp = round(
                    pre_z.ambient_temp_c + (post_z.ambient_temp_c - pre_z.ambient_temp_c) * relief_factor + (diurnal_pulse * 0.6),
                    2,
                )
                interp_water = pre_z.water_availability + (post_z.water_availability - pre_z.water_availability) * relief_factor

                step_risks.append(interp_risk)
                step_temps.append(interp_temp)
                step_waters.append(interp_water)
                if classify_risk_level(interp_risk) == RiskLevel.CRITICAL:
                    crit_count += 1

                fulfillment = max(0.0, 1.0 - post_z.unmet_demand_ratio) * relief_factor
                protected_est += int(post_z.population * fulfillment * (0.65 + 0.35 * (1.0 - interp_risk / 100.0)))

            snapshots.append(
                SimulationTickSnapshot(
                    tick_index=idx,
                    hour=hour,
                    avg_risk=round(sum(step_risks) / max(1, len(step_risks)), 2),
                    max_temp_c=max(step_temps, default=0.0),
                    critical_zone_count=crit_count,
                    protected_population=protected_est,
                    avg_water_availability_pct=round((sum(step_waters) / max(1, len(step_waters))) * 100.0, 1),
                )
            )
        return snapshots

    def run_simulation(
        self,
        scenario: HeatwaveScenarioConfig | None = None,
        strategy: AllocationStrategy = AllocationStrategy.BALANCED_PRIORITY,
        simulation_id: str | None = None,
        inventory_multiplier: float = 1.0,
        disable_asset_id: str | None = None,
    ) -> SimulationResult:
        cfg = scenario or HeatwaveScenarioConfig()
        sim_id = simulation_id or f"SIM-{uuid.uuid4().hex[:10].upper()}"
        events: List[SimulationTimelineEvent] = []

        base_city = create_default_city()

        # Optional inventory scaling for what-if capacity analysis
        if inventory_multiplier != 1.0:
            res = base_city.available_resources
            base_city.available_resources = ResourceBundle(
                water_tankers=max(0, int(round(res.water_tankers * inventory_multiplier))),
                medical_units=max(0, int(round(res.medical_units * inventory_multiplier))),
                cooling_units=max(0, int(round(res.cooling_units * inventory_multiplier))),
                emergency_personnel=max(0, int(round(res.emergency_personnel * inventory_multiplier))),
                shelter_capacity=max(0, int(round(res.shelter_capacity * inventory_multiplier))),
            )

        # Optional cascading infrastructure asset outage injection
        if disable_asset_id:
            for asset in base_city.infrastructure:
                if asset.asset_id == disable_asset_id:
                    asset.operational = False
                    asset.condition_score = 0.25
                    for z in base_city.zones:
                        if z.zone_id == asset.zone_id:
                            z.infrastructure_condition = round(max(0.15, z.infrastructure_condition - 0.30), 3)
                            z.hospital_accessibility = round(max(0.15, z.hospital_accessibility - 0.20), 3)

        events.append(
            SimulationTimelineEvent(
                step=1,
                phase="INITIALIZATION",
                title="Digital Twin Loaded",
                detail=f"Loaded {base_city.city_name} with {len(base_city.zones)} zones ({base_city.total_population:,} residents).",
            )
        )

        stressed_city = apply_heatwave_conditions(base_city, cfg)
        crisis_city = evaluate_city_risk(stressed_city)
        events.append(
            SimulationTimelineEvent(
                step=2,
                phase="CRISIS_ASSESSMENT",
                title="Heatwave Impact & Risk Computed",
                detail=f"Applied {cfg.base_temperature_c}?C heatwave ({cfg.duration_hours}h). City mean risk: {crisis_city.average_risk_score}/100.",
            )
        )

        council_report = self.authority_agent.deliberate(crisis_city, strategy=strategy)
        events.append(
            SimulationTimelineEvent(
                step=3,
                phase="MULTI_AGENT_COUNCIL",
                title="Agent Council Deliberation Complete",
                detail=council_report.city_wide_summary,
            )
        )

        allocated_city, unallocated, _, alloc_notes = allocate_constrained_resources(
            crisis_city, council_report.authority_directives, strategy
        )
        note_suffix = f" ({alloc_notes[0]})" if alloc_notes else ""
        events.append(
            SimulationTimelineEvent(
                step=4,
                phase="RESOURCE_ALLOCATION",
                title="Constrained Resource Dispatch",
                detail=f"Dispatched emergency units under '{strategy.value}' respecting finite inventory & safety floors.{note_suffix}",
            )
        )

        final_city = apply_intervention_effects(allocated_city)
        metrics = evaluate_simulation_outcomes(crisis_city, final_city, unallocated)
        trajectory = self._build_temporal_trajectory(crisis_city, final_city, cfg.duration_hours)

        events.append(
            SimulationTimelineEvent(
                step=5,
                phase="OUTCOME_EVALUATION",
                title="Post-Intervention Impact Evaluated",
                detail=(
                    f"Risk reduced by {metrics.risk_reduction_pct}% "
                    f"({metrics.initial_avg_risk} -> {metrics.final_avg_risk}) across {len(trajectory)-1} 6h intervals; "
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
            temporal_trajectory=trajectory,
        )

    def run_what_if(
        self,
        base_scenario: HeatwaveScenarioConfig,
        base_strategy: AllocationStrategy,
        modifications: WhatIfModifications,
    ) -> CounterfactualComparisonReport:
        baseline = self.run_simulation(scenario=base_scenario, strategy=base_strategy)

        alt_scenario = base_scenario.model_copy(
            update={
                "base_temperature_c": round(min(56.0, max(35.0, base_scenario.base_temperature_c + modifications.temperature_offset_c)), 2),
                "water_scarcity_factor": round(min(0.95, max(0.0, base_scenario.water_scarcity_factor + modifications.water_scarcity_offset)), 3),
                "grid_stress_factor": round(min(0.95, max(0.0, base_scenario.grid_stress_factor + modifications.grid_stress_offset)), 3),
            }
        )
        alt_strategy = modifications.override_strategy or base_strategy
        alternative = self.run_simulation(
            scenario=alt_scenario,
            strategy=alt_strategy,
            inventory_multiplier=modifications.inventory_multiplier,
            disable_asset_id=modifications.disable_asset_id,
        )

        risk_red_delta = round(alternative.metrics.risk_reduction_pct - baseline.metrics.risk_reduction_pct, 2)
        final_risk_delta = round(alternative.metrics.final_avg_risk - baseline.metrics.final_avg_risk, 2)
        pop_delta = alternative.metrics.population_protected - baseline.metrics.population_protected
        fair_delta = round(alternative.metrics.allocation_fairness_jain - baseline.metrics.allocation_fairness_jain, 4)
        vuln_delta = round(
            alternative.metrics.vulnerability_outcome_equity - baseline.metrics.vulnerability_outcome_equity, 4
        )
        cost_delta = round(alternative.metrics.estimated_cost_inr_lakhs - baseline.metrics.estimated_cost_inr_lakhs, 2)

        direction = "improves" if final_risk_delta < 0 else "worsens"
        verdict = (
            f"'{modifications.label}' {direction} residual city risk by {final_risk_delta:+.2f} pts "
            f"({pop_delta:+,} protected residents, vulnerability equity {vuln_delta:+.4f}, cost {cost_delta:+.2f}L INR)."
        )

        return CounterfactualComparisonReport(
            baseline=baseline,
            alternative=alternative,
            modifications=modifications,
            risk_reduction_delta=risk_red_delta,
            final_risk_delta=final_risk_delta,
            protected_pop_delta=pop_delta,
            fairness_delta=fair_delta,
            vuln_equity_delta=vuln_delta,
            cost_delta_lakhs=cost_delta,
            tradeoff_verdict=verdict,
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
            f"Under {cfg.base_temperature_c}?C ({cfg.duration_hours}h), '{best_key}' achieved the highest "
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
