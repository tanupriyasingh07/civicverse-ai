from app.agents.city_authority import CityAuthorityAgent
from app.allocation.allocator import allocate_constrained_resources
from app.evaluation.metrics import apply_intervention_effects, evaluate_simulation_outcomes
from app.scenarios.heatwave import HeatwaveScenarioConfig, apply_heatwave_conditions
from app.schemas.agents import AllocationStrategy
from app.schemas.city import ResourceBundle
from app.simulation.city_generator import create_default_city
from app.simulation.risk_engine import evaluate_city_risk


def _build_crisis_city_and_directives(temp: float = 48.0):
    city = evaluate_city_risk(
        apply_heatwave_conditions(create_default_city(), HeatwaveScenarioConfig(base_temperature_c=temp))
    )
    report = CityAuthorityAgent().deliberate(city, strategy=AllocationStrategy.BALANCED_PRIORITY)
    return city, report.authority_directives


def test_zero_inventory_edge_case():
    city, directives = _build_crisis_city_and_directives()
    city.available_resources = ResourceBundle(
        water_tankers=0,
        medical_units=0,
        cooling_units=0,
        emergency_personnel=0,
        shelter_capacity=0,
    )

    updated_city, unallocated, _, _ = allocate_constrained_resources(
        city, directives, AllocationStrategy.BALANCED_PRIORITY
    )

    for z in updated_city.zones:
        assert z.assigned_resources == ResourceBundle()
        assert z.unmet_demand_ratio == 1.0

    post_city = apply_intervention_effects(updated_city)
    metrics = evaluate_simulation_outcomes(city, post_city, unallocated)
    assert metrics.allocation_fairness_jain == 0.0
    assert metrics.vulnerability_outcome_equity == 0.0
    assert metrics.resource_utilization_pct == 0.0


def test_scarce_inventory_triggers_proportional_safety_floor_rationing():
    city, directives = _build_crisis_city_and_directives(temp=49.0)
    city.available_resources.water_tankers = 3

    updated_city, unallocated, _, notes = allocate_constrained_resources(
        city, directives, AllocationStrategy.RISK_PRIORITY
    )

    total_assigned_water = sum(z.assigned_resources.water_tankers for z in updated_city.zones)
    assert total_assigned_water == 3
    assert unallocated.water_tankers == 0
    assert any("Safety-floor contention on 'water_tankers'" in n for n in notes)


def test_zero_demand_edge_case():
    city, directives = _build_crisis_city_and_directives()
    for d in directives:
        d.recommended_bundle = ResourceBundle()
    for z in city.zones:
        z.resource_demand = ResourceBundle()

    updated_city, unallocated, _, _ = allocate_constrained_resources(
        city, directives, AllocationStrategy.BALANCED_PRIORITY
    )

    for z in updated_city.zones:
        assert z.unmet_demand_ratio == 0.0
    assert unallocated == city.available_resources


def test_infrastructure_assets_relieved_after_intervention():
    city, directives = _build_crisis_city_and_directives(temp=48.0)
    pre_loads = {a.asset_id: a.current_load for a in city.infrastructure}

    allocated_city, unallocated, _, _ = allocate_constrained_resources(
        city, directives, AllocationStrategy.BALANCED_PRIORITY
    )
    post_city = apply_intervention_effects(allocated_city)
    metrics = evaluate_simulation_outcomes(city, post_city, unallocated)

    assert any(a.current_load < pre_loads[a.asset_id] for a in post_city.infrastructure)
    assert 0.0 < metrics.vulnerability_outcome_equity <= 1.0


def test_deterministic_tie_breaking_on_equal_priority():
    city, directives = _build_crisis_city_and_directives()
    for d in directives:
        d.priority_score = 75.0

    run1, _, _, _ = allocate_constrained_resources(city, directives, AllocationStrategy.RISK_PRIORITY)
    run2, _, _, _ = allocate_constrained_resources(city, reversed(directives), AllocationStrategy.RISK_PRIORITY)

    for z1, z2 in zip(run1.zones, run2.zones):
        assert z1.assigned_resources == z2.assigned_resources
