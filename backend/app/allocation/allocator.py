from typing import Dict, List, Tuple
from app.schemas.agents import AllocationStrategy, ZoneDecisionRecord
from app.schemas.city import CityState, ResourceBundle, RiskLevel


RESOURCE_FIELDS = (
    "water_tankers",
    "medical_units",
    "cooling_units",
    "emergency_personnel",
    "shelter_capacity",
)

RESOURCE_CRITICALITY_WEIGHTS = {
    "water_tankers": 0.30,
    "medical_units": 0.30,
    "cooling_units": 0.20,
    "emergency_personnel": 0.10,
    "shelter_capacity": 0.10,
}


def allocate_constrained_resources(
    city: CityState,
    directives: list[ZoneDecisionRecord],
    strategy: AllocationStrategy,
) -> Tuple[CityState, ResourceBundle, Dict[str, ResourceBundle], List[str]]:
    updated_city = city.model_copy(deep=True)
    zone_map = {z.zone_id: z for z in updated_city.zones}
    remaining = {k: max(0, v) for k, v in updated_city.available_resources.model_dump().items()}
    notes: List[str] = []

    ordered_directives = sorted(
        directives,
        key=lambda d: (-d.priority_score, d.zone_id),
    )

    allocated_by_zone: Dict[str, Dict[str, int]] = {
        z.zone_id: {field: 0 for field in RESOURCE_FIELDS} for z in updated_city.zones
    }

    critical_directives = [
        d for d in ordered_directives
        if zone_map[d.zone_id].risk_level in (RiskLevel.CRITICAL, RiskLevel.HIGH)
    ]

    for field in RESOURCE_FIELDS:
        avail = remaining[field]
        if avail <= 0 or not critical_directives:
            continue

        step = 50 if field == "shelter_capacity" else 1
        desired_floors: Dict[str, int] = {}
        for d in critical_directives:
            demand_qty = max(0, d.recommended_bundle.model_dump()[field])
            if demand_qty > 0:
                desired_floors[d.zone_id] = min(demand_qty, max(step, int(demand_qty * 0.15)))

        total_floor_req = sum(desired_floors.values())
        if total_floor_req == 0:
            continue

        if total_floor_req <= avail:
            for z_id, floor_qty in desired_floors.items():
                allocated_by_zone[z_id][field] += floor_qty
                remaining[field] -= floor_qty
        else:
            scale = avail / total_floor_req
            notes.append(
                f"Safety-floor contention on '{field}': critical floor demand ({total_floor_req}) "
                f"exceeded inventory ({avail}); applied proportional rationing (scale={scale:.2f})."
            )
            for d in critical_directives:
                z_id = d.zone_id
                if z_id not in desired_floors or remaining[field] <= 0:
                    continue
                raw_scaled = int(desired_floors[z_id] * scale)
                if field == "shelter_capacity":
                    raw_scaled = (raw_scaled // 50) * 50
                grant = min(desired_floors[z_id], raw_scaled, remaining[field])
                if grant > 0:
                    allocated_by_zone[z_id][field] += grant
                    remaining[field] -= grant

            for d in critical_directives:
                z_id = d.zone_id
                if z_id in desired_floors and remaining[field] >= step:
                    gap = desired_floors[z_id] - allocated_by_zone[z_id][field]
                    if gap >= step:
                        allocated_by_zone[z_id][field] += step
                        remaining[field] -= step

    cap_ratio = 0.85 if strategy == AllocationStrategy.BALANCED_PRIORITY else 1.0

    for directive in ordered_directives:
        zone = zone_map[directive.zone_id]
        demand = directive.recommended_bundle.model_dump()
        for field in RESOURCE_FIELDS:
            demand_qty = max(0, demand[field])
            target = int(demand_qty * cap_ratio) if directive.priority_rank <= 3 else demand_qty
            needed = max(0, target - allocated_by_zone[zone.zone_id][field])
            if needed > 0 and remaining[field] > 0:
                grant = min(needed, remaining[field])
                allocated_by_zone[zone.zone_id][field] += grant
                remaining[field] -= grant

    for directive in ordered_directives:
        zone = zone_map[directive.zone_id]
        demand = directive.recommended_bundle.model_dump()
        for field in RESOURCE_FIELDS:
            demand_qty = max(0, demand[field])
            needed = max(0, demand_qty - allocated_by_zone[zone.zone_id][field])
            if needed > 0 and remaining[field] > 0:
                grant = min(needed, remaining[field])
                allocated_by_zone[zone.zone_id][field] += grant
                remaining[field] -= grant

    final_bundles: Dict[str, ResourceBundle] = {}
    for zone_id, alloc_dict in allocated_by_zone.items():
        bundle = ResourceBundle(**alloc_dict)
        zone = zone_map[zone_id]
        zone.assigned_resources = bundle

        demand_dict = zone.resource_demand.model_dump()
        weighted_unmet = 0.0
        active_weight_sum = 0.0
        for field in RESOURCE_FIELDS:
            d_val = max(0, demand_dict[field])
            if d_val > 0:
                w = RESOURCE_CRITICALITY_WEIGHTS[field]
                unmet_frac = max(0.0, 1.0 - (alloc_dict[field] / d_val))
                weighted_unmet += unmet_frac * w
                active_weight_sum += w

        zone.unmet_demand_ratio = round(
            (weighted_unmet / active_weight_sum) if active_weight_sum > 0 else 0.0,
            4,
        )
        final_bundles[zone_id] = bundle

    unallocated_bundle = ResourceBundle(**remaining)
    return updated_city, unallocated_bundle, final_bundles, notes
