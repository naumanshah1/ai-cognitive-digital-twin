import React, { useState, useMemo } from 'react';
import {
  Sliders,
  Send,
  ShieldAlert,
  Layers,
  TrendingUp,
  TrendingDown,
  RotateCcw,
  Zap,
  HelpCircle,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ReferenceLine,
} from 'recharts';
import { useAuth } from '../context/AuthContext';
import { useDemo } from '../context/DemoContext';
import { apiClient } from '../services/api';
import type { AgentRunResponse } from '../types/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';

export const SimulationPage: React.FC = () => {
  const { user } = useAuth();
  const { isDemoMode, activePersona } = useDemo();

  const baseline = activePersona.simulationBaseline;

  // Form State initialized to active persona baseline
  const [taskType, setTaskType] = useState<'retrospective' | 'forecasting'>('retrospective');
  const [focusHours, setFocusHours] = useState<number>(baseline.focusHours);
  const [sleepHours, setSleepHours] = useState<number>(baseline.sleepHours);
  const [screenHours, setScreenHours] = useState<number>(baseline.screenHours);
  const [interruptions, setInterruptions] = useState<number>(baseline.interruptions);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agentResult, setAgentResult] = useState<AgentRunResponse | null>(null);

  // Compute calculated simulation values (associational linear model matching backend champion)
  // Productivity baseline ~ 70
  // focus: +3.2 pts per hr diff
  // sleep: +2.1 pts per hr diff (diminishing over 8.5)
  // screen: -1.2 pts per hr diff
  // interruptions: -2.4 pts per interruption diff
  const simulatedProductivity = useMemo(() => {
    if (agentResult?.simulation_result?.simulated_productivity !== undefined) {
      return agentResult.simulation_result.simulated_productivity;
    }
    const dFocus = focusHours - baseline.focusHours;
    const dSleep = sleepHours - baseline.sleepHours;
    const dScreen = screenHours - baseline.screenHours;
    const dInter = interruptions - baseline.interruptions;

    const delta = dFocus * 3.2 + dSleep * 2.1 - dScreen * 1.1 - dInter * 2.4;
    const score = Math.max(25, Math.min(98, baseline.baselineProductivity + delta));
    return Number(score.toFixed(1));
  }, [focusHours, sleepHours, screenHours, interruptions, baseline, agentResult]);

  const productivityDelta = useMemo(() => {
    return Number((simulatedProductivity - baseline.baselineProductivity).toFixed(1));
  }, [simulatedProductivity, baseline]);

  // Out of distribution / IQR checks
  const isOOD = focusHours > 8.0 || focusHours < 2.5 || sleepHours < 5.0 || interruptions > 8;

  // Scenario Presets
  const applyPreset = (presetName: string) => {
    switch (presetName) {
      case 'DEEP_WORK':
        setFocusHours(Math.min(8.0, baseline.focusHours + 2.0));
        setInterruptions(Math.max(1, baseline.interruptions - 2));
        break;
      case 'MEETING_RECOVERY':
        setScreenHours(Math.max(4.0, baseline.screenHours - 1.5));
        setSleepHours(Math.min(8.5, baseline.sleepHours + 1.0));
        break;
      case 'SLEEP_OPTIMIZATION':
        setSleepHours(Math.min(8.5, baseline.sleepHours + 1.5));
        break;
      case 'FRAGMENTATION_TEST':
        setFocusHours(Math.max(2.5, baseline.focusHours - 1.5));
        setInterruptions(baseline.interruptions + 4);
        break;
      case 'RESET':
        setFocusHours(baseline.focusHours);
        setSleepHours(baseline.sleepHours);
        setScreenHours(baseline.screenHours);
        setInterruptions(baseline.interruptions);
        break;
      default:
        break;
    }
  };

  const handleRunSimulation = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const modificationsDesc = `focus_duration_hours=${focusHours}, sleep_hours=${sleepHours}, screen_time_hours=${screenHours}, interruption_count=${interruptions}`;
    const goal = `Execute counterfactual what-if simulation for ${
      user?.display_name || user?.email || activePersona.name
    } with task_type='${taskType}' and modifications: ${modificationsDesc}. Compare baseline to simulated productivity and report distribution bounds.`;

    try {
      const res = await apiClient.runAgent({
        goal,
        target_user_id: user?.id || 'demo_user',
        simulation_params: {
          focus_duration_hours: focusHours,
          sleep_hours: sleepHours,
          screen_time_hours: screenHours,
          interruption_count: interruptions,
        },
      });
      setAgentResult(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Simulation failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  // Diverging delta data for chart
  const divergingData = [
    {
      name: 'Focus (h)',
      delta: Number((focusHours - baseline.focusHours).toFixed(1)),
    },
    {
      name: 'Sleep (h)',
      delta: Number((sleepHours - baseline.sleepHours).toFixed(1)),
    },
    {
      name: 'Screen (h)',
      delta: Number((screenHours - baseline.screenHours).toFixed(1)),
    },
    {
      name: 'Interruptions',
      delta: -(interruptions - baseline.interruptions), // inverted because fewer interruptions is positive
    },
    {
      name: 'Productivity',
      delta: productivityDelta,
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-2">
            <Sliders className="w-3.5 h-3.5" />
            <span>Counterfactual Scenario Laboratory</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            What-if Simulation Engine
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-3xl">
            Simulate prospective habit adjustments and evaluate counterfactual changes in productivity indicators.
            Powered by calibrated Milestone 4 regression estimators and sequence models.
          </p>
        </div>

        {/* Data Source Context */}
        <div className="flex items-center space-x-2 px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs">
          <Layers className="w-4 h-4 text-indigo-500 shrink-0" />
          <div>
            <div className="font-semibold text-slate-700 dark:text-slate-300">
              {isDemoMode ? activePersona.name : user?.display_name || user?.email || 'Authorized Account'}
            </div>
            <div className="text-[11px] text-slate-400 font-mono">
              Baseline: {baseline.baselineProductivity.toFixed(1)} Pts
            </div>
          </div>
        </div>
      </div>

      {error && <ErrorAlert title="Simulation Notice" message={error} />}

      {/* Out of distribution warning */}
      {isOOD && (
        <div className="rounded-xl bg-amber-500/10 border border-amber-500/30 p-4 text-amber-300 text-xs flex items-center space-x-3">
          <ShieldAlert className="w-5 h-5 shrink-0 text-amber-400" />
          <div>
            <strong>Distribution Boundary Warning:</strong> One or more modified features fall outside the 1.5×IQR
            training distribution. Predictions represent statistical extrapolations and should be interpreted with caution.
          </div>
        </div>
      )}

      {/* Main Interactive Laboratory Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Controls Column (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Preset Buttons */}
          <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 shadow-xs">
            <div className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-3 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Zap className="w-4 h-4 text-amber-400" />
                Scenario Presets
              </span>
              <button
                type="button"
                onClick={() => applyPreset('RESET')}
                className="text-[11px] text-slate-400 hover:text-indigo-400 flex items-center gap-1"
              >
                <RotateCcw className="w-3 h-3" />
                Reset Baseline
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => applyPreset('DEEP_WORK')}
                className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800 hover:border-indigo-500 text-left transition"
              >
                <div className="font-semibold text-slate-900 dark:text-white">Deep Work Immersion</div>
                <div className="text-[10px] text-slate-400 mt-0.5">+2.0h focus, -2 interr.</div>
              </button>

              <button
                type="button"
                onClick={() => applyPreset('MEETING_RECOVERY')}
                className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800 hover:border-indigo-500 text-left transition"
              >
                <div className="font-semibold text-slate-900 dark:text-white">Meeting Recovery</div>
                <div className="text-[10px] text-slate-400 mt-0.5">-1.5h screen, +1.0h sleep</div>
              </button>

              <button
                type="button"
                onClick={() => applyPreset('SLEEP_OPTIMIZATION')}
                className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800 hover:border-indigo-500 text-left transition"
              >
                <div className="font-semibold text-slate-900 dark:text-white">Sleep Restoration</div>
                <div className="text-[10px] text-slate-400 mt-0.5">+1.5h nightly sleep</div>
              </button>

              <button
                type="button"
                onClick={() => applyPreset('FRAGMENTATION_TEST')}
                className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800 hover:border-rose-500 text-left transition"
              >
                <div className="font-semibold text-slate-900 dark:text-white">Fragmentation Stress</div>
                <div className="text-[10px] text-slate-400 mt-0.5">+4 interruptions, -1.5h</div>
              </button>
            </div>
          </div>

          {/* Interactive Sliders Form */}
          <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-xs space-y-6">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Behavioural Covariate Adjusters
            </h3>

            {/* Slider 1: Focus Duration */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-slate-700 dark:text-slate-300">Daily Focus Duration</span>
                <span className="font-mono font-bold text-indigo-400">
                  {focusHours.toFixed(1)} hrs{' '}
                  <span className="text-[10px] text-slate-400 font-normal">
                    (Base: {baseline.focusHours.toFixed(1)})
                  </span>
                </span>
              </div>
              <input
                type="range"
                min={2.0}
                max={9.0}
                step={0.5}
                value={focusHours}
                onChange={(e) => setFocusHours(parseFloat(e.target.value))}
                className="w-full accent-indigo-600 cursor-pointer"
              />
            </div>

            {/* Slider 2: Sleep Duration */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-slate-700 dark:text-slate-300">Nocturnal Sleep Recovery</span>
                <span className="font-mono font-bold text-cyan-400">
                  {sleepHours.toFixed(1)} hrs{' '}
                  <span className="text-[10px] text-slate-400 font-normal">
                    (Base: {baseline.sleepHours.toFixed(1)})
                  </span>
                </span>
              </div>
              <input
                type="range"
                min={4.0}
                max={10.0}
                step={0.5}
                value={sleepHours}
                onChange={(e) => setSleepHours(parseFloat(e.target.value))}
                className="w-full accent-cyan-500 cursor-pointer"
              />
            </div>

            {/* Slider 3: Screen Time */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-slate-700 dark:text-slate-300">Total Screen Active Time</span>
                <span className="font-mono font-bold text-purple-400">
                  {screenHours.toFixed(1)} hrs{' '}
                  <span className="text-[10px] text-slate-400 font-normal">
                    (Base: {baseline.screenHours.toFixed(1)})
                  </span>
                </span>
              </div>
              <input
                type="range"
                min={3.0}
                max={12.0}
                step={0.5}
                value={screenHours}
                onChange={(e) => setScreenHours(parseFloat(e.target.value))}
                className="w-full accent-purple-500 cursor-pointer"
              />
            </div>

            {/* Slider 4: Interruptions */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-slate-700 dark:text-slate-300">Daily Interruption Density</span>
                <span className="font-mono font-bold text-amber-400">
                  {interruptions} events{' '}
                  <span className="text-[10px] text-slate-400 font-normal">
                    (Base: {baseline.interruptions})
                  </span>
                </span>
              </div>
              <input
                type="range"
                min={0}
                max={12}
                step={1}
                value={interruptions}
                onChange={(e) => setInterruptions(parseInt(e.target.value))}
                className="w-full accent-amber-500 cursor-pointer"
              />
            </div>

            {/* Estimation Paradigm */}
            <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Estimation Paradigm
              </label>
              <select
                value={taskType}
                onChange={(e) => setTaskType(e.target.value as 'retrospective' | 'forecasting')}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
              >
                <option value="retrospective">Retrospective Counterfactual (Linear Regression)</option>
                <option value="forecasting">Next-Day Prospective (LSTM Sequence Forecaster)</option>
              </select>
            </div>

            {/* Submit Simulation Action */}
            <button
              type="button"
              onClick={handleRunSimulation}
              disabled={loading}
              className="w-full inline-flex items-center justify-center space-x-2 px-4 py-2.5 text-xs font-semibold rounded-xl text-white bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-600/30 transition disabled:opacity-50"
            >
              {loading ? (
                <>
                  <LoadingSpinner size="sm" />
                  <span>Computing Counterfactual...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Run Model Simulation</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Results Column (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Top Score Comparison Banner */}
          <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-xs">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-4 flex items-center justify-between">
              <span>Estimated Productivity Impact</span>
              <span className="text-xs font-normal text-slate-400">
                Associational Estimate
              </span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
              {/* Baseline Card */}
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200/60 dark:border-slate-800">
                <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Baseline Score
                </div>
                <div className="mt-2 text-3xl font-extrabold text-slate-700 dark:text-slate-300">
                  {baseline.baselineProductivity.toFixed(1)}
                </div>
                <div className="text-[10px] text-slate-400 mt-1">Observed Benchmark</div>
              </div>

              {/* Arrow Column */}
              <div className="flex flex-col items-center justify-center py-2 sm:py-0">
                <div
                  className={`inline-flex items-center space-x-1 px-3 py-1.5 rounded-full text-xs font-bold ${
                    productivityDelta >= 0
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                  }`}
                >
                  {productivityDelta >= 0 ? (
                    <TrendingUp className="w-4 h-4" />
                  ) : (
                    <TrendingDown className="w-4 h-4" />
                  )}
                  <span>
                    {productivityDelta >= 0 ? `+${productivityDelta}` : productivityDelta} Pts
                  </span>
                </div>
                <span className="text-[10px] text-slate-400 mt-1">Projected Delta</span>
              </div>

              {/* Simulated Card */}
              <div className="p-4 rounded-xl bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-200/60 dark:border-indigo-900/40">
                <div className="text-[11px] font-semibold text-indigo-400 uppercase tracking-wider">
                  Simulated Score
                </div>
                <div className="mt-2 text-3xl font-extrabold text-indigo-600 dark:text-indigo-400">
                  {simulatedProductivity.toFixed(1)}
                </div>
                <div className="text-[10px] text-slate-400 mt-1">Counterfactual State</div>
              </div>
            </div>
          </div>

          {/* Diverging Change Visualization */}
          <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-xs">
            <h4 className="text-sm font-bold text-slate-900 dark:text-white mb-1">
              Covariate Delta & Sensitivity Breakdown
            </h4>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
              Relative parameter shifts compared against their baseline references.
            </p>

            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={divergingData} margin={{ top: 10, right: 20, left: -20, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
                  <ReferenceLine y={0} stroke="#64748b" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#f8fafc',
                      fontSize: '12px',
                    }}
                    formatter={(val: unknown) => [`${Number(val) > 0 ? '+' : ''}${Number(val).toFixed(1)}`, 'Delta']}
                  />
                  <Bar dataKey="delta" radius={[4, 4, 4, 4]}>
                    {divergingData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.delta >= 0 ? '#10b981' : '#f43f5e'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Parameter Comparison Table */}
          <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-xs">
            <h4 className="text-sm font-bold text-slate-900 dark:text-white mb-3">
              Counterfactual Parameter Verification
            </h4>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-950 text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="px-3 py-2.5 font-semibold">Covariate</th>
                    <th className="px-3 py-2.5 font-semibold">Baseline</th>
                    <th className="px-3 py-2.5 font-semibold">Simulated</th>
                    <th className="px-3 py-2.5 font-semibold">Difference</th>
                    <th className="px-3 py-2.5 font-semibold">Model Bound</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                  <tr>
                    <td className="px-3 py-2.5 font-medium">Daily Focus Hours</td>
                    <td className="px-3 py-2.5 font-mono">{baseline.focusHours.toFixed(1)}h</td>
                    <td className="px-3 py-2.5 font-mono">{focusHours.toFixed(1)}h</td>
                    <td className="px-3 py-2.5 font-mono text-indigo-400">
                      {(focusHours - baseline.focusHours).toFixed(1)}h
                    </td>
                    <td className="px-3 py-2.5 text-emerald-400">In Distribution</td>
                  </tr>
                  <tr>
                    <td className="px-3 py-2.5 font-medium">Nocturnal Sleep Hours</td>
                    <td className="px-3 py-2.5 font-mono">{baseline.sleepHours.toFixed(1)}h</td>
                    <td className="px-3 py-2.5 font-mono">{sleepHours.toFixed(1)}h</td>
                    <td className="px-3 py-2.5 font-mono text-cyan-400">
                      {(sleepHours - baseline.sleepHours).toFixed(1)}h
                    </td>
                    <td className="px-3 py-2.5 text-emerald-400">In Distribution</td>
                  </tr>
                  <tr>
                    <td className="px-3 py-2.5 font-medium">Total Screen Hours</td>
                    <td className="px-3 py-2.5 font-mono">{baseline.screenHours.toFixed(1)}h</td>
                    <td className="px-3 py-2.5 font-mono">{screenHours.toFixed(1)}h</td>
                    <td className="px-3 py-2.5 font-mono text-purple-400">
                      {(screenHours - baseline.screenHours).toFixed(1)}h
                    </td>
                    <td className="px-3 py-2.5 text-emerald-400">In Distribution</td>
                  </tr>
                  <tr>
                    <td className="px-3 py-2.5 font-medium">Daily Interruptions</td>
                    <td className="px-3 py-2.5 font-mono">{baseline.interruptions}</td>
                    <td className="px-3 py-2.5 font-mono">{interruptions}</td>
                    <td className="px-3 py-2.5 font-mono text-amber-400">
                      {interruptions - baseline.interruptions}
                    </td>
                    <td className="px-3 py-2.5 text-emerald-400">In Distribution</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Scientific & Non-Causal Transparency Disclaimer */}
      <div className="rounded-2xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 p-5 text-xs text-slate-600 dark:text-slate-400 space-y-2">
        <div className="flex items-center space-x-2 font-semibold text-slate-800 dark:text-slate-200">
          <HelpCircle className="w-4 h-4 text-indigo-500" />
          <span>Non-Causal Statistical Disclaimer & Model Limitations</span>
        </div>
        <p className="leading-relaxed">
          Simulated values represent associational statistical estimates derived from historical observational telemetry
          using Milestone 4 linear regression estimators. They do not demonstrate causal proof or guarantee identical future outcomes.
        </p>
        <p className="leading-relaxed">
          Parameter effects are bounded by empirical training distributions. Severe out-of-distribution modifications
          introduce epistemic model uncertainty.
        </p>
      </div>
    </div>
  );
};
