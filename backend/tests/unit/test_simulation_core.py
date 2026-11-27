from app.scenarios.heatwave import HeatwaveScenarioConfig, apply_heatwave_conditions
from app.schemas.city import RiskLevel
from app.simulation.city_generator import create_default_city
from app.simulation.risk_engine import evaluate_city_risk


def test_city_generation_structure():
    city = create_default_city()
    assert city.city_name == "Aurelia Metro"
    assert len(city.zones) == 8
    assert len(city.infrastructure) >= 6
    assert city.available_resources.water_tankers == 42


def test_deterministic_heatwave_reproducibility():
    base_city = create_default_city()
    config = HeatwaveScenarioConfig(base_temperature_c=46.0, random_seed=101)

    run1 = evaluate_city_risk(apply_heatwave_conditions(base_city, config))
    run2 = evaluate_city_risk(apply_heatwave_conditions(base_city, config))

    assert [z.risk_score for z in run1.zones] == [z.risk_score for z in run2.zones]
    assert [z.ambient_temp_c for z in run1.zones] == [z.ambient_temp_c for z in run2.zones]


def test_high_vulnerability_zone_escalates_to_critical():
    city = create_default_city()
    config = HeatwaveScenarioConfig(base_temperature_c=47.0, duration_hours=72, random_seed=42)
    crisis_city = evaluate_city_risk(apply_heatwave_conditions(city, config))

    z6 = next(z for z in crisis_city.zones if z.zone_id == "Z6")
    z7 = next(z for z in crisis_city.zones if z.zone_id == "Z7")

    assert z6.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
    assert z6.risk_score > z7.risk_score
    assert z6.resource_demand.water_tankers > z7.resource_demand.water_tankers
