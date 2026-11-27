from app.schemas.agents import AgentAssessment, ZoneRecommendation
from app.schemas.city import CityState, ResourceBundle, RiskLevel


class InfrastructureAgent:
    agent_id = "agent_infrastructure_02"
    agent_name = "Urban Infrastructure & Utilities Agent"
    domain = "Water Grid, Power Substations & Cooling Continuity"

    def analyze(self, city: CityState) -> AgentAssessment:
        recommendations: list[ZoneRecommendation] = []
        critical_zones: list[str] = []
        constraints: list[str] = []

        total_water_demand = sum(z.resource_demand.water_tankers for z in city.zones)
        if total_water_demand > city.available_resources.water_tankers:
            constraints.append(
                f"Potable water fleet shortage: demand ({total_water_demand} tankers) vs available ({city.available_resources.water_tankers})."
            )

        total_cooling_demand = sum(z.resource_demand.cooling_units for z in city.zones)
        if total_cooling_demand > city.available_resources.cooling_units:
            constraints.append(
                f"Mobile cooling unit shortage: demand ({total_cooling_demand}) vs available ({city.available_resources.cooling_units})."
            )

        for asset in city.infrastructure:
            if asset.current_load > asset.capacity:
                constraints.append(
                    f"Asset overload: {asset.name} operating at {int((asset.current_load / asset.capacity) * 100)}% capacity."
                )

        for zone in sorted(city.zones, key=lambda z: z.water_availability):
            threats: list[str] = []
            if zone.water_availability < 0.45:
                threats.append(f"Severe water supply depletion ({int(zone.water_availability * 100)}% remaining)")
            if zone.infrastructure_condition < 0.55:
                threats.append(f"Substation & pipeline thermal degradation ({int(zone.infrastructure_condition * 100)}% integrity)")
            if not threats:
                threats.append("Grid load elevated but within controllable operating margin")

            water_deficit = 1.0 - zone.water_availability
            infra_deficit = 1.0 - zone.infrastructure_condition
            urgency = round(
                min(100.0, (water_deficit * 50.0) + (infra_deficit * 35.0) + (zone.risk_score * 0.15)),
                2,
            )

            if urgency >= 55.0 or zone.risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH):
                critical_zones.append(zone.zone_id)

            requested = ResourceBundle(
                water_tankers=zone.resource_demand.water_tankers,
                medical_units=0,
                cooling_units=zone.resource_demand.cooling_units,
                emergency_personnel=0,
                shelter_capacity=0,
            )

            action = (
                "Dispatch emergency water tankers, deploy portable micro-grid cooling units, and shed non-essential grid load"
                if urgency >= 55.0
                else "Stabilize water pressure and monitor transformer thermal load"
            )

            rationale = (
                f"Zone {zone.zone_id} water supply is at {int(zone.water_availability * 100)}% "
                f"with infrastructure condition at {int(zone.infrastructure_condition * 100)}%."
            )

            recommendations.append(
                ZoneRecommendation(
                    zone_id=zone.zone_id,
                    zone_name=zone.name,
                    urgency_score=urgency,
                    risk_level=zone.risk_level,
                    immediate_threats=threats,
                    recommended_action=action,
                    requested_resources=requested,
                    rationale=rationale,
                )
            )

        city_severity = round(
            sum(r.urgency_score for r in recommendations) / max(1, len(recommendations)), 2
        )

        return AgentAssessment(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            domain=self.domain,
            city_severity_index=city_severity,
            critical_zone_ids=critical_zones,
            identified_constraints=constraints,
            zone_recommendations=recommendations,
            executive_summary=(
                f"Flagged {len(critical_zones)} utility-stressed zones; "
                f"infrastructure stress index is {city_severity}/100."
            ),
        )
