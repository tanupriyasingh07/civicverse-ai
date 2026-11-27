import { useState } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { FlaskConical, Play, TrendingDown, TrendingUp } from 'lucide-react';
import { runWhatIf } from '../../services/api';
import type {
  AllocationStrategy,
  CounterfactualComparisonReport,
  HeatwaveScenarioConfig,
  SimulationResult,
} from '../../types/simulation';

interface WhatIfTemporalPanelProps {
  result: SimulationResult | null;
  scenario: HeatwaveScenarioConfig;
  strategy: AllocationStrategy;
}

export function WhatIfTemporalPanel({ result, scenario, strategy }: WhatIfTemporalPanelProps) {
  const [label, setLabel] = useState('+30% Emergency Fleet Capacity');
  const [invMult, setInvMult] = useState(1.3);
  const [tempOffset, setTempOffset] = useState(0.0);
  const [disableAsset, setDisableAsset] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<CounterfactualComparisonReport | null>(null);

  const executeWhatIf = async (preset?: {
    label: string;
    inv: number;
    temp: number;
    asset: string;
  }) => {
    const activeLabel = preset ? preset.label : label;
    const activeInv = preset ? preset.inv : invMult;
    const activeTemp = preset ? preset.temp : tempOffset;
    const activeAsset = preset ? preset.asset : disableAsset;

    if (preset) {
      setLabel(preset.label);
      setInvMult(preset.inv);
      setTempOffset(preset.temp);
      setDisableAsset(preset.asset);
    }

    setLoading(true);
    try {
      const data = await runWhatIf(scenario, strategy, {
        label: activeLabel,
        inventory_multiplier: activeInv,
        temperature_offset_c: activeTemp,
        water_scarcity_offset: 0,
        grid_stress_offset: 0,
        disable_asset_id: activeAsset || null,
        override_strategy: null,
      });
      setReport(data);
    } finally {
      setLoading(false);
    }
  };

  const trajectory = result?.temporal_trajectory ?? [];

  return (
    <div className="space-y-4 p-4 text-xs">
      <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-3">
        <div className="mb-2 flex items-center justify-between">
          <span className="font-bold text-sky-300">
            6-Hour Temporal Crisis & Intervention Trajectory (Hour 0 ? Hour {scenario.duration_hours})
          </span>
          <span className="font-mono text-[10px] text-slate-400">
            {trajectory.length} discrete simulation ticks
          </span>
        </div>

        {trajectory.length === 0 ? (
          <p className="py-6 text-center text-slate-400">
            Execute a simulation run to generate the multi-hour risk & thermal trajectory.
          </p>
        ) : (
          <div className="h-52 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trajectory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis
                  dataKey="hour"
                  tickFormatter={(h) => `${h}h`}
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px' }} />
                <Area
                  type="monotone"
                  dataKey="avg_risk"
                  name="Mean City Risk"
                  stroke="#f43f5e"
                  fill="#f43f5e"
                  fillOpacity={0.2}
                />
                <Area
                  type="monotone"
                  dataKey="avg_water_availability_pct"
                  name="Water Reserve %"
                  stroke="#38bdf8"
                  fill="#38bdf8"
                  fillOpacity={0.18}
                />
                <Area
                  type="monotone"
                  dataKey="max_temp_c"
                  name="Peak Temp (?C)"
                  stroke="#f59e0b"
                  fill="#f59e0b"
                  fillOpacity={0.12}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      <div className="rounded-xl border border-purple-500/30 bg-slate-900/90 p-3">
        <div className="mb-2.5 flex flex-wrap items-center justify-between gap-2">
          <span className="flex items-center gap-1.5 font-bold text-purple-300">
            <FlaskConical className="h-4 w-4" /> Counterfactual What-If Experimentation Lab
          </span>
          <div className="flex flex-wrap gap-1.5">
            <button
              type="button"
              onClick={() =>
                executeWhatIf({ label: '+30% Fleet Capacity', inv: 1.3, temp: 0, asset: '' })
              }
              className="rounded border border-emerald-500/40 bg-emerald-950/40 px-2 py-1 text-[10px] font-semibold text-emerald-300 hover:bg-emerald-900/50"
            >
              +30% Fleet
            </button>
            <button
              type="button"
              onClick={() =>
                executeWhatIf({ label: 'Extreme +3.5?C Surge', inv: 1.0, temp: 3.5, asset: '' })
              }
              className="rounded border border-amber-500/40 bg-amber-950/40 px-2 py-1 text-[10px] font-semibold text-amber-300 hover:bg-amber-900/50"
            >
              +3.5?C Surge
            </button>
            <button
              type="button"
              onClick={() =>
                executeWhatIf({
                  label: 'Old Quarter Hospital Outage',
                  inv: 1.0,
                  temp: 0,
                  asset: 'INF-HOSP-01',
                })
              }
              className="rounded border border-rose-500/40 bg-rose-950/40 px-2 py-1 text-[10px] font-semibold text-rose-300 hover:bg-rose-900/50"
            >
              Hospital Outage
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
          <div>
            <label className="text-[10px] text-slate-400">
              Fleet Multiplier: <strong className="text-white">{invMult.toFixed(2)}x</strong>
            </label>
            <input
              type="range"
              min={0.5}
              max={2.0}
              step={0.1}
              value={invMult}
              onChange={(e) => setInvMult(parseFloat(e.target.value))}
              className="mt-1 w-full accent-purple-400"
            />
          </div>
          <div>
            <label className="text-[10px] text-slate-400">
              Temp Offset: <strong className="text-white">{tempOffset >= 0 ? `+${tempOffset}` : tempOffset}?C</strong>
            </label>
            <input
              type="range"
              min={-4}
              max={6}
              step={0.5}
              value={tempOffset}
              onChange={(e) => setTempOffset(parseFloat(e.target.value))}
              className="mt-1 w-full accent-amber-400"
            />
          </div>
          <div>
            <label className="text-[10px] text-slate-400">Inject Asset Failure</label>
            <select
              value={disableAsset}
              onChange={(e) => setDisableAsset(e.target.value)}
              className="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 text-[11px] text-slate-200"
            >
              <option value="">None (All Operational)</option>
              <option value="INF-HOSP-01">INF-HOSP-01 (Old Quarter Hospital)</option>
              <option value="INF-WTR-01">INF-WTR-01 (Canal Water Plant)</option>
              <option value="INF-PWR-01">INF-PWR-01 (Industrial Substation)</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              type="button"
              disabled={loading}
              onClick={() => executeWhatIf()}
              className="flex w-full items-center justify-center gap-1.5 rounded-lg bg-purple-600 px-3 py-1.5 font-bold text-white hover:bg-purple-500 disabled:opacity-50"
            >
              <Play className="h-3.5 w-3.5" />
              {loading ? 'Simulating...' : 'Run Counterfactual'}
            </button>
          </div>
        </div>

        {report && (
          <div className="mt-3 space-y-2 rounded-lg border border-purple-500/30 bg-slate-950/90 p-3">
            <p className="text-[11px] font-semibold text-purple-200">{report.tradeoff_verdict}</p>
            <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
              <div className="rounded border border-slate-800 bg-slate-900 p-2">
                <div className="text-[10px] text-slate-400">Residual Risk ?</div>
                <div
                  className={`mt-0.5 flex items-center gap-1 font-mono text-sm font-bold ${
                    report.final_risk_delta <= 0 ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  {report.final_risk_delta <= 0 ? (
                    <TrendingDown className="h-3.5 w-3.5" />
                  ) : (
                    <TrendingUp className="h-3.5 w-3.5" />
                  )}
                  {report.final_risk_delta >= 0 ? `+${report.final_risk_delta}` : report.final_risk_delta} pts
                </div>
              </div>
              <div className="rounded border border-slate-800 bg-slate-900 p-2">
                <div className="text-[10px] text-slate-400">Protected Pop ?</div>
                <div
                  className={`mt-0.5 font-mono text-sm font-bold ${
                    report.protected_pop_delta >= 0 ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  {report.protected_pop_delta >= 0
                    ? `+${report.protected_pop_delta.toLocaleString()}`
                    : report.protected_pop_delta.toLocaleString()}
                </div>
              </div>
              <div className="rounded border border-slate-800 bg-slate-900 p-2">
                <div className="text-[10px] text-slate-400">Vuln. Equity ?</div>
                <div className="mt-0.5 font-mono text-sm font-bold text-purple-300">
                  {report.vuln_equity_delta >= 0
                    ? `+${report.vuln_equity_delta.toFixed(3)}`
                    : report.vuln_equity_delta.toFixed(3)}
                </div>
              </div>
              <div className="rounded border border-slate-800 bg-slate-900 p-2">
                <div className="text-[10px] text-slate-400">Deployment Cost ?</div>
                <div className="mt-0.5 font-mono text-sm font-bold text-amber-300">
                  {report.cost_delta_lakhs >= 0 ? `+?${report.cost_delta_lakhs}L` : `-?${Math.abs(report.cost_delta_lakhs)}L`}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
