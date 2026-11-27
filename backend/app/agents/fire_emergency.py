from app.schemas.agents import AgentAssessment, ZoneRecommendation
from app.schemas.city import CityState, ResourceBundle, RiskLevel


class FireEmergencyAgent:
    agent_id = "agent_fire_emergency_01"
    agent_name = "Fire & Emergency Response Agent"
    domain = "Life Safety, Heatstroke Triage & Thermal Hazard"

    def analyze(self, city: CityState) -> AgentAssessment:
        recommendations: list[ZoneRecommendation] = []
        critical_zones: list[str] = []
        constraints: list[str] = []

        total_med_demand = sum(z.resource_demand.medical_units for z in city.zones)
        if total_med_demand > city.available_resources.medical_units:
            constraints.append(
                f"Medical unit deficit: demand ({total_med_demand}) exceeds supply ({city.available_resources.medical_units})."
            )

        total_shelter_demand = sum(z.resource_demand.shelter_capacity for z in city.zones)
        if total_shelter_demand > city.available_resources.shelter_capacity:
            constraints.append(
                f"Cooling shelter deficit: demand ({total_shelter_demand}) exceeds capacity ({city.available_resources.shelter_capacity})."
            )

        for zone in sorted(city.zones, key=lambda z: z.risk_score, reverse=True):
            threats: list[str] = []
            if zone.ambient_temp_c >= 47.5:
                threats.append(f"Extreme thermal exposure ({zone.ambient_temp_c}°C) — acute heatstroke surge")
            if zone.hospital_accessibility < 0.55:
                threats.append(f"Severely degraded hospital access ({int(zone.hospital_accessibility * 100)}%)")
            if zone.building_density >= 0.85 and zone.ambient_temp_c >= 46.5:
                threats.append("High-density urban heat-trapping & electrical fire hazard")
            if not threats:
                threats.append("Elevated ambient heat load requiring standard triage standby")

            urgency = round(
                min(
                    100.0,
                    (zone.risk_score * 0.65)
                    + (zone.vulnerability_index * 20.0)
                    + ((1.0 - zone.hospital_accessibility) * 15.0),
                ),
                2,
            )

            if zone.risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH):
                critical_zones.append(zone.zone_id)

            requested = ResourceBundle(
                water_tankers=0,
                medical_units=zone.resource_demand.medical_units,
                cooling_units=0,
                emergency_personnel=zone.resource_demand.emergency_personnel,
                shelter_capacity=zone.resource_demand.shelter_capacity,
            )

            action = (
                "Deploy mobile heat-triage units, expand emergency cooling shelters, and stage rapid fire-rescue squads"
                if zone.risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH)
                else "Maintain mobile paramedic patrol and heat-advisory monitoring"
            )

            rationale = (
                f"Zone {zone.zone_id} ({zone.name}) at {zone.ambient_temp_c}°C with "
                f"{zone.population:,} residents (vulnerability {zone.vulnerability_index:.2f}) "
                f"and {int(zone.hospital_accessibility * 100)}% hospital access."
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
                f"Identified {len(critical_zones)} high/critical life-safety zones; "
                f"city emergency severity index is {city_severity}/100."
            ),
        )
