export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';

export type AllocationStrategy =
  | 'population_priority'
  | 'risk_priority'
  | 'vulnerability_priority'
  | 'balanced_priority';

export interface ResourceBundle {
  water_tankers: number;
  medical_units: number;
  cooling_units: number;
  emergency_personnel: number;
  shelter_capacity: number;
}

export interface InfrastructureAsset {
  asset_id: string;
  name: string;
  asset_type: 'hospital' | 'water_station' | 'emergency_station' | 'cooling_center' | 'power_substation';
  zone_id: string;
  capacity: number;
  current_load: number;
  condition_score: number;
  operational: boolean;
}

export interface ZoneState {
  zone_id: string;
  name: string;
  zone_type: string;
  grid_x: number;
  grid_z: number;
  width: number;
  depth: number;
  building_density: number;
  population: number;
  vulnerability_index: number;
  ambient_temp_c: number;
  heat_island_offset_c: number;
  water_availability: number;
  infrastructure_condition: number;
  hospital_accessibility: number;
  risk_score: number;
  risk_level: RiskLevel;
  risk_factors: Record<string, number>;
  resource_demand: ResourceBundle;
  assigned_resources: ResourceBundle;
  unmet_demand_ratio: number;
}

export interface CityState {
  city_id: string;
  city_name: string;
  tick: number;
  zones: ZoneState[];
  infrastructure: InfrastructureAsset[];
  available_resources: ResourceBundle;
}

export interface HeatwaveScenarioConfig {
  scenario_id: string;
  name: string;
  crisis_type: string;
  base_temperature_c: number;
  duration_hours: number;
  water_scarcity_factor: number;
  grid_stress_factor: number;
  random_seed: number;
}

export interface ZoneRecommendation {
  zone_id: string;
  zone_name: string;
  urgency_score: number;
  risk_level: RiskLevel;
  immediate_threats: string[];
  recommended_action: string;
  requested_resources: ResourceBundle;
  rationale: string;
}

export interface AgentAssessment {
  agent_id: string;
  agent_name: string;
  domain: string;
  city_severity_index: number;
  critical_zone_ids: string[];
  identified_constraints: string[];
  zone_recommendations: ZoneRecommendation[];
  executive_summary: string;
}

export interface AgentConflictRecord {
  zone_id: string;
  zone_name: string;
  fire_urgency: number;
  infra_urgency: number;
  divergence_delta: number;
  winning_domain: string;
  arbitration_reason: string;
}

export interface ZoneDecisionRecord {
  decision_id: string;
  zone_id: string;
  zone_name: string;
  priority_rank: number;
  priority_score: number;
  risk_score: number;
  selected_action: string;
  recommended_bundle: ResourceBundle;
  relevant_factors: Record<string, number>;
  reasoning: string;
  alternative_considered: string;
  rejection_reason: string;
}

export interface MultiAgentCouncilReport {
  strategy: AllocationStrategy;
  fire_emergency_assessment: AgentAssessment;
  infrastructure_assessment: AgentAssessment;
  detected_conflicts: AgentConflictRecord[];
  authority_directives: ZoneDecisionRecord[];
  city_wide_summary: string;
  strategy_tradeoff_explanation: string;
}

export interface SimulationMetrics {
  initial_avg_risk: number;
  final_avg_risk: number;
  risk_reduction_pct: number;
  population_protected: number;
  population_protected_pct: number;
  emergency_effectiveness: number;
  resource_utilization_pct: number;
  unmet_demand_pct: number;
  resource_wastage_pct: number;
  allocation_fairness_jain: number;
  vulnerability_outcome_equity: number;
  estimated_cost_inr_lakhs: number;
  composite_score: number;
  metric_weights: Record<string, number>;
}

export interface SimulationTimelineEvent {
  step: number;
  phase: string;
  title: string;
  detail: string;
}

export interface SimulationResult {
  simulation_id: string;
  created_at: string;
  scenario: HeatwaveScenarioConfig;
  strategy: AllocationStrategy;
  initial_crisis_city: CityState;
  final_city: CityState;
  unallocated_resources: ResourceBundle;
  council_report: MultiAgentCouncilReport;
  metrics: SimulationMetrics;
  timeline_events: SimulationTimelineEvent[];
  temporal_trajectory?: SimulationTickSnapshot[];
}

export interface StrategyComparisonReport {
  scenario: HeatwaveScenarioConfig;
  results_by_strategy: Record<string, SimulationResult>;
  recommended_strategy: AllocationStrategy;
  comparison_summary: string;
}

export interface SimulationHistoryItem {
  simulation_id: string;
  created_at: string;
  scenario_name: string;
  strategy: AllocationStrategy;
  base_temperature_c: number;
  duration_hours: number;
  initial_avg_risk: number;
  final_avg_risk: number;
  risk_reduction_pct: number;
  population_protected: number;
  allocation_fairness_jain: number;
  composite_score: number;
  summary_text: string;
}

export interface SimulationTickSnapshot {
  tick_index: number;
  hour: number;
  avg_risk: number;
  max_temp_c: number;
  critical_zone_count: number;
  protected_population: number;
  avg_water_availability_pct: number;
}

export interface WhatIfModifications {
  label: string;
  inventory_multiplier: number;
  temperature_offset_c: number;
  water_scarcity_offset: number;
  grid_stress_offset: number;
  disable_asset_id?: string | null;
  override_strategy?: AllocationStrategy | null;
}

export interface CounterfactualComparisonReport {
  baseline: SimulationResult;
  alternative: SimulationResult;
  modifications: WhatIfModifications;
  risk_reduction_delta: number;
  final_risk_delta: number;
  protected_pop_delta: number;
  fairness_delta: number;
  vuln_equity_delta: number;
  cost_delta_lakhs: number;
  tradeoff_verdict: string;
}
