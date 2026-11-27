import { useEffect, useState } from 'react';
import { Activity, Bot, History, Scale, ShieldCheck } from 'lucide-react';
import { civicApi } from './services/api';
import type {
  AllocationStrategy,
  CityState,
  HeatwaveScenarioConfig,
  SimulationHistoryItem,
  SimulationResult,
  StrategyComparisonReport,
} from './types/simulation';
import { CityScene } from './components/scene/CityScene';
import { ScenarioConfigurator } from './components/panels/ScenarioConfigurator';
import { ZoneInspectorPanel } from './components/panels/ZoneInspectorPanel';
import { AgentCouncilPanel } from './components/panels/AgentCouncilPanel';
import { StrategyComparisonPanel } from './components/analytics/StrategyComparisonPanel';
import { WhatIfTemporalPanel } from './components/analytics/WhatIfTemporalPanel';
import { HistoryReplayPanel } from './components/panels/HistoryReplayPanel';

type BottomTab = 'agents' | 'comparison' | 'whatif' | 'history';

export function App() {
  const [baselineCity, setBaselineCity] = useState<CityState | null>(null);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [comparison, setComparison] = useState<StrategyComparisonReport | null>(null);
  const [history, setHistory] = useState<SimulationHistoryItem[]>([]);
  const [selectedZoneId, setSelectedZoneId] = useState<string>('Z6');
  const [viewMode, setViewMode] = useState<'post' | 'pre'>('post');
  const [activeTab, setActiveTab] = useState<BottomTab>('agents');
  const [isDrawerExpanded, setIsDrawerExpanded] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [isComparing, setIsComparing] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [scenario, setScenario] = useState<HeatwaveScenarioConfig>({
    scenario_id: 'heatwave_mvp_v1',
    name: 'Severe Urban Heatwave Crisis',
    crisis_type: 'urban_heatwave',
    base_temperature_c: 46.5,
    duration_hours: 48,
    water_scarcity_factor: 0.35,
    grid_stress_factor: 0.25,
    random_seed: 42,
  });
  const [strategy, setStrategy] = useState<AllocationStrategy>('balanced_priority');

  const refreshHistory = async () => {
    try {
      const data = await civicApi.getHistory(20);
      setHistory(data.runs);
    } catch {
      // ignore if backend not started yet
    }
  };

  useEffect(() => {
    civicApi
      .getBaselineCity()
      .then((city) => {
        setBaselineCity(city);
        setErrorMsg(null);
      })
      .catch((err) => setErrorMsg(err.message));
    refreshHistory();
  }, []);

  const handleRunSimulation = async () => {
    setIsRunning(true);
    setErrorMsg(null);
    try {
      const sim = await civicApi.runSimulation(scenario, strategy);
      setResult(sim);
      setViewMode('post');
      await refreshHistory();
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Simulation failed');
    } finally {
      setIsRunning(false);
    }
  };

  const handleCompareStrategies = async () => {
    setIsComparing(true);
    setErrorMsg(null);
    try {
      const comp = await civicApi.compareStrategies(scenario);
      setComparison(comp);
      setActiveTab('comparison');
      await refreshHistory();
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Strategy comparison failed');
    } finally {
      setIsComparing(false);
    }
  };

  const handleLoadSimulation = async (simId: string) => {
    try {
      const loaded = await civicApi.getSimulation(simId);
      setResult(loaded);
      setScenario(loaded.scenario);
      setStrategy(loaded.strategy);
      setViewMode('post');
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to load simulation');
    }
  };

  const displayedCity: CityState | null = result
    ? viewMode === 'post'
      ? result.final_city
      : result.initial_crisis_city
    : baselineCity;

  const selectedZone = displayedCity?.zones.find((z) => z.zone_id === selectedZoneId) || null;
  const selectedDecision = result?.council_report.authority_directives.find(
    (d) => d.zone_id === selectedZoneId
  );

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-slate-950 text-slate-100">
      <header className="flex h-13 shrink-0 items-center justify-between border-b border-slate-800 bg-slate-950/95 px-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-500/20 text-sky-400">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-tight text-white">
              CIVICVERSE AI <span className="ml-1.5 text-xs font-normal text-slate-400">Aurelia Metro Digital Twin</span>
            </h1>
          </div>
        </div>

        {result && (
          <div className="hidden items-center gap-4 text-xs lg:flex">
            <div className="rounded-md border border-slate-800 bg-slate-900 px-3 py-1">
              <span className="text-slate-400">Mean Risk: </span>
              <span className="font-mono font-bold text-red-400">{result.metrics.initial_avg_risk}</span>
              <span className="text-slate-500"> → </span>
              <span className="font-mono font-bold text-emerald-400">{result.metrics.final_avg_risk}</span>
            </div>
            <div className="rounded-md border border-slate-800 bg-slate-900 px-3 py-1">
              <span className="text-slate-400">Protected: </span>
              <span className="font-mono font-bold text-sky-400">
                {result.metrics.population_protected.toLocaleString()} ({result.metrics.population_protected_pct}%)
              </span>
            </div>
            <div className="rounded-md border border-slate-800 bg-slate-900 px-3 py-1">
              <span className="text-slate-400">Fairness (Jain): </span>
              <span className="font-mono font-bold text-amber-300">{result.metrics.allocation_fairness_jain}</span>
            </div>
            <div className="rounded-md border border-sky-500/40 bg-sky-500/10 px-3 py-1">
              <span className="text-sky-300">Score: </span>
              <span className="font-mono font-bold text-white">{result.metrics.composite_score}/100</span>
            </div>
          </div>
        )}
      </header>

      {errorMsg && (
        <div className="bg-red-950/90 px-4 py-1.5 text-xs text-red-200 border-b border-red-800">
          Backend Connection Notice: {errorMsg}
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">
        <aside className="w-88 shrink-0 space-y-3 overflow-y-auto border-r border-slate-800 bg-slate-950/95 p-3">
          <ScenarioConfigurator
            scenario={scenario}
            strategy={strategy}
            viewMode={viewMode}
            isRunning={isRunning}
            isComparing={isComparing}
            onChangeScenario={(patch) => setScenario((prev) => ({ ...prev, ...patch }))}
            onChangeStrategy={setStrategy}
            onChangeViewMode={setViewMode}
            onRunSimulation={handleRunSimulation}
            onCompareStrategies={handleCompareStrategies}
          />
          <ZoneInspectorPanel zone={selectedZone} decision={selectedDecision} />
        </aside>

        <main className="flex flex-1 flex-col overflow-hidden">
          <div className="relative flex-1">
            <CityScene
              city={displayedCity}
              selectedZoneId={selectedZoneId}
              onSelectZone={(id) => id && setSelectedZoneId(id)}
            />
          </div>

          <section className={`${isDrawerExpanded ? "h-[74vh]" : "h-72"} shrink-0 flex flex-col border-t border-slate-800 bg-slate-950 transition-all duration-200`}>
            <div className="flex items-center gap-1 border-b border-slate-800 px-3 py-1.5 text-xs">
              <button
                onClick={() => setActiveTab('agents')}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 font-semibold transition ${
                  activeTab === 'agents' ? 'bg-sky-500/20 text-sky-300' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Bot className="h-3.5 w-3.5" /> Multi-Agent Council &amp; Decisions
              </button>
              <button
                onClick={() => setActiveTab('comparison')}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 font-semibold transition ${
                  activeTab === 'comparison' ? 'bg-amber-500/20 text-amber-300' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Scale className="h-3.5 w-3.5" /> Strategy Comparison
              </button>
              <button
                onClick={() => setActiveTab('history')}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 font-semibold transition ${
                  activeTab === 'history' ? 'bg-emerald-500/20 text-emerald-300' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <History className="h-3.5 w-3.5" /> History &amp; Replay
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('whatif')}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 font-semibold transition ${
                  activeTab === 'whatif' ? 'bg-purple-500/20 text-purple-300' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Temporal & What-If Lab
              </button>
              <button
                type="button"
                onClick={() => setIsDrawerExpanded((prev) => !prev)}
                className="ml-auto rounded-md border border-slate-700 bg-slate-800/90 px-2.5 py-1 text-[11px] font-semibold text-sky-300 hover:border-sky-500/50 hover:bg-slate-800"
              >
                {isDrawerExpanded ? 'Restore Split View' : 'Expand Panel'}
              </button>
              {result && (
                <span className="ml-2 flex items-center gap-1 font-mono text-[11px] text-slate-400">
                  <Activity className="h-3 w-3 text-emerald-400" /> {result.simulation_id}
                </span>
              )}
            </div>

            <div className="flex-1 overflow-y-auto">
              {activeTab === 'agents' && (
                <AgentCouncilPanel
                  report={result?.council_report || null}
                  onSelectZone={(id) => setSelectedZoneId(id)}
                />
              )}
              {activeTab === 'comparison' && <StrategyComparisonPanel comparison={comparison} />}
              {activeTab === 'whatif' && (
                <WhatIfTemporalPanel result={result} scenario={scenario} strategy={strategy} />
              )}
              {activeTab === 'history' && (
                <HistoryReplayPanel
                  currentResult={result}
                  history={history}
                  onLoadSimulation={handleLoadSimulation}
                  onReplayStepChange={setViewMode}
                />
              )}
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

export default App;
