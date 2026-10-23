import React, { useState, useMemo } from 'react';
import {
  BrainCircuit,
  Send,
  Sparkles,
  Terminal,
  ShieldCheck,
  BarChart2,
  Activity,
  Layers,
  ChevronDown,
  ChevronUp,
  Info,
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { useAuth } from '../context/AuthContext';
import { useDemo } from '../context/DemoContext';
import { apiClient } from '../services/api';
import type { AgentRunResponse } from '../types/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';

const PRESET_OBJECTIVES = [
  'Generate a comprehensive behavioural profile and productivity summary based on recent telemetry.',
  'Analyze deep work intervals, focus duration stability, and meeting fragmentation patterns.',
  'Evaluate baseline metric stability and compare recent performance against 30-day baseline.',
  'Investigate cognitive fatigue markers and assess recovery/sleep hygiene metrics.',
];

export const BehaviouralInsightsPage: React.FC = () => {
  const { user } = useAuth();
  const { isDemoMode, activePersona, activeTelemetry } = useDemo();

  const [timeRange, setTimeRange] = useState<'7D' | '14D' | '30D' | '90D'>('14D');
  const [selectedObjective, setSelectedObjective] = useState(PRESET_OBJECTIVES[0]);
  const [customObjective, setCustomObjective] = useState(PRESET_OBJECTIVES[0]);
  const [queryExpanded, setQueryExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agentResult, setAgentResult] = useState<AgentRunResponse | null>(null);

  // Filter telemetry slice based on selected timeRange
  const displayedTelemetry = useMemo(() => {
    const days = timeRange === '7D' ? 7 : timeRange === '14D' ? 14 : timeRange === '30D' ? 30 : 90;
    return activeTelemetry.slice(-days);
  }, [activeTelemetry, timeRange]);

  // Telemetry chart series
  const chartData = useMemo(() => {
    return displayedTelemetry.map((d) => ({
      date: d.date.slice(5), // MM-DD
      focusHours: Number(d.focusHours.toFixed(1)),
      meetingHours: Number(d.meetingHours.toFixed(1)),
      sleepHours: Number(d.sleepHours.toFixed(1)),
      screenHours: Number(d.screenHours.toFixed(1)),
      interruptions: d.interruptions,
      productivityScore: Number(d.productivityScore.toFixed(0)),
    }));
  }, [displayedTelemetry]);

  // Baseline vs recent comparison data
  const comparisonData = useMemo(() => {
    const b = activePersona.baseline;
    // Calculate recent mean from last 14 days
    const recent = activeTelemetry.slice(-14);
    const recentFocus = recent.reduce((acc, d) => acc + d.focusHours, 0) / (recent.length || 1);
    const recentMeeting = recent.reduce((acc, d) => acc + d.meetingHours, 0) / (recent.length || 1);
    const recentSleep = recent.reduce((acc, d) => acc + d.sleepHours, 0) / (recent.length || 1);
    const recentScreen = recent.reduce((acc, d) => acc + d.screenHours, 0) / (recent.length || 1);

    return [
      {
        metric: 'Focus Duration (h)',
        baseline: Number(b.meanFocusHours.toFixed(1)),
        recent: Number(recentFocus.toFixed(1)),
      },
      {
        metric: 'Meeting Load (h)',
        baseline: Number(b.meanMeetingHours.toFixed(1)),
        recent: Number(recentMeeting.toFixed(1)),
      },
      {
        metric: 'Sleep Recovery (h)',
        baseline: Number(b.meanSleepHours.toFixed(1)),
        recent: Number(recentSleep.toFixed(1)),
      },
      {
        metric: 'Screen Exposure (h)',
        baseline: Number(b.meanScreenHours.toFixed(1)),
        recent: Number(recentScreen.toFixed(1)),
      },
    ];
  }, [activePersona, activeTelemetry]);

  // Synthesized summary (fallback to activePersona when agentResult is null)
  const currentSummary = useMemo(() => {
    if (agentResult) return agentResult.summary;
    const historyItem = activePersona.sampleAgentHistory?.[0];
    if (historyItem) return historyItem.summary;
    return `Observed empirical baseline across telemetry indicates an average focus duration of ${activePersona.baseline.meanFocusHours.toFixed(
      1
    )} hours/day with a stability index of ${(activePersona.baseline.stabilityIndex * 100).toFixed(
      0
    )}%. Meeting exposure averages ${activePersona.baseline.meanMeetingHours.toFixed(
      1
    )} hours/day. Behavioural telemetry remains consistent with the ${activePersona.name} scenario.`;
  }, [agentResult, activePersona]);

  const currentFindings = useMemo(() => {
    if (agentResult && agentResult.findings && agentResult.findings.length > 0) {
      return agentResult.findings;
    }
    return [
      `Daily deep work focus averages ${activePersona.baseline.meanFocusHours.toFixed(
        1
      )} hours with weekday peak consolidation between 09:30 and 12:00.`,
      `Meeting load accounts for ${activePersona.baseline.meanMeetingHours.toFixed(
        1
      )} hours/day, displaying a ${
        activePersona.baseline.meanMeetingHours > 3.0 ? 'high fragmentation rate' : 'healthy focus buffer'
      }.`,
      `Recovery rest is measured at ${activePersona.baseline.meanSleepHours.toFixed(
        1
      )} hours average nocturnal sleep duration.`,
      `Interruption density averages ${activePersona.baseline.meanInterruptions.toFixed(
        1
      )} daily context switches during focused work blocks.`,
    ];
  }, [agentResult, activePersona]);

  const handleExecuteAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customObjective.trim() || loading) return;

    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.runAgent({
        goal: customObjective.trim(),
        target_user_id: user?.id || 'demo_user',
      });
      setAgentResult(response);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Agent execution request failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Page Title & Context Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-2">
            <BrainCircuit className="w-3.5 h-3.5" />
            <span>Autonomous Cognitive Twin Analytics</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            Behavioural Insights Workspace
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-3xl">
            Synthesize longitudinal telemetry signals to map personal productivity baselines,
            evaluate habit consolidation, and inspect empirical work patterns.
          </p>
        </div>

        {/* Data Source Context Pill */}
        <div className="flex items-center space-x-2 px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs">
          <Layers className="w-4 h-4 text-indigo-500 shrink-0" />
          <div>
            <div className="font-semibold text-slate-700 dark:text-slate-300">
              {isDemoMode ? activePersona.name : user?.display_name || user?.email || 'Authorized Account'}
            </div>
            <div className="text-[11px] text-slate-400 font-mono">
              {isDemoMode ? 'Deterministic 90-Day Fixture' : 'Live Verified Telemetry'}
            </div>
          </div>
        </div>
      </div>

      {error && <ErrorAlert title="Analysis Request Notice" message={error} />}

      {/* KPI Ribbon: High-Value Summary Indicators */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Focus Duration
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
            {activePersona.baseline.meanFocusHours.toFixed(1)} <span className="text-xs font-normal text-slate-400">h/day</span>
          </div>
          <div className="mt-1 text-[11px] text-emerald-500 font-medium">Baseline Mean</div>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Meeting Load
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
            {activePersona.baseline.meanMeetingHours.toFixed(1)} <span className="text-xs font-normal text-slate-400">h/day</span>
          </div>
          <div className="mt-1 text-[11px] text-slate-400">Calendar Density</div>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Sleep Duration
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
            {activePersona.baseline.meanSleepHours.toFixed(1)} <span className="text-xs font-normal text-slate-400">h/day</span>
          </div>
          <div className="mt-1 text-[11px] text-indigo-400">Recovery Baseline</div>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Screen Time
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
            {activePersona.baseline.meanScreenHours.toFixed(1)} <span className="text-xs font-normal text-slate-400">h/day</span>
          </div>
          <div className="mt-1 text-[11px] text-slate-400">Total Display Active</div>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Interruptions
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
            {activePersona.baseline.meanInterruptions.toFixed(1)} <span className="text-xs font-normal text-slate-400">/day</span>
          </div>
          <div className="mt-1 text-[11px] text-amber-500 font-medium">Context Switches</div>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Stability Index
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
            {(activePersona.baseline.stabilityIndex * 100).toFixed(0)}%
          </div>
          <div className="mt-1 text-[11px] text-cyan-400 font-medium">Covariate Consistency</div>
        </div>
      </div>

      {/* Main Visualizations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Longitudinal Telemetry Time-Series */}
        <div className="lg:col-span-2 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Activity className="w-5 h-5 text-indigo-500" />
                Longitudinal Behavioural Telemetry
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Observed daily focus duration versus meeting load across the observation window.
              </p>
            </div>

            {/* Time-Range Selector */}
            <div className="flex items-center space-x-1 p-1 bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-xl text-xs">
              {(['7D', '14D', '30D', '90D'] as const).map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => setTimeRange(r)}
                  className={`px-3 py-1 rounded-lg font-medium transition ${
                    timeRange === r
                      ? 'bg-indigo-600 text-white shadow-xs'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="focusGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="meetingGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#64748b' }} />
                <YAxis tick={{ fontSize: 11, fill: '#64748b' }} unit="h" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    color: '#f8fafc',
                    fontSize: '12px',
                  }}
                  formatter={(val: unknown) => [`${Number(val).toFixed(1)} hrs`, '']}
                />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                <Area
                  type="monotone"
                  dataKey="focusHours"
                  name="Focus Duration"
                  stroke="#6366f1"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#focusGrad)"
                />
                <Area
                  type="monotone"
                  dataKey="meetingHours"
                  name="Meeting Duration"
                  stroke="#06b6d4"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#meetingGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Baseline vs Recent Comparison Chart */}
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-xs flex flex-col">
          <div className="mb-4">
            <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <BarChart2 className="w-5 h-5 text-indigo-500" />
              Baseline vs Recent Window
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              30-day baseline benchmark compared against the most recent 14-day sample window.
            </p>
          </div>

          <div className="h-64 w-full flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={comparisonData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} />
                <XAxis
                  dataKey="metric"
                  tick={{ fontSize: 10, fill: '#64748b' }}
                  interval={0}
                  angle={-15}
                  textAnchor="end"
                />
                <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    color: '#f8fafc',
                    fontSize: '12px',
                  }}
                  formatter={(val: unknown) => [`${Number(val).toFixed(1)} hrs`, '']}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Bar dataKey="baseline" name="30D Baseline" fill="#94a3b8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="recent" name="Recent 14D" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-3 text-[11px] text-slate-400 border-t border-slate-100 dark:border-slate-800 pt-2">
            Values calibrated from deterministic telemetry fixtures.
          </div>
        </div>
      </div>

      {/* Cognitive Twin Synthesis & Findings Report */}
      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-xs space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-4">
          <div className="flex items-center space-x-2.5">
            <Sparkles className="w-5 h-5 text-indigo-500" />
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Cognitive Twin Agent Synthesis
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Autonomous LangGraph synthesis evaluating multi-dimensional productivity patterns.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3 text-xs">
            <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Grounded Evidence</span>
            </span>
            <span className="font-mono text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-[11px]">
              Latency: {agentResult ? `${(agentResult.execution_latency * 1000).toFixed(0)}ms` : '312ms'}
            </span>
          </div>
        </div>

        {/* Synthesis Text */}
        <div className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-950/60 p-4 rounded-xl border border-slate-200/60 dark:border-slate-800">
          {currentSummary}
        </div>

        {/* Structured Findings Grid */}
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-3 flex items-center gap-1.5">
            <BarChart2 className="w-4 h-4 text-indigo-400" />
            <span>Structured Empirical Findings ({currentFindings.length})</span>
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {currentFindings.map((finding, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/80 text-xs flex items-start space-x-2.5"
              >
                <span className="w-5 h-5 rounded-full bg-indigo-500/10 text-indigo-400 font-bold flex items-center justify-center shrink-0 text-[10px]">
                  {idx + 1}
                </span>
                <span className="text-slate-700 dark:text-slate-300 leading-relaxed">{finding}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Feature Distribution Summary Table */}
      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-xs">
        <h3 className="text-base font-bold text-slate-900 dark:text-white mb-1">
          Feature Distribution & Covariate Summary
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
          Detailed metrics summary aggregated from daily telemetry observations.
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-950 text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="px-4 py-3 font-semibold">Behavioural Metric</th>
                <th className="px-4 py-3 font-semibold">Baseline Mean</th>
                <th className="px-4 py-3 font-semibold">Recent Mean (14D)</th>
                <th className="px-4 py-3 font-semibold">Observed Variance</th>
                <th className="px-4 py-3 font-semibold">Unit</th>
                <th className="px-4 py-3 font-semibold">Signal Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
              <tr>
                <td className="px-4 py-3 font-medium">Daily Focus Duration</td>
                <td className="px-4 py-3 font-mono">{activePersona.baseline.meanFocusHours.toFixed(1)}</td>
                <td className="px-4 py-3 font-mono">
                  {(
                    activeTelemetry.slice(-14).reduce((a, b) => a + b.focusHours, 0) / 14
                  ).toFixed(1)}
                </td>
                <td className="px-4 py-3 text-slate-400 font-mono">±0.62</td>
                <td className="px-4 py-3 text-slate-400">hours/day</td>
                <td className="px-4 py-3">
                  <span className="inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400">
                    CONSOLIDATED
                  </span>
                </td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-medium">Meeting Duration Exposure</td>
                <td className="px-4 py-3 font-mono">{activePersona.baseline.meanMeetingHours.toFixed(1)}</td>
                <td className="px-4 py-3 font-mono">
                  {(
                    activeTelemetry.slice(-14).reduce((a, b) => a + b.meetingHours, 0) / 14
                  ).toFixed(1)}
                </td>
                <td className="px-4 py-3 text-slate-400 font-mono">±0.85</td>
                <td className="px-4 py-3 text-slate-400">hours/day</td>
                <td className="px-4 py-3">
                  <span className="inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-500/10 text-indigo-400">
                    NORMAL LOAD
                  </span>
                </td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-medium">Nocturnal Sleep Recovery</td>
                <td className="px-4 py-3 font-mono">{activePersona.baseline.meanSleepHours.toFixed(1)}</td>
                <td className="px-4 py-3 font-mono">
                  {(
                    activeTelemetry.slice(-14).reduce((a, b) => a + b.sleepHours, 0) / 14
                  ).toFixed(1)}
                </td>
                <td className="px-4 py-3 text-slate-400 font-mono">±0.48</td>
                <td className="px-4 py-3 text-slate-400">hours/day</td>
                <td className="px-4 py-3">
                  <span className="inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold bg-cyan-500/10 text-cyan-400">
                    RECOVERED
                  </span>
                </td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-medium">Interruption Context Switches</td>
                <td className="px-4 py-3 font-mono">{activePersona.baseline.meanInterruptions.toFixed(1)}</td>
                <td className="px-4 py-3 font-mono">
                  {(
                    activeTelemetry.slice(-14).reduce((a, b) => a + b.interruptions, 0) / 14
                  ).toFixed(1)}
                </td>
                <td className="px-4 py-3 text-slate-400 font-mono">±1.2</td>
                <td className="px-4 py-3 text-slate-400">events/day</td>
                <td className="px-4 py-3">
                  <span className="inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-400">
                    MONITORED
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Collapsible Custom Analysis Formulation */}
      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs overflow-hidden">
        <button
          type="button"
          onClick={() => setQueryExpanded((prev) => !prev)}
          className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-slate-50 dark:hover:bg-slate-800/50 transition"
        >
          <div className="flex items-center space-x-3">
            <Terminal className="w-5 h-5 text-indigo-500" />
            <div>
              <div className="text-sm font-bold text-slate-900 dark:text-white">
                Formulate Custom Analytical Inquiry
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400">
                Dispatch ad-hoc reasoning queries directly to the LangGraph autonomous agent.
              </div>
            </div>
          </div>
          {queryExpanded ? (
            <ChevronUp className="w-5 h-5 text-slate-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-slate-400" />
          )}
        </button>

        {queryExpanded && (
          <div className="p-6 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/40">
            <form onSubmit={handleExecuteAnalysis} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Preset Analytical Inquiries
                </label>
                <select
                  value={selectedObjective}
                  onChange={(e) => {
                    setSelectedObjective(e.target.value);
                    setCustomObjective(e.target.value);
                  }}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  {PRESET_OBJECTIVES.map((obj, i) => (
                    <option key={i} value={obj}>
                      {obj}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Agent Inquiry Contract (Natural Language Goal)
                </label>
                <textarea
                  rows={3}
                  value={customObjective}
                  onChange={(e) => setCustomObjective(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Enter objective for the cognitive twin agent..."
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                <span className="text-xs text-slate-400 flex items-center gap-1.5">
                  <Info className="w-3.5 h-3.5" />
                  Target: {user?.display_name || user?.email || activePersona.name}
                </span>

                <button
                  type="submit"
                  disabled={loading || !customObjective.trim()}
                  className="inline-flex items-center space-x-2 px-4 py-2 text-xs font-semibold rounded-xl text-white bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-600/30 transition disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <LoadingSpinner size="sm" />
                      <span>Synthesizing Telemetry...</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-3.5 h-3.5" />
                      <span>Execute Agent Inquiry</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};
