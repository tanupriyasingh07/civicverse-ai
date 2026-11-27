from app.agents.fire_emergency import FireEmergencyAgent
from app.agents.infrastructure import InfrastructureAgent
from app.schemas.agents import (
    AllocationStrategy,
    MultiAgentCouncilReport,
    ZoneDecisionRecord,
)
from app.schemas.city import CityState, ResourceBundle, ZoneState


class CityAuthorityAgent:
    agent_id = "agent_city_authority_03"
    agent_name = "City Emergency Authority Coordinator"

    def __init__(self) -> None:
        self.fire_agent = FireEmergencyAgent()
        self.infra_agent = InfrastructureAgent()

    def _compute_strategy_priority(
        self,
        zone: ZoneState,
        fire_urgency: float,
        infra_urgency: float,
        max_population: int,
        strategy: AllocationStrategy,
    ) -> float:
        pop_norm = (zone.population / max(1, max_population)) * 100.0
        vuln_norm = zone.vulnerability_index * 100.0
        joint_agent_score = (fire_urgency * 0.55) + (infra_urgency * 0.45)

        if strategy == AllocationStrategy.POPULATION_PRIORITY:
            return round((pop_norm * 0.70) + (zone.risk_score * 0.30), 2)
        if strategy == AllocationStrategy.RISK_PRIORITY:
            return round((zone.risk_score * 0.75) + (joint_agent_score * 0.25), 2)
        if strategy == AllocationStrategy.VULNERABILITY_PRIORITY:
            return round((vuln_norm * 0.65) + (zone.risk_score * 0.35), 2)
        # BALANCED_PRIORITY (Risk + Vulnerability + Infrastructure + Population aware)
        return round(
            (zone.risk_score * 0.35)
            + (vuln_norm * 0.25)
            + (infra_urgency * 0.20)
            + (pop_norm * 0.20),
            2,
        )

    def deliberate(
        self, city: CityState, strategy: AllocationStrategy = AllocationStrategy.BALANCED_PRIORITY
    ) -> MultiAgentCouncilReport:
        fire_report = self.fire_agent.analyze(city)
        infra_report = self.infra_agent.analyze(city)

        fire_map = {r.zone_id: r for r in fire_report.zone_recommendations}
        infra_map = {r.zone_id: r for r in infra_report.zone_recommendations}
        max_pop = max(z.population for z in city.zones)

        scored_zones = []
        for zone in city.zones:
            f_rec = fire_map[zone.zone_id]
            i_rec = infra_map[zone.zone_id]
            p_score = self._compute_strategy_priority(
                zone, f_rec.urgency_score, i_rec.urgency_score, max_pop, strategy
            )
            scored_zones.append((zone, f_rec, i_rec, p_score))

        scored_zones.sort(key=lambda item: item[3], reverse=True)

        directives: list[ZoneDecisionRecord] = []
        for rank, (zone, f_rec, i_rec, p_score) in enumerate(scored_zones, start=1):
            merged_bundle = ResourceBundle(
                water_tankers=i_rec.requested_resources.water_tankers,
                medical_units=f_rec.requested_resources.medical_units,
                cooling_units=i_rec.requested_resources.cooling_units,
                emergency_personnel=f_rec.requested_resources.emergency_personnel,
                shelter_capacity=f_rec.requested_resources.shelter_capacity,
            )

            factors = {
                "risk_score": zone.risk_score,
                "population": float(zone.population),
                "vulnerability_pct": round(zone.vulnerability_index * 100.0, 1),
                "fire_agent_urgency": f_rec.urgency_score,
                "infra_agent_urgency": i_rec.urgency_score,
                "strategy_priority_score": p_score,
            }

            reasoning = (
                f"Ranked #{rank} under '{strategy.value}' (priority {p_score}/100): "
                f"risk {zone.risk_score}/100, population {zone.population:,}, "
                f"vulnerability {int(zone.vulnerability_index * 100)}%, "
                f"Fire Urgency {f_rec.urgency_score}, Infra Urgency {i_rec.urgency_score}."
            )

            if rank <= 3:
                alt = "Defer full resource allocation to preserve central reserve buffer"
                reject = (
                    f"Rejected because deferred response in {zone.name} (risk {zone.risk_score}, "
                    f"temp {zone.ambient_temp_c}°C) risks acute mortality and grid failure."
                )
            else:
                alt = "Immediate 100% demand fulfillment ahead of higher-ranked zones"
                reject = (
                    f"Rejected due to city-wide resource constraints; higher-priority zones (#1-#3) "
                    f"exhibit greater composite urgency under '{strategy.value}'."
                )

            directives.append(
                ZoneDecisionRecord(
                    decision_id=f"DEC-{city.city_id}-{zone.zone_id}-R{rank}",
                    zone_id=zone.zone_id,
                    zone_name=zone.name,
                    priority_rank=rank,
                    priority_score=p_score,
                    risk_score=zone.risk_score,
                    selected_action=f"{f_rec.recommended_action}; {i_rec.recommended_action}",
                    recommended_bundle=merged_bundle,
                    relevant_factors=factors,
                    reasoning=reasoning,
                    alternative_considered=alt,
                    rejection_reason=reject,
                )
            )

        strategy_explanations = {
            AllocationStrategy.POPULATION_PRIORITY: "Maximizes raw headcount coverage first; trades off higher per-capita vulnerability in smaller wards.",
            AllocationStrategy.RISK_PRIORITY: "Targets peak composite hazard scores first; may leave high-population moderate-risk zones partially unserved.",
            AllocationStrategy.VULNERABILITY_PRIORITY: "Protects socio-economically fragile & elderly populations first; trades off commercial/industrial infrastructure continuity.",
            AllocationStrategy.BALANCED_PRIORITY: "Jointly weights hazard severity (35%), vulnerability (25%), infrastructure stress (20%), and population scale (20%) to balance equity and risk reduction.",
        }

        top_zone = directives[0]
        return MultiAgentCouncilReport(
            strategy=strategy,
            fire_emergency_assessment=fire_report,
            infrastructure_assessment=infra_report,
            authority_directives=directives,
            city_wide_summary=(
                f"Council prioritized {top_zone.zone_name} (#1, score {top_zone.priority_score}) "
                f"across {len(directives)} zones using '{strategy.value}'."
            ),
            strategy_tradeoff_explanation=strategy_explanations[strategy],
        )
