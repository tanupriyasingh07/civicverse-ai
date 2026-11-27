import { AlertTriangle, Bot, Flame, Wrench, Landmark } from 'lucide-react';
import type { MultiAgentCouncilReport } from '../../types/simulation';

interface AgentCouncilPanelProps {
  report: MultiAgentCouncilReport | null;
  onSelectZone: (zoneId: string) => void;
}

export function AgentCouncilPanel({ report, onSelectZone }: AgentCouncilPanelProps) {
  if (!report) {
    return (
      <div className="p-6 text-center text-xs text-slate-400">
        Execute a simulation run to convene the Fire & Emergency, Infrastructure, and City Authority agents.
      </div>
    );
  }

  return (
    <div className="space-y-4 p-4 text-xs">
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        <div className="rounded-xl border border-rose-500/30 bg-slate-900/90 p-3">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5 font-bold text-rose-300">
              <Flame className="h-4 w-4" /> Fire & Emergency
            </span>
            <span className="font-mono text-xs font-bold text-rose-400">
              {report.fire_emergency_assessment.city_severity_index}/100
            </span>
          </div>
          <p className="mt-1.5 text-[11px] text-slate-300">
            {report.fire_emergency_assessment.executive_summary}
          </p>
          {report.fire_emergency_assessment.identified_constraints.map((c, i) => (
            <p key={i} className="mt-1 rounded bg-rose-950/50 px-2 py-1 text-[10px] text-rose-200">
              ? {c}
            </p>
          ))}
        </div>

        <div className="rounded-xl border border-cyan-500/30 bg-slate-900/90 p-3">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5 font-bold text-cyan-300">
              <Wrench className="h-4 w-4" /> Infrastructure Agent
            </span>
            <span className="font-mono text-xs font-bold text-cyan-400">
              {report.infrastructure_assessment.city_severity_index}/100
            </span>
          </div>
          <p className="mt-1.5 text-[11px] text-slate-300">
            {report.infrastructure_assessment.executive_summary}
          </p>
          {report.infrastructure_assessment.identified_constraints.map((c, i) => (
            <p key={i} className="mt-1 rounded bg-cyan-950/50 px-2 py-1 text-[10px] text-cyan-200">
              ? {c}
            </p>
          ))}
        </div>

        <div className="rounded-xl border border-amber-500/30 bg-slate-900/90 p-3">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5 font-bold text-amber-300">
              <Landmark className="h-4 w-4" /> City Authority
            </span>
            <span className="rounded bg-amber-500/20 px-1.5 py-0.5 font-mono text-[10px] uppercase text-amber-300">
              {report.strategy}
            </span>
          </div>
          <p className="mt-1.5 text-[11px] text-slate-200">{report.city_wide_summary}</p>
          <p className="mt-1.5 text-[10px] text-slate-400">{report.strategy_tradeoff_explanation}</p>
        </div>
      </div>

      {report.detected_conflicts && report.detected_conflicts.length > 0 && (
        <div className="rounded-xl border border-amber-500/35 bg-amber-950/15 p-3">
          <div className="mb-2 flex items-center gap-1.5 font-bold text-amber-300">
            <AlertTriangle className="h-4 w-4" /> Inter-Agent Disagreements & Arbitration ({report.detected_conflicts.length})
          </div>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
            {report.detected_conflicts.map((c) => (
              <div
                key={c.zone_id}
                onClick={() => onSelectZone(c.zone_id)}
                className="cursor-pointer rounded-lg border border-amber-500/25 bg-slate-950/80 p-2.5 hover:border-amber-400/60"
              >
                <div className="flex items-center justify-between font-bold text-white">
                  <span>{c.zone_id} ? {c.zone_name}</span>
                  <span className="rounded bg-amber-500/20 px-1.5 py-0.5 font-mono text-[10px] text-amber-300">
                    ? {c.divergence_delta} pts ? {c.winning_domain}
                  </span>
                </div>
                <p className="mt-1 text-[11px] text-slate-300">{c.arbitration_reason}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-3">
        <div className="mb-2 flex items-center gap-1.5 font-bold text-slate-200">
          <Bot className="h-4 w-4 text-sky-400" /> Explainable Authority Directives & Counterfactual Trade-Off Audit
        </div>
        <div className="space-y-2">
          {report.authority_directives.map((d) => (
            <div
              key={d.decision_id}
              onClick={() => onSelectZone(d.zone_id)}
              className="cursor-pointer rounded-lg border border-slate-800 bg-slate-950/75 p-2.5 transition hover:border-sky-500/50"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="rounded bg-sky-500/20 px-2 py-0.5 font-mono font-bold text-sky-300">
                    Rank #{d.priority_rank}
                  </span>
                  <span className="font-bold text-white">
                    {d.zone_id} ? {d.zone_name}
                  </span>
                </div>
                <span className="font-mono text-[11px] text-slate-400">
                  Priority: {d.priority_score} | Risk: {d.risk_score}
                </span>
              </div>
              <p className="mt-1 text-[11px] text-slate-300">{d.reasoning}</p>
              <p className="mt-1 text-[10px] text-slate-400">
                <span className="font-semibold text-amber-400">Counterfactual Rejected:</span> {d.rejection_reason}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
