from typing import Dict, Tuple
from app.schemas.agents import AllocationStrategy, ZoneDecisionRecord
from app.schemas.city import CityState, ResourceBundle, RiskLevel


RESOURCE_FIELDS = (
    "water_tankers",
    "medical_units",
    "cooling_units",
    "emergency_personnel",
    "shelter_capacity",
)


def allocate_constrained_resources(
    city: CityState,
    directives: list[ZoneDecisionRecord],
    strategy: AllocationStrategy,
) -> Tuple[CityState, ResourceBundle, Dict[str, ResourceBundle]]:
    """
    Allocates finite city-wide emergency resources across zones according to
    City Authority priority rankings while enforcing minimum safety floors for
    HIGH/CRITICAL zones and strict inventory upper bounds.
    """
    updated_city = city.model_copy(deep=True)
    zone_map = {z.zone_id: z for z in updated_city.zones}
    remaining = updated_city.available_resources.model_dump()
    allocated_by_zone: Dict[str, Dict[str, int]] = {
        z.zone_id: {field: 0 for field in RESOURCE_FIELDS} for z in updated_city.zones
    }

    # Pass 1: Minimum safety floor (15% of demand, at least 1 unit) for HIGH/CRITICAL zones
    for directive in directives:
        zone = zone_map[directive.zone_id]
        if zone.risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH):
            demand = directive.recommended_bundle.model_dump()
            for field in RESOURCE_FIELDS:
                if demand[field] > 0 and remaining[field] > 0:
                    step = 50 if field == "shelter_capacity" else 1
                    floor_qty = max(step, int(demand[field] * 0.15))
                    grant = min(demand[field], floor_qty, remaining[field])
                    allocated_by_zone[zone.zone_id][field] += grant
                    remaining[field] -= grant

    # Pass 2: Priority-ordered allocation up to strategy cap
    cap_ratio = 0.85 if strategy == AllocationStrategy.BALANCED_PRIORITY else 1.0

    for directive in directives:
        zone = zone_map[directive.zone_id]
        demand = directive.recommended_bundle.model_dump()
        for field in RESOURCE_FIELDS:
            target = int(demand[field] * cap_ratio) if directive.priority_rank <= 3 else demand[field]
            needed = max(0, target - allocated_by_zone[zone.zone_id][field])
            if needed > 0 and remaining[field] > 0:
                grant = min(needed, remaining[field])
                allocated_by_zone[zone.zone_id][field] += grant
                remaining[field] -= grant

    # Pass 3: Distribute any leftover inventory in priority order up to 100% demand
    for directive in directives:
        zone = zone_map[directive.zone_id]
        demand = directive.recommended_bundle.model_dump()
        for field in RESOURCE_FIELDS:
            needed = max(0, demand[field] - allocated_by_zone[zone.zone_id][field])
            if needed > 0 and remaining[field] > 0:
                grant = min(needed, remaining[field])
                allocated_by_zone[zone.zone_id][field] += grant
                remaining[field] -= grant

    final_bundles: Dict[str, ResourceBundle] = {}
    for zone_id, alloc_dict in allocated_by_zone.items():
        bundle = ResourceBundle(**alloc_dict)
        zone = zone_map[zone_id]
        zone.assigned_resources = bundle

        # Calculate weighted unmet demand ratio for the zone
        demand_dict = zone.resource_demand.model_dump()
        ratios = []
        for field in RESOURCE_FIELDS:
            if demand_dict[field] > 0:
                ratios.append(1.0 - (alloc_dict[field] / demand_dict[field]))
        zone.unmet_demand_ratio = round(sum(ratios) / max(1, len(ratios)), 3)
        final_bundles[zone_id] = bundle

    unallocated_bundle = ResourceBundle(**remaining)
    return updated_city, unallocated_bundle, final_bundles
