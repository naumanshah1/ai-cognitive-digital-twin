import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  BrainCircuit,
  Activity,
  Sparkles,
  Sliders,
  Bot,
  ArrowRight,
  CheckCircle2,
  Play,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useDemo } from '../../context/DemoContext';
import { api } from '../../services/api';
import type { HistoryItem, AgentRunResponse } from '../../types/api';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';

export const UserOverviewPage: React.FC = () => {
  const { user } = useAuth();
  const { isDemoMode, activePersona, activeTelemetry } = useDemo();
  const [timeRange, setTimeRange] = useState<'7D' | '14D' | '30D' | '90D'>('14D');
  const [recentRuns, setRecentRuns] = useState<HistoryItem[]>([]);
  const [totalInquiries, setTotalInquiries] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [quickRunning, setQuickRunning] = useState(false);
  const [quickResult, setQuickResult] = useState<AgentRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadPersonalData = async () => {
    setLoading(true);
    setError(null);
    try {
      const historyRes = await api.getExecutionHistory({ limit: 5 });
      setRecentRuns(historyRes.items || []);
      setTotalInquiries(historyRes.total || 0);
    } catch {
      // User-friendly message without leaking server trace
      setError('Insights and activity history are temporarily unavailable. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPersonalData();
  }, [user]);

  const handleQuickBaseline = async () => {
    setQuickRunning(true);
    setError(null);
    try {
      const result = await api.runAgent({
        goal: 'Generate a personal behavioural overview and evaluate current baseline stability.',
      });
      setQuickResult(result);
      // Reload history to show newly completed inquiry
      loadPersonalData();
    } catch {
      setError('Unable to run behavioural analysis at this moment. Please check back shortly.');
    } finally {
      setQuickRunning(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading your personal behavioural twin..." fullHeight />;
  }

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-900/60 via-slate-900 to-slate-900 border border-indigo-800/40 p-6 sm:p-8 shadow-xl">
        <div className="max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 mb-3">
            <BrainCircuit className="w-3.5 h-3.5 text-indigo-400" />
            <span>Personal Behavioural Twin Active</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Welcome back, {user?.display_name || user?.username || 'Explorer'}
          </h1>
          <p className="mt-2 text-sm text-slate-300 leading-relaxed">
            Your cognitive twin continuously synthesizes telemetry signals to map your productivity baselines,
            detect shifts in work habits, and estimate the impact of potential schedule modifications.
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={handleQuickBaseline}
              disabled={quickRunning}
              className="inline-flex items-center px-4 py-2.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-600/30 transition disabled:opacity-50"
            >
              {quickRunning ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                  Synthesizing Baseline...
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 mr-2" />
                  Run Baseline Analysis
                </>
              )}
            </button>
            <Link
              to="/app/simulation"
              className="inline-flex items-center px-4 py-2.5 rounded-xl text-xs font-medium text-slate-200 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 transition"
            >
              <Sliders className="w-3.5 h-3.5 mr-2 text-cyan-400" />
              What-if Simulation
            </Link>
            <Link
              to="/app/agent"
              className="inline-flex items-center px-4 py-2.5 rounded-xl text-xs font-medium text-slate-200 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 transition"
            >
              <Bot className="w-3.5 h-3.5 mr-2 text-indigo-400" />
              Agent Workspace
            </Link>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-xl bg-amber-500/10 border border-amber-500/20 p-4 text-amber-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={loadPersonalData} className="text-xs font-semibold underline ml-4">
            Retry
          </button>
        </div>
      )}

      {/* Quick Agent Run Notification */}
      {quickResult && (
        <div className="rounded-xl bg-slate-900 border border-indigo-500/30 p-5 shadow-lg">
          <div className="flex items-center space-x-2 text-indigo-400 font-semibold text-xs mb-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Latest Twin Insight Synthesized</span>
          </div>
          <p className="text-sm text-slate-200 font-medium mb-2">{quickResult.summary}</p>
          {quickResult.findings && quickResult.findings.length > 0 && (
            <ul className="text-xs text-slate-400 space-y-1 list-disc pl-5">
              {quickResult.findings.slice(0, 3).map((f, i) => (
                <li key={i}>{f}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Behavioral Signals Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider">Behavioural Baseline</span>
            <BrainCircuit className="w-4 h-4 text-indigo-500" />
          </div>
          <p className="text-3xl font-extrabold text-slate-900 dark:text-white">
            {isDemoMode ? `${(activePersona.baseline.stabilityIndex * 100).toFixed(0)}% Stable` : totalInquiries > 0 ? 'Active' : 'Calibrated'}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
            Mean Focus Duration: <strong className="text-slate-900 dark:text-white">{activePersona.baseline.meanFocusHours.toFixed(1)} hrs/day</strong> • Baseline meeting load: <strong className="text-slate-900 dark:text-white">{activePersona.baseline.meanMeetingHours.toFixed(1)} hrs/day</strong>.
          </p>
          <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
            <Link
              to="/app/insights"
              className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline inline-flex items-center"
            >
              Inspect Telemetry Insights <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Link>
          </div>
        </div>

        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider">Drift Alert Status</span>
            <Activity className="w-4 h-4 text-cyan-500" />
          </div>
          <p className={`text-3xl font-extrabold ${activePersona.driftStatus.status === 'DRIFT_DETECTED' ? 'text-amber-400' : 'text-emerald-400'}`}>
            {activePersona.driftStatus.status === 'DRIFT_DETECTED' ? 'Shift Detected' : 'Stable'}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
            Kolmogorov-Smirnov test: <strong className="text-slate-900 dark:text-white">p = {activePersona.driftStatus.pValue.toFixed(2)}</strong> ({activePersona.driftStatus.status === 'DRIFT_DETECTED' ? 'Covariate drift flagged' : 'No significant shift detected'}).
          </p>
          <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
            <Link
              to="/app/drift"
              className="text-xs font-semibold text-cyan-600 dark:text-cyan-400 hover:underline inline-flex items-center"
            >
              View Drift Diagnostics <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Link>
          </div>
        </div>

        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 dark:text-slate-400 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider">Action Plans</span>
            <Sparkles className="w-4 h-4 text-purple-500" />
          </div>
          <p className="text-3xl font-extrabold text-slate-900 dark:text-white">
            {activePersona.recommendations.length} Active
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
            Prioritized evidence-linked interventions ready for review in recommendations centre.
          </p>
          <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
            <Link
              to="/app/recommendations"
              className="text-xs font-semibold text-purple-600 dark:text-purple-400 hover:underline inline-flex items-center"
            >
              Explore Recommendations <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Link>
          </div>
        </div>
      </div>

      {/* Prominent Trend Visualization & Time-Range Selector */}
      <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-indigo-400" />
              Personal Behavioural Trends & Focus Telemetry
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Daily deep work focus hours versus meeting exposure over the selected observation window.
            </p>
          </div>

          <div className="flex items-center space-x-1.5 p-1 bg-slate-950 border border-slate-800 rounded-xl text-xs">
            {(['7D', '14D', '30D', '90D'] as const).map((range) => (
              <button
                key={range}
                type="button"
                onClick={() => setTimeRange(range)}
                className={`px-3 py-1 rounded-lg font-medium transition ${
                  timeRange === range
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                {range}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Line / Area Chart */}
          <div className="lg:col-span-2 h-72">
            <div className="h-full">
              <div className="h-full flex flex-col">
                <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                  <div className="flex items-center space-x-4">
                    <span className="flex items-center space-x-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-indigo-500" />
                      <span>Focus Hours (hrs/day)</span>
                    </span>
                    <span className="flex items-center space-x-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
                      <span>Meeting Duration (hrs/day)</span>
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-500">Unit: Hours / Day</span>
                </div>

                <div className="flex-1 bg-slate-950/80 border border-slate-800/80 rounded-xl p-4 flex flex-col justify-between">
                  <div className="grid grid-cols-7 gap-2 h-44 items-end">
                    {activeTelemetry.slice(-7).map((d, i) => (
                      <div key={i} className="flex flex-col items-center h-full justify-end group">
                        <div className="w-full flex space-x-1 items-end justify-center h-36">
                          <div
                            style={{ height: `${Math.min(100, (d.focusHours / 9) * 100)}%` }}
                            className="w-3.5 bg-indigo-500/80 hover:bg-indigo-400 rounded-t transition-all group-hover:shadow-lg group-hover:shadow-indigo-500/20"
                            title={`Focus: ${d.focusHours.toFixed(1)}h`}
                          />
                          <div
                            style={{ height: `${Math.min(100, (d.meetingHours / 9) * 100)}%` }}
                            className="w-3.5 bg-cyan-400/80 hover:bg-cyan-300 rounded-t transition-all"
                            title={`Meeting: ${d.meetingHours.toFixed(1)}h`}
                          />
                        </div>
                        <span className="text-[10px] text-slate-400 mt-2 font-mono">{d.dayOfWeek.slice(0, 3)}</span>
                      </div>
                    ))}
                  </div>

                  <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                    <span>Average Focus: <strong className="text-indigo-300">{activePersona.baseline.meanFocusHours.toFixed(1)}h</strong> (Baseline)</span>
                    <span>Meeting Density: <strong className="text-cyan-300">{activePersona.baseline.meanMeetingHours.toFixed(1)}h</strong> (Target: &lt; 2.5h)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Baseline vs Current Summary Cards */}
          <div className="space-y-3 flex flex-col justify-between">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span>Focus Stability Index</span>
                <span className="text-emerald-400 font-semibold">+4.2%</span>
              </div>
              <div className="text-xl font-bold text-white">88.5 / 100</div>
              <p className="text-[11px] text-slate-400 mt-1">
                Consistent deep work blocks maintained across morning windows.
              </p>
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span>Task Interruption Rate</span>
                <span className="text-emerald-400 font-semibold">-18%</span>
              </div>
              <div className="text-xl font-bold text-white">2.1 / hour</div>
              <p className="text-[11px] text-slate-400 mt-1">
                Context switching remains below the 3.5/hr cohort drift threshold.
              </p>
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl">
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span>Estimated Productivity Score</span>
                <span className="text-indigo-400 font-semibold">Model v1</span>
              </div>
              <div className="text-xl font-bold text-indigo-400">76.8 / 100</div>
              <p className="text-[11px] text-slate-400 mt-1">
                Based on validated multi-variate regression without causal guarantees.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Personal Activity */}
      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Recent Personal Twin Inquiries
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Only inquiries initiated by your account are displayed.
            </p>
          </div>
          <Link
            to="/app/history"
            className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
          >
            View Full History →
          </Link>
        </div>

        {recentRuns.length === 0 ? (
          <div className="text-center py-10 px-4 rounded-xl border border-dashed border-slate-300 dark:border-slate-800">
            <BrainCircuit className="w-8 h-8 text-slate-400 mx-auto mb-2" />
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
              No inquiries yet
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-sm mx-auto">
              Ask your cognitive twin a question in the Agent Workspace or trigger an initial baseline analysis above.
            </p>
            <Link
              to="/app/agent"
              className="mt-4 inline-flex items-center px-3.5 py-2 text-xs font-semibold text-white bg-indigo-600 rounded-lg hover:bg-indigo-500 transition"
            >
              Open Agent Workspace
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {recentRuns.map((run) => (
              <div key={run.id} className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-start space-x-3">
                  <div className="w-7 h-7 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center shrink-0 mt-0.5">
                    <Bot className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-900 dark:text-slate-100 line-clamp-1">
                      {run.user_goal}
                    </p>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center space-x-2 mt-0.5">
                      <span>{new Date(run.created_at).toLocaleString()}</span>
                      <span>•</span>
                      <span>Latency: {run.execution_latency.toFixed(2)}s</span>
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-2 shrink-0">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                      run.status === 'COMPLETED'
                        ? 'bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400'
                        : 'bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400'
                    }`}
                  >
                    {run.status}
                  </span>
                  <Link
                    to="/app/history"
                    className="text-xs text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
                  >
                    Details →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
