from app.agents.city_authority import CityAuthorityAgent
from app.scenarios.heatwave import HeatwaveScenarioConfig, apply_heatwave_conditions
from app.schemas.agents import AllocationStrategy
from app.simulation.city_generator import create_default_city
from app.simulation.risk_engine import evaluate_city_risk


def test_multi_agent_council_deliberation():
    city = evaluate_city_risk(
        apply_heatwave_conditions(create_default_city(), HeatwaveScenarioConfig(base_temperature_c=46.5))
    )
    council = CityAuthorityAgent()
    report = council.deliberate(city, strategy=AllocationStrategy.BALANCED_PRIORITY)

    assert len(report.fire_emergency_assessment.zone_recommendations) == 8
    assert len(report.infrastructure_assessment.zone_recommendations) == 8
    assert len(report.authority_directives) == 8
    assert report.authority_directives[0].priority_rank == 1
    assert len(report.fire_emergency_assessment.identified_constraints) > 0


def test_strategy_changes_zone_prioritization():
    city = evaluate_city_risk(
        apply_heatwave_conditions(create_default_city(), HeatwaveScenarioConfig(base_temperature_c=46.0))
    )
    council = CityAuthorityAgent()

    pop_report = council.deliberate(city, strategy=AllocationStrategy.POPULATION_PRIORITY)
    vuln_report = council.deliberate(city, strategy=AllocationStrategy.VULNERABILITY_PRIORITY)

    # Under population priority, Z5 (82,000 pop) ranks #1; under vulnerability priority, Z6 (0.91 vuln) ranks #1
    assert pop_report.authority_directives[0].zone_id == "Z5"
    assert vuln_report.authority_directives[0].zone_id == "Z6"
