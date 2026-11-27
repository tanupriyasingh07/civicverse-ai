from app.agents.city_authority import CityAuthorityAgent
from app.scenarios.heatwave import HeatwaveScenarioConfig, apply_heatwave_conditions
from app.schemas.agents import AllocationStrategy
from app.simulation.city_generator import create_default_city
from app.simulation.risk_engine import evaluate_city_risk


def test_multi_agent_council_deliberation_and_conflict_arbitration():
    city = evaluate_city_risk(
        apply_heatwave_conditions(create_default_city(), HeatwaveScenarioConfig(base_temperature_c=47.5))
    )
    council = CityAuthorityAgent()
    report = council.deliberate(city, strategy=AllocationStrategy.BALANCED_PRIORITY)

    assert len(report.authority_directives) == 8
    ranks = [d.priority_rank for d in report.authority_directives]
    assert ranks == list(range(1, 9))
    assert all(d.reasoning and d.rejection_reason for d in report.authority_directives)
    assert all("Counterfactual" in d.alternative_considered for d in report.authority_directives)
    for c in report.detected_conflicts:
        assert c.divergence_delta >= 12.0
        assert c.winning_domain in ("Fire & Emergency", "Infrastructure & Utilities")


def test_strategy_changes_zone_prioritization():
    city = evaluate_city_risk(
        apply_heatwave_conditions(create_default_city(), HeatwaveScenarioConfig(base_temperature_c=47.0))
    )
    council = CityAuthorityAgent()

    pop_report = council.deliberate(city, strategy=AllocationStrategy.POPULATION_PRIORITY)
    vuln_report = council.deliberate(city, strategy=AllocationStrategy.VULNERABILITY_PRIORITY)

    pop_order = [d.zone_id for d in pop_report.authority_directives]
    vuln_order = [d.zone_id for d in vuln_report.authority_directives]
    assert pop_order != vuln_order
