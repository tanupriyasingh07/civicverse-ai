import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Award } from 'lucide-react';
import type { StrategyComparisonReport } from '../../types/simulation';

interface StrategyComparisonPanelProps {
  comparison: StrategyComparisonReport | null;
}

export function StrategyComparisonPanel({ comparison }: StrategyComparisonPanelProps) {
  if (!comparison) {
    return (
      <div className="p-6 text-center text-xs text-slate-400">
        Click <strong>Compare All 4</strong> to evaluate all response strategies against identical heatwave conditions.
      </div>
    );
  }

  const rows = Object.entries(comparison.results_by_strategy).map(([key, res]) => ({
    strategy: key.replace('_priority', '').toUpperCase(),
    rawKey: key,
    compositeScore: res.metrics.composite_score,
    riskReduction: res.metrics.risk_reduction_pct,
    protectedPct: res.metrics.population_protected_pct,
    fairnessPct: Math.round(res.metrics.allocation_fairness_jain * 100),
    vulnEquityPct: Math.round((res.metrics.vulnerability_outcome_equity ?? res.metrics.allocation_fairness_jain) * 100),
    unmetPct: res.metrics.unmet_demand_pct,
    costLakhs: res.metrics.estimated_cost_inr_lakhs,
    protectedPop: res.metrics.population_protected,
  }));

  return (
    <div className="space-y-4 p-4 text-xs">
      <div className="flex items-start gap-2.5 rounded-xl border border-emerald-500/35 bg-emerald-950/20 p-3">
        <Award className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
        <div>
          <span className="font-bold text-emerald-300">
            Recommended Strategy: {comparison.recommended_strategy.toUpperCase()}
          </span>
          <p className="mt-0.5 text-[11px] text-slate-200">{comparison.comparison_summary}</p>
        </div>
      </div>

      <div className="h-56 w-full rounded-xl border border-slate-800 bg-slate-900/90 p-3">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="strategy" tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <Tooltip
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '12px' }}
            />
            <Legend wrapperStyle={{ fontSize: '11px' }} />
            <Bar dataKey="compositeScore" name="Composite Score" fill="#38bdf8" radius={[4, 4, 0, 0]} />
            <Bar dataKey="riskReduction" name="Risk Reduction %" fill="#10b981" radius={[4, 4, 0, 0]} />
            <Bar dataKey="vulnEquityPct" name="Vuln. Outcome Equity %" fill="#a855f7" radius={[4, 4, 0, 0]} />
            <Bar dataKey="fairnessPct" name="Jain Fairness %" fill="#f59e0b" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/90">
        <table className="w-full text-left text-[11px]">
          <thead className="border-b border-slate-800 bg-slate-950 text-slate-400">
            <tr>
              <th className="px-3 py-2">Strategy</th>
              <th className="px-3 py-2">Composite</th>
              <th className="px-3 py-2">Risk Drop</th>
              <th className="px-3 py-2">Protected Pop</th>
              <th className="px-3 py-2">Jain Fairness</th>
              <th className="px-3 py-2">Vuln. Equity</th>
              <th className="px-3 py-2">Unmet Demand</th>
              <th className="px-3 py-2">Est. Cost</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80 text-slate-200">
            {rows.map((r) => (
              <tr
                key={r.rawKey}
                className={r.rawKey === comparison.recommended_strategy ? 'bg-emerald-500/10' : ''}
              >
                <td className="px-3 py-2 font-bold">{r.strategy}</td>
                <td className="px-3 py-2 font-mono text-sky-400">{r.compositeScore}</td>
                <td className="px-3 py-2 font-mono text-emerald-400">{r.riskReduction}%</td>
                <td className="px-3 py-2 font-mono">{r.protectedPop.toLocaleString()}</td>
                <td className="px-3 py-2 font-mono text-amber-300">{(r.fairnessPct / 100).toFixed(2)}</td>
                <td className="px-3 py-2 font-mono text-purple-300">{(r.vulnEquityPct / 100).toFixed(2)}</td>
                <td className="px-3 py-2 font-mono text-rose-300">{r.unmetPct}%</td>
                <td className="px-3 py-2 font-mono">?{r.costLakhs}L</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
