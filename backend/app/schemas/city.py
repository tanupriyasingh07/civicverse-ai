from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ZoneType(str, Enum):
    RESIDENTIAL_HIGH_DENSITY = "residential_high_density"
    RESIDENTIAL_VULNERABLE = "residential_vulnerable"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    MEDICAL_DISTRICT = "medical_district"
    SUBURBAN = "suburban"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class InfrastructureType(str, Enum):
    HOSPITAL = "hospital"
    WATER_STATION = "water_station"
    EMERGENCY_STATION = "emergency_station"
    COOLING_CENTER = "cooling_center"
    POWER_SUBSTATION = "power_substation"


class InfrastructureAsset(BaseModel):
    asset_id: str
    name: str
    asset_type: InfrastructureType
    zone_id: str
    capacity: int = Field(ge=0)
    current_load: int = Field(ge=0)
    condition_score: float = Field(ge=0.0, le=1.0, description="1.0 = optimal, 0.0 = failed")
    operational: bool = True


class ResourceBundle(BaseModel):
    water_tankers: int = Field(default=0, ge=0)
    medical_units: int = Field(default=0, ge=0)
    cooling_units: int = Field(default=0, ge=0)
    emergency_personnel: int = Field(default=0, ge=0)
    shelter_capacity: int = Field(default=0, ge=0)


class ZoneState(BaseModel):
    zone_id: str
    name: str
    zone_type: ZoneType
    # 3D spatial footprint on the digital twin grid
    grid_x: float
    grid_z: float
    width: float = 18.0
    depth: float = 18.0
    building_density: float = Field(ge=0.1, le=1.0)
    # Socio-environmental indicators
    population: int = Field(gt=0)
    vulnerability_index: float = Field(ge=0.0, le=1.0, description="0.0 = resilient, 1.0 = highly vulnerable")
    ambient_temp_c: float
    heat_island_offset_c: float = Field(default=0.0)
    water_availability: float = Field(ge=0.0, le=1.0, description="1.0 = full supply, 0.0 = depleted")
    infrastructure_condition: float = Field(ge=0.0, le=1.0)
    hospital_accessibility: float = Field(ge=0.0, le=1.0)
    # Computed crisis state
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    risk_level: RiskLevel = RiskLevel.LOW
    risk_factors: Dict[str, float] = Field(default_factory=dict)
    resource_demand: ResourceBundle = Field(default_factory=ResourceBundle)
    assigned_resources: ResourceBundle = Field(default_factory=ResourceBundle)
    unmet_demand_ratio: float = Field(default=0.0, ge=0.0, le=1.0)


class CityState(BaseModel):
    city_id: str
    city_name: str
    tick: int = 0
    zones: List[ZoneState]
    infrastructure: List[InfrastructureAsset]
    available_resources: ResourceBundle

    @property
    def total_population(self) -> int:
        return sum(z.population for z in self.zones)

    @property
    def average_risk_score(self) -> float:
        if not self.zones:
            return 0.0
        return round(sum(z.risk_score for z in self.zones) / len(self.zones), 2)
