import { Flame, Play, Scale, Eye } from 'lucide-react';
import type { AllocationStrategy, HeatwaveScenarioConfig } from '../../types/simulation';

interface ScenarioConfiguratorProps {
  scenario: HeatwaveScenarioConfig;
  strategy: AllocationStrategy;
  viewMode: 'post' | 'pre';
  isRunning: boolean;
  isComparing: boolean;
  onChangeScenario: (patch: Partial<HeatwaveScenarioConfig>) => void;
  onChangeStrategy: (strategy: AllocationStrategy) => void;
  onChangeViewMode: (mode: 'post' | 'pre') => void;
  onRunSimulation: () => void;
  onCompareStrategies: () => void;
}

const STRATEGIES: { value: AllocationStrategy; label: string; desc: string }[] = [
  { value: 'balanced_priority', label: 'Balanced Multi-Factor', desc: 'Risk + Vulnerability + Infra + Pop' },
  { value: 'risk_priority', label: 'Peak Risk Priority', desc: 'Targets highest hazard score first' },
  { value: 'vulnerability_priority', label: 'Vulnerability Equity', desc: 'Protects fragile populations first' },
  { value: 'population_priority', label: 'Population Scale', desc: 'Maximizes raw headcount coverage' },
];

export function ScenarioConfigurator({
  scenario,
  strategy,
  viewMode,
  isRunning,
  isComparing,
  onChangeScenario,
  onChangeStrategy,
  onChangeViewMode,
  onRunSimulation,
  onCompareStrategies,
}: ScenarioConfiguratorProps) {
  return (
    <div className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/90 p-4 shadow-xl backdrop-blur-md">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Flame className="h-4 w-4 text-orange-400" />
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Heatwave Crisis Parameters
          </h2>
        </div>
        <span className="rounded bg-orange-500/15 px-2 py-0.5 font-mono text-[11px] font-semibold text-orange-300">
          Seed #{scenario.random_seed}
        </span>
      </div>

      <div className="space-y-3 text-xs">
        <div>
          <div className="mb-1 flex justify-between text-slate-300">
            <span>Peak Ambient Temperature</span>
            <span className="font-mono font-bold text-red-400">{scenario.base_temperature_c.toFixed(1)}°C</span>
          </div>
          <input
            type="range"
            min={38}
            max={54}
            step={0.5}
            value={scenario.base_temperature_c}
            onChange={(e) => onChangeScenario({ base_temperature_c: parseFloat(e.target.value) })}
            className="w-full accent-orange-500"
          />
        </div>

        <div>
          <div className="mb-1 flex justify-between text-slate-300">
            <span>Heatwave Duration</span>
            <span className="font-mono font-bold text-amber-300">{scenario.duration_hours} hrs</span>
          </div>
          <input
            type="range"
            min={12}
            max={144}
            step={6}
            value={scenario.duration_hours}
            onChange={(e) => onChangeScenario({ duration_hours: parseInt(e.target.value, 10) })}
            className="w-full accent-amber-500"
          />
        </div>

        <div className="grid grid-cols-2 gap-2.5">
          <div>
            <div className="mb-1 flex justify-between text-[11px] text-slate-400">
              <span>Water Scarcity</span>
              <span className="font-mono text-cyan-300">{Math.round(scenario.water_scarcity_factor * 100)}%</span>
            </div>
            <input
              type="range"
              min={0.1}
              max={0.8}
              step={0.05}
              value={scenario.water_scarcity_factor}
              onChange={(e) => onChangeScenario({ water_scarcity_factor: parseFloat(e.target.value) })}
              className="w-full accent-cyan-500"
            />
          </div>
          <div>
            <div className="mb-1 flex justify-between text-[11px] text-slate-400">
              <span>Grid Stress</span>
              <span className="font-mono text-purple-300">{Math.round(scenario.grid_stress_factor * 100)}%</span>
            </div>
            <input
              type="range"
              min={0.1}
              max={0.8}
              step={0.05}
              value={scenario.grid_stress_factor}
              onChange={(e) => onChangeScenario({ grid_stress_factor: parseFloat(e.target.value) })}
              className="w-full accent-purple-500"
            />
          </div>
        </div>
      </div>

      <div className="space-y-1.5">
        <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          Response Allocation Strategy
        </label>
        <div className="grid grid-cols-1 gap-1.5">
          {STRATEGIES.map((s) => (
            <button
              key={s.value}
              onClick={() => onChangeStrategy(s.value)}
              className={`flex flex-col rounded-lg border px-3 py-2 text-left transition ${
                strategy === s.value
                  ? 'border-sky-500 bg-sky-500/15 text-white'
                  : 'border-slate-800 bg-slate-950/60 text-slate-300 hover:border-slate-700'
              }`}
            >
              <span className="text-xs font-semibold">{s.label}</span>
              <span className="text-[10px] text-slate-400">{s.desc}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/80 p-2 text-xs">
        <span className="flex items-center gap-1.5 text-slate-400">
          <Eye className="h-3.5 w-3.5 text-sky-400" /> 3D Twin State:
        </span>
        <div className="flex gap-1">
          <button
            onClick={() => onChangeViewMode('pre')}
            className={`rounded px-2 py-1 text-[11px] font-semibold ${
              viewMode === 'pre' ? 'bg-red-500/20 text-red-300 ring-1 ring-red-500/50' : 'text-slate-400'
            }`}
          >
            Unmitigated Crisis
          </button>
          <button
            onClick={() => onChangeViewMode('post')}
            className={`rounded px-2 py-1 text-[11px] font-semibold ${
              viewMode === 'post' ? 'bg-emerald-500/20 text-emerald-300 ring-1 ring-emerald-500/50' : 'text-slate-400'
            }`}
          >
            Post-Response
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 pt-1">
        <button
          onClick={onRunSimulation}
          disabled={isRunning}
          className="flex items-center justify-center gap-1.5 rounded-lg bg-sky-500 px-3 py-2.5 text-xs font-bold text-slate-950 shadow-lg shadow-sky-500/20 transition hover:bg-sky-400 disabled:opacity-50"
        >
          <Play className="h-3.5 w-3.5 fill-current" />
          {isRunning ? 'Simulating...' : 'Execute Run'}
        </button>
        <button
          onClick={onCompareStrategies}
          disabled={isComparing}
          className="flex items-center justify-center gap-1.5 rounded-lg border border-amber-500/40 bg-amber-500/15 px-3 py-2.5 text-xs font-bold text-amber-300 transition hover:bg-amber-500/25 disabled:opacity-50"
        >
          <Scale className="h-3.5 w-3.5" />
          {isComparing ? 'Comparing...' : 'Compare All 4'}
        </button>
      </div>
    </div>
  );
}
