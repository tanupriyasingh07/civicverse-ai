from app.scenarios.heatwave import HeatwaveScenarioConfig
from app.schemas.agents import AllocationStrategy
from app.simulation.engine import SimulationEngine


def test_resource_allocation_respects_inventory_constraints():
    engine = SimulationEngine()
    result = engine.run_simulation(
        scenario=HeatwaveScenarioConfig(base_temperature_c=47.0),
        strategy=AllocationStrategy.BALANCED_PRIORITY,
    )

    avail = result.initial_crisis_city.available_resources
    total_water = sum(z.assigned_resources.water_tankers for z in result.final_city.zones)
    total_med = sum(z.assigned_resources.medical_units for z in result.final_city.zones)
    total_cool = sum(z.assigned_resources.cooling_units for z in result.final_city.zones)
    total_pers = sum(z.assigned_resources.emergency_personnel for z in result.final_city.zones)
    total_shelter = sum(z.assigned_resources.shelter_capacity for z in result.final_city.zones)

    assert total_water <= avail.water_tankers
    assert total_med <= avail.medical_units
    assert total_cool <= avail.cooling_units
    assert total_pers <= avail.emergency_personnel
    assert total_shelter <= avail.shelter_capacity
    assert result.metrics.final_avg_risk < result.metrics.initial_avg_risk


def test_strategy_comparison_fairness_and_tradeoffs():
    engine = SimulationEngine()
    comparison = engine.compare_strategies(HeatwaveScenarioConfig(base_temperature_c=46.5, random_seed=77))

    assert len(comparison.results_by_strategy) == 4
    pop_metrics = comparison.results_by_strategy[AllocationStrategy.POPULATION_PRIORITY.value].metrics
    bal_metrics = comparison.results_by_strategy[AllocationStrategy.BALANCED_PRIORITY.value].metrics

    # Balanced priority should achieve equal or higher Jain fairness than pure population priority
    assert bal_metrics.allocation_fairness_jain >= pop_metrics.allocation_fairness_jain
    assert comparison.recommended_strategy in list(AllocationStrategy)
