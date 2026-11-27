import random
from pydantic import BaseModel, Field
from app.schemas.city import CityState


class HeatwaveScenarioConfig(BaseModel):
    scenario_id: str = "heatwave_mvp_v1"
    name: str = "Severe Urban Heatwave Crisis"
    crisis_type: str = "urban_heatwave"
    base_temperature_c: float = Field(default=46.0, ge=35.0, le=56.0)
    duration_hours: int = Field(default=48, ge=6, le=168)
    water_scarcity_factor: float = Field(default=0.35, ge=0.0, le=0.9)
    grid_stress_factor: float = Field(default=0.25, ge=0.0, le=0.9)
    random_seed: int = Field(default=42)


def apply_heatwave_conditions(city: CityState, config: HeatwaveScenarioConfig) -> CityState:
    """
    Deterministically applies heatwave stressors (ambient heat + urban heat-island effect,
    water depletion, infrastructure strain, and hospital load surge) to a cloned city state.
    """
    rng = random.Random(config.random_seed)
    updated_city = city.model_copy(deep=True)
    updated_city.tick += 1

    duration_multiplier = min(1.35, 0.85 + (config.duration_hours / 96.0))

    for zone in updated_city.zones:
        micro_variation = rng.uniform(-0.4, 0.4)
        zone.ambient_temp_c = round(
            config.base_temperature_c + zone.heat_island_offset_c + micro_variation, 2
        )

        # Water supply drops faster in high-temperature, high-density zones
        temp_excess = max(0.0, zone.ambient_temp_c - 38.0)
        water_loss = (config.water_scarcity_factor * 0.65) + (temp_excess * 0.018 * duration_multiplier)
        zone.water_availability = round(max(0.05, min(1.0, zone.water_availability - water_loss)), 3)

        # Power/water infrastructure degrades under sustained thermal + grid stress
        infra_loss = (config.grid_stress_factor * 0.50) + (temp_excess * 0.012 * duration_multiplier)
        zone.infrastructure_condition = round(
            max(0.10, min(1.0, zone.infrastructure_condition - infra_loss)), 3
        )

        # Hospital accessibility drops as emergency admissions surge
        surge_penalty = (temp_excess * 0.014) + (zone.vulnerability_index * 0.08)
        zone.hospital_accessibility = round(
            max(0.10, min(1.0, zone.hospital_accessibility - surge_penalty)), 3
        )

    for asset in updated_city.infrastructure:
        zone_match = next((z for z in updated_city.zones if z.zone_id == asset.zone_id), None)
        if zone_match:
            asset.condition_score = zone_match.infrastructure_condition
            surge_ratio = 1.0 + max(0.0, (zone_match.ambient_temp_c - 40.0) * 0.06)
            asset.current_load = min(int(asset.capacity * 1.25), int(asset.current_load * surge_ratio))

    return updated_city
