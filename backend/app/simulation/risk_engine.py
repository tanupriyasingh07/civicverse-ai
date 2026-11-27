import math
from app.schemas.city import CityState, ResourceBundle, RiskLevel, ZoneState


def classify_risk_level(score: float) -> RiskLevel:
    if score >= 75.0:
        return RiskLevel.CRITICAL
    if score >= 55.0:
        return RiskLevel.HIGH
    if score >= 35.0:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


def evaluate_zone_risk_and_demand(zone: ZoneState) -> ZoneState:
    """
    Computes an explainable, weighted multi-factor risk score (0-100) and
    derives deterministic emergency resource demand from zone stressors.
    """
    # Normalize thermal stress between 35°C (0.0) and 52°C (1.0)
    thermal_stress = max(0.0, min(1.0, (zone.ambient_temp_c - 35.0) / 17.0))
    water_deficit = 1.0 - zone.water_availability
    infra_fragility = 1.0 - zone.infrastructure_condition
    medical_gap = 1.0 - zone.hospital_accessibility
    vulnerability = zone.vulnerability_index

    # Weighted composite risk formula (weights sum to 1.0)
    contributions = {
        "thermal_stress": round(thermal_stress * 32.0, 2),
        "vulnerability": round(vulnerability * 24.0, 2),
        "water_deficit": round(water_deficit * 20.0, 2),
        "infrastructure_fragility": round(infra_fragility * 14.0, 2),
        "medical_access_gap": round(medical_gap * 10.0, 2),
    }

    raw_score = sum(contributions.values())
    zone.risk_score = round(max(0.0, min(100.0, raw_score)), 2)
    zone.risk_level = classify_risk_level(zone.risk_score)
    zone.risk_factors = contributions

    # Deterministic resource demand calculation scaled by population & severity
    pop_units = zone.population / 10000.0
    severity = zone.risk_score / 100.0

    zone.resource_demand = ResourceBundle(
        water_tankers=max(1, math.ceil(pop_units * (0.6 + water_deficit * 1.4) * (0.5 + severity))),
        medical_units=max(1, math.ceil(pop_units * (0.4 + vulnerability * 1.1 + medical_gap * 0.6) * severity)),
        cooling_units=max(1, math.ceil(pop_units * (0.5 + thermal_stress * 1.3) * (0.5 + vulnerability * 0.5))),
        emergency_personnel=max(4, math.ceil(pop_units * 3.2 * (0.4 + severity))),
        shelter_capacity=max(200, int(math.ceil((zone.population * vulnerability * severity * 0.08) / 50.0) * 50)),
    )
    return zone


def evaluate_city_risk(city: CityState) -> CityState:
    updated_city = city.model_copy(deep=True)
    for zone in updated_city.zones:
        evaluate_zone_risk_and_demand(zone)
    return updated_city
