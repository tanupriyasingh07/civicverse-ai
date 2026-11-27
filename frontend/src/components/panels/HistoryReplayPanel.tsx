import { useEffect, useRef, useState } from 'react';
import { History, Play, Radio, RotateCcw } from 'lucide-react';
import type { SimulationHistoryItem, SimulationResult } from '../../types/simulation';

interface HistoryReplayPanelProps {
  currentResult: SimulationResult | null;
  history: SimulationHistoryItem[];
  onLoadSimulation: (simulationId: string) => void | Promise<void>;
  onReplayStepChange?: (step: number) => void;
}

export function HistoryReplayPanel({
  currentResult,
  history,
  onLoadSimulation,
  onReplayStepChange,
}: HistoryReplayPanelProps) {
  const [replayIndex, setReplayIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const events = currentResult?.timeline_events ?? [];

  useEffect(() => {
    setReplayIndex(events.length);
    setIsPlaying(false);
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, [currentResult?.simulation_id, events.length]);

  const startWebSocketReplay = () => {
    if (!currentResult) return;
    if (wsRef.current) {
      wsRef.current.close();
    }

    setReplayIndex(0);
    setIsPlaying(true);

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//localhost:8001/ws/simulation/${currentResult.simulation_id}`;

    try {
      const socket = new WebSocket(wsUrl);
      wsRef.current = socket;

      socket.onopen = () => setWsConnected(true);
      socket.onmessage = (msg) => {
        const payload = JSON.parse(msg.data);
        if (payload.type === 'timeline_event' && payload.data?.step) {
          setReplayIndex(payload.data.step);
          onReplayStepChange?.(payload.data.step);
        } else if (payload.type === 'simulation_complete') {
          setReplayIndex(events.length);
          onReplayStepChange?.(events.length);
          setIsPlaying(false);
          setWsConnected(false);
        }
      };
      socket.onerror = () => {
        setWsConnected(false);
        setIsPlaying(false);
        setReplayIndex(events.length);
      };
      socket.onclose = () => setWsConnected(false);
    } catch {
      setIsPlaying(false);
      setReplayIndex(events.length);
    }
  };

  return (
    <div className="grid grid-cols-1 gap-4 p-4 text-xs md:grid-cols-2">
      <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-3">
        <div className="mb-2 flex items-center justify-between">
          <span className="flex items-center gap-1.5 font-bold text-sky-300">
            <Play className="h-4 w-4" /> WebSocket Step-by-Step Replay
          </span>
          <div className="flex items-center gap-1.5">
            {wsConnected && (
              <span className="flex items-center gap-1 rounded bg-emerald-500/20 px-1.5 py-0.5 text-[10px] text-emerald-300">
                <Radio className="h-3 w-3 animate-pulse" /> WS Live
              </span>
            )}
            <button
              type="button"
              disabled={!currentResult || isPlaying}
              onClick={startWebSocketReplay}
              className="flex items-center gap-1 rounded bg-sky-600 px-2.5 py-1 text-[11px] font-semibold text-white hover:bg-sky-500 disabled:opacity-40"
            >
              <RotateCcw className="h-3 w-3" /> Stream Replay
            </button>
          </div>
        </div>

        {!currentResult ? (
          <p className="py-6 text-center text-slate-400">Run or load a simulation to replay its execution timeline.</p>
        ) : (
          <div className="space-y-2">
            {events.slice(0, replayIndex).map((ev) => (
              <div
                key={ev.step}
                className="rounded-lg border border-slate-800 bg-slate-950/80 p-2.5 transition-all"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white">
                    Step {ev.step}: {ev.title}
                  </span>
                  <span className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-sky-300">
                    {ev.phase}
                  </span>
                </div>
                <p className="mt-1 text-[11px] text-slate-300">{ev.detail}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-3">
        <div className="mb-2 flex items-center gap-1.5 font-bold text-slate-200">
          <History className="h-4 w-4 text-emerald-400" /> Persisted Simulation Runs ({history.length})
        </div>
        {history.length === 0 ? (
          <p className="py-6 text-center text-slate-400">No persisted runs yet.</p>
        ) : (
          <div className="max-h-64 space-y-2 overflow-y-auto pr-1">
            {history.map((item) => (
              <div
                key={item.simulation_id}
                onClick={() => onLoadSimulation(item.simulation_id)}
                className="cursor-pointer rounded-lg border border-slate-800 bg-slate-950/75 p-2.5 transition hover:border-emerald-500/50"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-emerald-300">{item.simulation_id}</span>
                  <span className="rounded bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] uppercase text-slate-300">
                    {item.strategy}
                  </span>
                </div>
                <p className="mt-1 text-[11px] text-slate-300">{item.summary_text}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
