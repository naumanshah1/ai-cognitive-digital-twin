import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  Server,
  Database,
  Cpu,
  Bot,
  History,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  ArrowRight,
} from 'lucide-react';
import { apiClient } from '../services/api';
import { useAuth } from '../context/AuthContext';
import type { HealthResponse, ReadinessResponse, HistoryItem } from '../types/api';
import { MetricCard } from '../components/common/MetricCard';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';

export const OverviewPage: React.FC = () => {
  const { user, targetUserId } = useAuth();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [recentRuns, setRecentRuns] = useState<HistoryItem[]>([]);
  const [totalRuns, setTotalRuns] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOverviewData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Fetch liveness
      const healthRes = await apiClient.getHealth();
      setHealth(healthRes);

      // 2. Fetch readiness (database & LLM)
      try {
        const readyRes = await apiClient.getReadiness();
        setReadiness(readyRes);
      } catch (err: unknown) {
        console.warn('Readiness check failed or degraded:', err);
        setReadiness(null);
      }

      // 3. Fetch authenticated user's recent execution history
      try {
        const historyRes = await apiClient.getExecutionHistory({ page: 1, limit: 5 });
        setRecentRuns(historyRes.items);
        setTotalRuns(historyRes.total);
      } catch (err: unknown) {
        console.warn('Execution history fetch failed:', err);
        setRecentRuns([]);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to connect to backend service';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOverviewData();
  }, [user]);

  const dbStatus = readiness?.components?.database?.status;
  const modelsStatus = readiness?.components?.models?.status || readiness?.components?.ml_pipeline?.status;

  if (loading) {
    return <LoadingSpinner message="Checking backend diagnostics and loading telemetry..." fullHeight />;
  }

  return (
    <div className="space-y-6">
      {/* Page Title & Context Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            System Overview
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Real-time infrastructure health, cognitive model readiness, and audit records for{' '}
            <span className="font-semibold text-slate-700 dark:text-slate-300">
              {user?.id || 'synthetic session'}
            </span>
            .
          </p>
        </div>
        <button
          type="button"
          onClick={fetchOverviewData}
          className="inline-flex items-center space-x-2 px-3.5 py-2 text-xs font-medium rounded-lg text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 transition shadow-xs"
        >
          <Activity className="w-4 h-4 text-indigo-500" aria-hidden="true" />
          <span>Refresh Telemetry</span>
        </button>
      </div>

      {error && (
        <ErrorAlert
          title="Backend Connection Warning"
          message={error}
          onRetry={fetchOverviewData}
        />
      )}

      {/* Top Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="API Service (Liveness)"
          value={health?.status === 'ok' ? 'Operational' : 'Unavailable'}
          icon={Activity}
          subtitle={`Version: ${health?.version || 'Unknown'}`}
          statusVariant={health?.status === 'ok' ? 'success' : 'danger'}
        />
        <MetricCard
          title="PostgreSQL Readiness"
          value={dbStatus ? dbStatus.toUpperCase() : 'Unknown'}
          icon={Database}
          subtitle={dbStatus ? `Pool latency: ${readiness?.components?.database?.latency_ms?.toFixed(1) || '0'}ms` : 'Unconfirmed dependency'}
          statusVariant={
            dbStatus === 'ready'
              ? 'success'
              : dbStatus === 'degraded'
              ? 'warning'
              : 'danger'
          }
        />
        <MetricCard
          title="Cognitive Model Engine"
          value={modelsStatus ? modelsStatus.toUpperCase() : 'Unknown'}
          icon={Cpu}
          subtitle={modelsStatus ? 'LangGraph node executor' : 'Unconfirmed dependency'}
          statusVariant={
            modelsStatus === 'ready'
              ? 'success'
              : modelsStatus === 'degraded'
              ? 'warning'
              : 'neutral'
          }
        />
        <MetricCard
          title="Audited Executions"
          value={totalRuns}
          icon={History}
          subtitle="User runs in PostgreSQL"
          statusVariant="neutral"
        />
      </div>

      {/* Readiness vs Liveness Clarification Box */}
      <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <Server className="w-4 h-4 text-indigo-600 dark:text-indigo-400" aria-hidden="true" />
          Subsystem Diagnostics (Liveness vs. Readiness)
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-4">
          A successful HTTP 200 on <code>/health</code> confirms only that FastAPI is responding. True readiness on <code>/health/ready</code> verifies live PostgreSQL queries and ML model components.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="p-3 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
            <div className="flex items-center justify-between text-xs font-medium">
              <span className="text-slate-600 dark:text-slate-300">FastAPI Process</span>
              {health?.status === 'ok' ? (
                <span className="flex items-center text-emerald-600 dark:text-emerald-400">
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Live
                </span>
              ) : (
                <span className="flex items-center text-rose-600 dark:text-rose-400">
                  <XCircle className="w-3.5 h-3.5 mr-1" /> Down
                </span>
              )}
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Environment: <span className="font-mono">{health?.environment || 'unknown'}</span>
            </div>
          </div>

          <div className="p-3 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
            <div className="flex items-center justify-between text-xs font-medium">
              <span className="text-slate-600 dark:text-slate-300">PostgreSQL DB</span>
              {dbStatus === 'ready' ? (
                <span className="flex items-center text-emerald-600 dark:text-emerald-400">
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Connected
                </span>
              ) : dbStatus ? (
                <span className="flex items-center text-rose-600 dark:text-rose-400">
                  <XCircle className="w-3.5 h-3.5 mr-1" /> {dbStatus}
                </span>
              ) : (
                <span className="flex items-center text-amber-500">
                  <HelpCircle className="w-3.5 h-3.5 mr-1" /> Unknown
                </span>
              )}
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Pool verified via <code>SELECT 1</code>
            </div>
          </div>

          <div className="p-3 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
            <div className="flex items-center justify-between text-xs font-medium">
              <span className="text-slate-600 dark:text-slate-300">Cognitive Models</span>
              {modelsStatus === 'ready' ? (
                <span className="flex items-center text-emerald-600 dark:text-emerald-400">
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Ready
                </span>
              ) : modelsStatus ? (
                <span className="flex items-center text-amber-500">
                  <AlertTriangle className="w-3.5 h-3.5 mr-1" /> {modelsStatus}
                </span>
              ) : (
                <span className="flex items-center text-slate-400">
                  <HelpCircle className="w-3.5 h-3.5 mr-1" /> Unknown
                </span>
              )}
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              LangGraph cognitive twin agent
            </div>
          </div>
        </div>
      </div>

      {/* Quick Launchpad & Recent Runs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quick Launch Cards */}
        <div className="lg:col-span-1 space-y-3">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
            Cognitive Modules
          </h3>
          <Link
            to="/agent"
            className="block p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-indigo-500 transition shadow-xs group"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400">
                  <Bot className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-slate-900 dark:text-slate-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                    Agent Workspace
                  </div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">
                    Run autonomous multi-step reasoning
                  </div>
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-500 transition-transform group-hover:translate-x-1" />
            </div>
          </Link>

          <Link
            to="/drift"
            className="block p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-indigo-500 transition shadow-xs group"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-lg bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400">
                  <Activity className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-slate-900 dark:text-slate-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                    Drift Detection
                  </div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">
                    Inspect KS & PSI statistical tests
                  </div>
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-500 transition-transform group-hover:translate-x-1" />
            </div>
          </Link>

          <Link
            to="/simulation"
            className="block p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-indigo-500 transition shadow-xs group"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400">
                  <TrendingUp className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-sm font-semibold text-slate-900 dark:text-slate-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                    What-if Simulation
                  </div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">
                    Simulate behavioural parameter shifts
                  </div>
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-500 transition-transform group-hover:translate-x-1" />
            </div>
          </Link>
        </div>

        {/* Recent Audit / Execution History */}
        <div className="lg:col-span-2">
          <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                  Recent Agent Executions (Target: {targetUserId})
                </h3>
                <Link
                  to="/history"
                  className="text-xs font-medium text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300"
                >
                  View All History &rarr;
                </Link>
              </div>

              {recentRuns.length === 0 ? (
                <div className="py-8 text-center text-slate-500 text-xs">
                  No execution records found for the active user identity. Run an agent query to generate audit records.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400">
                        <th className="pb-2 font-medium">Request ID</th>
                        <th className="pb-2 font-medium">Target User</th>
                        <th className="pb-2 font-medium">Status</th>
                        <th className="pb-2 font-medium">Goal Summary</th>
                        <th className="pb-2 font-medium">Latency</th>
                        <th className="pb-2 font-medium text-right">Timestamp</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {recentRuns.map((run) => (
                        <tr key={run.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                          <td className="py-2.5 font-mono text-slate-600 dark:text-slate-300 truncate max-w-[120px]">
                            {run.request_id}
                          </td>
                          <td className="py-2.5 text-slate-700 dark:text-slate-300 font-medium">
                            {run.user_id}
                          </td>
                          <td className="py-2.5">
                            <StatusBadge status={run.status} size="sm" />
                          </td>
                          <td className="py-2.5 text-slate-500 truncate max-w-[180px]">
                            {run.user_goal}
                          </td>
                          <td className="py-2.5 text-slate-500">
                            {run.execution_latency ? `${(run.execution_latency * 1000).toFixed(0)} ms` : 'N/A'}
                          </td>
                          <td className="py-2.5 text-right text-slate-400">
                            {new Date(run.created_at).toLocaleTimeString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
              <span>Audited under PostgreSQL tenant ownership</span>
              <span>Authorization authoritative</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
