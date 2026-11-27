import type {
  AllocationStrategy,
  CityState,
  HeatwaveScenarioConfig,
  SimulationHistoryItem,
  SimulationResult,
  StrategyComparisonReport,
} from '../types/simulation';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

export async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`API Error (${response.status}): ${errorBody || response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export const civicApi = {
  health: () => apiFetch<{ status: string; service: string; port: number; database_dialect: string }>('/health'),
  getBaselineCity: () => apiFetch<CityState>('/api/city'),
  runSimulation: (scenario: Partial<HeatwaveScenarioConfig>, strategy: AllocationStrategy) =>
    apiFetch<SimulationResult>('/api/simulations/run', {
      method: 'POST',
      body: JSON.stringify({ scenario, strategy }),
    }),
  compareStrategies: (scenario: Partial<HeatwaveScenarioConfig>) =>
    apiFetch<StrategyComparisonReport>('/api/simulations/compare', {
      method: 'POST',
      body: JSON.stringify({ scenario }),
    }),
  getHistory: (limit = 20) => apiFetch<{ runs: SimulationHistoryItem[] }>(`/api/simulations/history?limit=${limit}`),
  getSimulation: (simulationId: string) => apiFetch<SimulationResult>(`/api/simulations/${simulationId}`),
};
