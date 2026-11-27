from typing import Dict
from pydantic import BaseModel, Field
from app.allocation.allocator import RESOURCE_FIELDS
from app.schemas.city import CityState, ResourceBundle
from app.simulation.risk_engine import classify_risk_level


UNIT_COST_INR_LAKHS = {
    "water_tankers": 0.45,
    "medical_units": 1.80,
    "cooling_units": 0.95,
    "emergency_personnel": 0.15,
    "shelter_capacity": 0.008,  # per bed/person capacity
}


class SimulationMetrics(BaseModel):
    initial_avg_risk: float
    final_avg_risk: float
    risk_reduction_pct: float
    population_protected: int
    population_protected_pct: float
    emergency_effectiveness: float = Field(ge=0.0, le=100.0)
    resource_utilization_pct: float = Field(ge=0.0, le=100.0)
    unmet_demand_pct: float = Field(ge=0.0, le=100.0)
    resource_wastage_pct: float = Field(ge=0.0, le=100.0)
    allocation_fairness_jain: float = Field(ge=0.0, le=1.0)
    estimated_cost_inr_lakhs: float
    composite_score: float = Field(ge=0.0, le=100.0)
    metric_weights: Dict[str, float]


def apply_intervention_effects(city: CityState) -> CityState:
    """
    Applies measurable post-allocation relief to each zone's water supply,
    ambient heat load, medical access, and recalculates residual risk score.
    """
    post_city = city.model_copy(deep=True)
    for zone in post_city.zones:
        fulfillment = 1.0 - zone.unmet_demand_ratio

        # Water tankers replenish local supply
        water_ratio = min(1.0, zone.assigned_resources.water_tankers / max(1, zone.resource_demand.water_tankers))
        zone.water_availability = round(min(1.0, zone.water_availability + (0.28 * water_ratio)), 3)

        # Cooling units & shelters reduce effective thermal exposure
        cool_ratio = min(1.0, zone.assigned_resources.cooling_units / max(1, zone.resource_demand.cooling_units))
        zone.ambient_temp_c = round(zone.ambient_temp_c - (2.6 * cool_ratio), 2)

        # Medical units & personnel improve emergency triage accessibility
        med_ratio = min(1.0, zone.assigned_resources.medical_units / max(1, zone.resource_demand.medical_units))
        zone.hospital_accessibility = round(min(1.0, zone.hospital_accessibility + (0.22 * med_ratio)), 3)

        # Risk reduction proportional to weighted fulfillment & infrastructure resilience
        reduction_points = zone.risk_score * (0.42 * fulfillment)
        zone.risk_score = round(max(5.0, zone.risk_score - reduction_points), 2)
        zone.risk_level = classify_risk_level(zone.risk_score)

    return post_city


def evaluate_simulation_outcomes(
    pre_city: CityState,
    post_city: CityState,
    unallocated: ResourceBundle,
) -> SimulationMetrics:
    initial_avg = pre_city.average_risk_score
    final_avg = post_city.average_risk_score
    risk_reduction_pct = round(
        max(0.0, ((initial_avg - final_avg) / max(1.0, initial_avg)) * 100.0), 2
    )

    total_pop = post_city.total_population
    protected_pop = sum(
        int(z.population * (1.0 - z.unmet_demand_ratio) * (0.65 + 0.35 * (1.0 - z.risk_score / 100.0)))
        for z in post_city.zones
    )
    protected_pct = round(min(100.0, (protected_pop / max(1, total_pop)) * 100.0), 2)

    # Resource utilization & wastage across normalized inventory fractions
    avail_dict = pre_city.available_resources.model_dump()
    unalloc_dict = unallocated.model_dump()
    util_fractions = []
    for field in RESOURCE_FIELDS:
        total_avail = max(1, avail_dict[field])
        used = total_avail - unalloc_dict[field]
        util_fractions.append(used / total_avail)

    utilization_pct = round((sum(util_fractions) / len(util_fractions)) * 100.0, 2)
    wastage_pct = round(max(0.0, 100.0 - utilization_pct), 2)

    unmet_pct = round(
        (sum(z.unmet_demand_ratio for z in post_city.zones) / max(1, len(post_city.zones))) * 100.0,
        2,
    )

    # Jain's Fairness Index over zone fulfillment ratios: (sum(x_i))^2 / (n * sum(x_i^2))
    fulfillments = [max(0.01, 1.0 - z.unmet_demand_ratio) for z in post_city.zones]
    n = len(fulfillments)
    sum_x = sum(fulfillments)
    sum_x_sq = sum(x * x for x in fulfillments)
    jain_index = round((sum_x * sum_x) / max(1e-6, n * sum_x_sq), 4)

    # Cost calculation in INR Lakhs
    total_cost = 0.0
    for z in post_city.zones:
        assigned = z.assigned_resources.model_dump()
        for field, unit_cost in UNIT_COST_INR_LAKHS.items():
            total_cost += assigned[field] * unit_cost
    total_cost = round(total_cost, 2)

    effectiveness = round(
        min(100.0, (risk_reduction_pct * 1.35) + (protected_pct * 0.45)), 2
    )

    weights = {
        "risk_reduction": 0.30,
        "population_protection": 0.30,
        "emergency_effectiveness": 0.20,
        "allocation_fairness": 0.10,
        "resource_utilization": 0.10,
    }

    composite = round(
        min(
            100.0,
            (min(100.0, risk_reduction_pct * 2.2) * weights["risk_reduction"])
            + (protected_pct * weights["population_protection"])
            + (effectiveness * weights["emergency_effectiveness"])
            + ((jain_index * 100.0) * weights["allocation_fairness"])
            + (utilization_pct * weights["resource_utilization"]),
        ),
        2,
    )

    return SimulationMetrics(
        initial_avg_risk=initial_avg,
        final_avg_risk=final_avg,
        risk_reduction_pct=risk_reduction_pct,
        population_protected=protected_pop,
        population_protected_pct=protected_pct,
        emergency_effectiveness=effectiveness,
        resource_utilization_pct=utilization_pct,
        unmet_demand_pct=unmet_pct,
        resource_wastage_pct=wastage_pct,
        allocation_fairness_jain=jain_index,
        estimated_cost_inr_lakhs=total_cost,
        composite_score=composite,
        metric_weights=weights,
    )
