import { useState } from 'react';
import { History, PlayCircle, RotateCcw } from 'lucide-react';
import type { SimulationHistoryItem, SimulationResult } from '../../types/simulation';

interface HistoryReplayPanelProps {
  currentResult: SimulationResult | null;
  history: SimulationHistoryItem[];
  onLoadSimulation: (simulationId: string) => void;
  onReplayStepChange: (mode: 'pre' | 'post') => void;
}

export function HistoryReplayPanel({
  currentResult,
  history,
  onLoadSimulation,
  onReplayStepChange,
}: HistoryReplayPanelProps) {
  const [activeReplayStep, setActiveReplayStep] = useState<number>(5);

  const triggerReplay = () => {
    if (!currentResult) return;
    setActiveReplayStep(1);
    onReplayStepChange('pre');
    let step = 1;
    const interval = setInterval(() => {
      step += 1;
      setActiveReplayStep(step);
      if (step >= 4) {
        onReplayStepChange('post');
      }
      if (step >= currentResult.timeline_events.length) {
        clearInterval(interval);
      }
    }, 650);
  };

  return (
    <div className="grid grid-cols-1 gap-4 p-4 text-xs md:grid-cols-2">
      <div className="space-y-2.5 rounded-xl border border-slate-800 bg-slate-900/90 p-3">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 font-bold text-slate-200">
            <PlayCircle className="h-4 w-4 text-sky-400" /> Execution Timeline Replay
          </span>
          {currentResult && (
            <button
              onClick={triggerReplay}
              className="flex items-center gap-1 rounded bg-sky-500/20 px-2.5 py-1 font-semibold text-sky-300 hover:bg-sky-500/30"
            >
              <RotateCcw className="h-3 w-3" /> Replay Run
            </button>
          )}
        </div>

        {currentResult ? (
          <div className="space-y-2">
            {currentResult.timeline_events.map((ev) => {
              const reached = ev.step <= activeReplayStep;
              return (
                <div
                  key={ev.step}
                  className={`rounded-lg border p-2 transition ${
                    reached
                      ? 'border-sky-500/40 bg-slate-950 text-slate-200'
                      : 'border-slate-800/60 bg-slate-950/30 text-slate-500'
                  }`}
                >
                  <div className="flex justify-between font-mono text-[10px]">
                    <span className="font-bold text-sky-400">
                      STEP {ev.step} • {ev.phase}
                    </span>
                  </div>
                  <p className="mt-0.5 font-semibold">{ev.title}</p>
                  <p className="text-[11px] text-slate-400">{ev.detail}</p>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-slate-400">Run or load a simulation to replay execution steps.</p>
        )}
      </div>

      <div className="space-y-2.5 rounded-xl border border-slate-800 bg-slate-900/90 p-3">
        <div className="flex items-center gap-1.5 font-bold text-slate-200">
          <History className="h-4 w-4 text-amber-400" /> Persisted Simulation Runs ({history.length})
        </div>
        <div className="max-h-72 space-y-2 overflow-y-auto pr-1">
          {history.length === 0 ? (
            <p className="text-slate-400">No persisted runs yet.</p>
          ) : (
            history.map((run) => (
              <button
                key={run.simulation_id}
                onClick={() => onLoadSimulation(run.simulation_id)}
                className={`w-full rounded-lg border p-2.5 text-left transition ${
                  currentResult?.simulation_id === run.simulation_id
                    ? 'border-amber-400/60 bg-amber-500/10'
                    : 'border-slate-800 bg-slate-950/80 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-sky-400">{run.simulation_id}</span>
                  <span className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] uppercase text-amber-300">
                    {run.strategy}
                  </span>
                </div>
                <div className="mt-1 flex justify-between text-[11px] text-slate-300">
                  <span>{run.base_temperature_c}°C ({run.duration_hours}h)</span>
                  <span className="font-mono text-emerald-400">
                    Risk -{run.risk_reduction_pct}% • Score {run.composite_score}
                  </span>
                </div>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
