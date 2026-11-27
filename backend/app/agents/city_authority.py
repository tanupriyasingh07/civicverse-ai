from typing import Dict, List, Tuple
from app.agents.fire_emergency import FireEmergencyAgent
from app.agents.infrastructure import InfrastructureAgent
from app.schemas.agents import (
    AgentConflictRecord,
    AllocationStrategy,
    MultiAgentCouncilReport,
    ZoneDecisionRecord,
)
from app.schemas.city import CityState, ResourceBundle, ZoneState


ALTERNATIVE_POLICY_MAP = {
    AllocationStrategy.BALANCED_PRIORITY: AllocationStrategy.RISK_PRIORITY,
    AllocationStrategy.RISK_PRIORITY: AllocationStrategy.VULNERABILITY_PRIORITY,
    AllocationStrategy.VULNERABILITY_PRIORITY: AllocationStrategy.POPULATION_PRIORITY,
    AllocationStrategy.POPULATION_PRIORITY: AllocationStrategy.BALANCED_PRIORITY,
}


class CityAuthorityAgent:
    """
    Consolidates Fire/Emergency and Infrastructure agent reports, arbitrates
    inter-agent priority conflicts, and computes counterfactual policy rank deltas.
    """

    def __init__(self) -> None:
        self.fire_agent = FireEmergencyAgent()
        self.infra_agent = InfrastructureAgent()

    def _compute_priority_score(
        self,
        zone: ZoneState,
        fire_urgency: float,
        infra_urgency: float,
        max_pop: int,
        strategy: AllocationStrategy,
    ) -> float:
        pop_norm = (zone.population / max(1, max_pop)) * 100.0
        vuln_norm = zone.vulnerability_index * 100.0

        if strategy == AllocationStrategy.POPULATION_PRIORITY:
            score = (0.55 * pop_norm) + (0.25 * zone.risk_score) + (0.10 * fire_urgency) + (0.10 * infra_urgency)
        elif strategy == AllocationStrategy.RISK_PRIORITY:
            score = (0.55 * zone.risk_score) + (0.25 * fire_urgency) + (0.15 * infra_urgency) + (0.05 * vuln_norm)
        elif strategy == AllocationStrategy.VULNERABILITY_PRIORITY:
            score = (0.50 * vuln_norm) + (0.25 * zone.risk_score) + (0.15 * fire_urgency) + (0.10 * pop_norm)
        else:
            score = (
                (0.35 * zone.risk_score)
                + (0.25 * vuln_norm)
                + (0.20 * ((fire_urgency + infra_urgency) / 2.0))
                + (0.20 * pop_norm)
            )
        return round(score, 2)

    def _strategy_explanation(self, strategy: AllocationStrategy) -> str:
        if strategy == AllocationStrategy.POPULATION_PRIORITY:
            return (
                "Prioritizes high-population districts to maximize absolute headcount coverage; "
                "trade-off: smaller, high-vulnerability pockets may experience delayed relief."
            )
        if strategy == AllocationStrategy.RISK_PRIORITY:
            return (
                "Targets zones with the highest composite hazard score first to suppress acute heat mortality; "
                "trade-off: moderate-risk zones with fragile grids receive residual capacity."
            )
        if strategy == AllocationStrategy.VULNERABILITY_PRIORITY:
            return (
                "Centers socio-economic vulnerability and elderly exposure to maximize outcome equity; "
                "trade-off: denser commercial hubs with lower vulnerability scores wait for secondary waves."
            )
        return (
            "Balances hazard severity (35%), vulnerability (25%), specialist urgency (20%), and population scale (20%) "
            "to avoid single-metric blind spots."
        )

    def deliberate(
        self,
        city: CityState,
        strategy: AllocationStrategy = AllocationStrategy.BALANCED_PRIORITY,
    ) -> MultiAgentCouncilReport:
        fire_report = self.fire_agent.assess(city)
        infra_report = self.infra_agent.assess(city)

        fire_by_zone = {r.zone_id: r for r in fire_report.zone_recommendations}
        infra_by_zone = {r.zone_id: r for r in infra_report.zone_recommendations}
        max_pop = max((z.population for z in city.zones), default=1)

        alt_strategy = ALTERNATIVE_POLICY_MAP[strategy]

        # Detect explicit inter-agent disagreements (divergence >= 12 urgency points)
        conflicts: List[AgentConflictRecord] = []
        for zone in city.zones:
            f_rec = fire_by_zone[zone.zone_id]
            i_rec = infra_by_zone[zone.zone_id]
            delta = round(abs(f_rec.urgency_score - i_rec.urgency_score), 2)
            if delta >= 12.0:
                if f_rec.urgency_score > i_rec.urgency_score:
                    winner = "Fire & Emergency"
                    reason = (
                        f"Life-safety & medical urgency ({f_rec.urgency_score}) exceeded utility stress ({i_rec.urgency_score}) "
                        f"by {delta} pts; prioritized immediate triage & hydration over grid stabilization."
                    )
                else:
                    winner = "Infrastructure & Utilities"
                    reason = (
                        f"Substation/water-grid stress ({i_rec.urgency_score}) exceeded triage urgency ({f_rec.urgency_score}) "
                        f"by {delta} pts; prioritized utility reinforcement to prevent cascading outage."
                    )
                conflicts.append(
                    AgentConflictRecord(
                        zone_id=zone.zone_id,
                        zone_name=zone.name,
                        fire_urgency=f_rec.urgency_score,
                        infra_urgency=i_rec.urgency_score,
                        divergence_delta=delta,
                        winning_domain=winner,
                        arbitration_reason=reason,
                    )
                )

        # Compute primary ranking and counterfactual alternative ranking
        scored_zones: List[Tuple[float, ZoneState]] = []
        alt_scores: Dict[str, float] = {}
        for zone in city.zones:
            f_rec = fire_by_zone[zone.zone_id]
            i_rec = infra_by_zone[zone.zone_id]
            p_score = self._compute_priority_score(zone, f_rec.urgency_score, i_rec.urgency_score, max_pop, strategy)
            a_score = self._compute_priority_score(zone, f_rec.urgency_score, i_rec.urgency_score, max_pop, alt_strategy)
            scored_zones.append((p_score, zone))
            alt_scores[zone.zone_id] = a_score

        scored_zones.sort(key=lambda item: (-item[0], item[1].zone_id))
        alt_ordered_ids = [
            z_id for z_id, _ in sorted(alt_scores.items(), key=lambda kv: (-kv[1], kv[0]))
        ]
        alt_rank_map = {z_id: idx for idx, z_id in enumerate(alt_ordered_ids, start=1)}

        directives: List[ZoneDecisionRecord] = []
        for rank, (p_score, zone) in enumerate(scored_zones, start=1):
            f_rec = fire_by_zone[zone.zone_id]
            i_rec = infra_by_zone[zone.zone_id]

            merged_bundle = ResourceBundle(
                water_tankers=max(f_rec.requested_resources.water_tankers, i_rec.requested_resources.water_tankers),
                medical_units=f_rec.requested_resources.medical_units,
                cooling_units=max(f_rec.requested_resources.cooling_units, i_rec.requested_resources.cooling_units),
                emergency_personnel=max(
                    f_rec.requested_resources.emergency_personnel,
                    i_rec.requested_resources.emergency_personnel,
                ),
                shelter_capacity=f_rec.requested_resources.shelter_capacity,
            )

            alt_rank = alt_rank_map[zone.zone_id]
            alt_score = alt_scores[zone.zone_id]
            rank_shift = alt_rank - rank
            score_delta = round(p_score - alt_score, 2)

            alt_considered = (
                f"Counterfactual '{alt_strategy.value}' policy (would assign Rank #{alt_rank}, score {alt_score}/100)"
            )
            if rank_shift > 0:
                rejection_reason = (
                    f"Rejected '{alt_strategy.value}' because it would demote {zone.name} by {rank_shift} "
                    f"rank(s) (score delta {score_delta:+.2f}), delaying response despite risk {zone.risk_score}/100 "
                    f"and {int(zone.vulnerability_index * 100)}% vulnerability."
                )
            elif rank_shift < 0:
                rejection_reason = (
                    f"Rejected '{alt_strategy.value}' (which would elevate {zone.name} by {abs(rank_shift)} rank(s)) "
                    f"because '{strategy.value}' reallocates scarce units to higher-weighted zones first."
                )
            else:
                rejection_reason = (
                    f"Both '{strategy.value}' and '{alt_strategy.value}' converge on Rank #{rank} for {zone.name} "
                    f"(score delta {score_delta:+.2f}), confirming robust priority consensus."
                )

            directives.append(
                ZoneDecisionRecord(
                    decision_id=f"DEC-{city.city_id}-{zone.zone_id}-R{rank}",
                    zone_id=zone.zone_id,
                    zone_name=zone.name,
                    priority_rank=rank,
                    priority_score=p_score,
                    risk_score=zone.risk_score,
                    selected_action=f"{f_rec.recommended_action} | {i_rec.recommended_action}",
                    recommended_bundle=merged_bundle,
                    relevant_factors={
                        "risk_score": zone.risk_score,
                        "ambient_temp_c": zone.ambient_temp_c,
                        "vulnerability_pct": round(zone.vulnerability_index * 100, 1),
                        "population": float(zone.population),
                        "fire_urgency": f_rec.urgency_score,
                        "infra_urgency": i_rec.urgency_score,
                        "counterfactual_rank": float(alt_rank),
                    },
                    reasoning=(
                        f"Ranked #{rank} under '{strategy.value}' (priority {p_score}/100): "
                        f"risk {zone.risk_score}/100, population {zone.population:,}, "
                        f"vulnerability {int(zone.vulnerability_index * 100)}%, "
                        f"Fire Urgency {f_rec.urgency_score}, Infra Urgency {i_rec.urgency_score}."
                    ),
                    alternative_considered=alt_considered,
                    rejection_reason=rejection_reason,
                )
            )

        top = directives[0]
        city_summary = (
            f"Council prioritized {top.zone_name} (#1, score {top.priority_score}) across {len(city.zones)} zones "
            f"using '{strategy.value}', resolving {len(conflicts)} inter-agent divergence(s)."
        )

        return MultiAgentCouncilReport(
            strategy=strategy,
            fire_emergency_assessment=fire_report,
            infrastructure_assessment=infra_report,
            detected_conflicts=conflicts,
            authority_directives=directives,
            city_wide_summary=city_summary,
            strategy_tradeoff_explanation=self._strategy_explanation(strategy),
        )
