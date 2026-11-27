import { MapPin, Droplets, HeartPulse, ShieldAlert } from 'lucide-react';
import type { ZoneDecisionRecord, ZoneState } from '../../types/simulation';

interface ZoneInspectorPanelProps {
  zone: ZoneState | null;
  decision?: ZoneDecisionRecord;
}

export function ZoneInspectorPanel({ zone, decision }: ZoneInspectorPanelProps) {
  if (!zone) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 text-center text-xs text-slate-400">
        Click any zone block in the 3D city to inspect telemetry, resource dispatch, and agent reasoning.
      </div>
    );
  }

  return (
    <div className="space-y-3 rounded-xl border border-slate-800 bg-slate-900/90 p-4 text-xs shadow-xl">
      <div className="flex items-start justify-between border-b border-slate-800 pb-2.5">
        <div>
          <div className="flex items-center gap-1.5">
            <MapPin className="h-3.5 w-3.5 text-sky-400" />
            <span className="font-mono text-xs font-bold text-sky-400">{zone.zone_id}</span>
            <h3 className="font-bold text-white">{zone.name}</h3>
          </div>
          <p className="mt-0.5 text-[11px] capitalize text-slate-400">
            {zone.zone_type.replace(/_/g, ' ')} • Pop: {zone.population.toLocaleString()}
          </p>
        </div>
        <div className="text-right">
          <span className="block font-mono text-lg font-extrabold text-white">{zone.risk_score.toFixed(1)}</span>
          <span className="text-[10px] font-bold uppercase text-orange-400">{zone.risk_level} RISK</span>
        </div>
      </div>

      {/* Key Vital Telemetry */}
      <div className="grid grid-cols-3 gap-2">
        <div className="rounded-lg bg-slate-950/80 p-2">
          <span className="text-[10px] text-slate-400">Temperature</span>
          <p className="font-mono text-sm font-bold text-red-400">{zone.ambient_temp_c.toFixed(1)}°C</p>
        </div>
        <div className="rounded-lg bg-slate-950/80 p-2">
          <span className="flex items-center gap-1 text-[10px] text-slate-400">
            <Droplets className="h-3 w-3 text-cyan-400" /> Water
          </span>
          <p className="font-mono text-sm font-bold text-cyan-300">{Math.round(zone.water_availability * 100)}%</p>
        </div>
        <div className="rounded-lg bg-slate-950/80 p-2">
          <span className="flex items-center gap-1 text-[10px] text-slate-400">
            <HeartPulse className="h-3 w-3 text-rose-400" /> Vulnerability
          </span>
          <p className="font-mono text-sm font-bold text-amber-300">{Math.round(zone.vulnerability_index * 100)}%</p>
        </div>
      </div>

      {/* Resource Demand vs Dispatched */}
      <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-2.5">
        <div className="mb-1.5 flex items-center justify-between">
          <span className="font-semibold text-slate-300">Dispatched vs Demand</span>
          <span className="font-mono text-[11px] text-emerald-400">
            Fulfilled: {Math.round((1 - zone.unmet_demand_ratio) * 100)}%
          </span>
        </div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[11px]">
          <div className="flex justify-between text-slate-400">
            <span>Water Tankers:</span>
            <span className="font-mono text-white">
              {zone.assigned_resources.water_tankers} / {zone.resource_demand.water_tankers}
            </span>
          </div>
          <div className="flex justify-between text-slate-400">
            <span>Medical Units:</span>
            <span className="font-mono text-white">
              {zone.assigned_resources.medical_units} / {zone.resource_demand.medical_units}
            </span>
          </div>
          <div className="flex justify-between text-slate-400">
            <span>Cooling Units:</span>
            <span className="font-mono text-white">
              {zone.assigned_resources.cooling_units} / {zone.resource_demand.cooling_units}
            </span>
          </div>
          <div className="flex justify-between text-slate-400">
            <span>Personnel:</span>
            <span className="font-mono text-white">
              {zone.assigned_resources.emergency_personnel} / {zone.resource_demand.emergency_personnel}
            </span>
          </div>
        </div>
      </div>

      {/* Explainable Decision Trace for Selected Zone */}
      {decision && (
        <div className="space-y-1.5 rounded-lg border border-sky-500/30 bg-sky-950/20 p-2.5">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1 font-bold text-sky-300">
              <ShieldAlert className="h-3.5 w-3.5" /> Authority Directive #{decision.priority_rank}
            </span>
            <span className="font-mono text-[10px] text-slate-400">{decision.decision_id}</span>
          </div>
          <p className="text-[11px] leading-relaxed text-slate-200">{decision.reasoning}</p>
          <p className="text-[10px] text-amber-300/90">
            <strong>Trade-off Rejected:</strong> {decision.rejection_reason}
          </p>
        </div>
      )}
    </div>
  );
}
