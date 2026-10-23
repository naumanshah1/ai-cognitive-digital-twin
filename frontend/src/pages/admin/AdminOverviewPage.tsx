import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Shield,
  Activity,
  Users,
  Database,
  Cpu,
  RefreshCw,
  ArrowRight,
} from 'lucide-react';
import { api, ApiClientError } from '../../services/api';
import type { AdminOverviewMetrics } from '../../types/api';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';

export const AdminOverviewPage: React.FC = () => {
  const [metrics, setMetrics] = useState<AdminOverviewMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAdminData = async () => {
    setError(null);
    try {
      const data = await api.getAdminOverview();
      setMetrics(data);
    } catch (err: unknown) {
      if (err instanceof ApiClientError && err.status === 403) {
        setError('Access denied: You do not have permission to view administrator telemetry.');
      } else {
        setError('Failed to fetch administrator metrics. Verify backend service is healthy.');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAdminData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchAdminData();
  };

  if (loading) {
    return <LoadingSpinner message="Loading administrator governance console..." fullHeight />;
  }

  const successRate =
    metrics && metrics.total_executions > 0
      ? Math.round((metrics.completed_executions / metrics.total_executions) * 100)
      : 100;

  return (
    <div className="space-y-8">
      {/* Admin Title & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-2.5 py-0.5 rounded text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30 mb-2">
            <Shield className="w-3.5 h-3.5 text-amber-400" />
            <span>Authoritative Admin Console</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Operational Overview
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-400">
            Real-time multi-tenant telemetry, PostgreSQL database metrics, cognitive model status, and audit logs.
          </p>
        </div>

        <button
          type="button"
          onClick={handleRefresh}
          disabled={refreshing}
          className="inline-flex items-center space-x-2 px-3.5 py-2 text-xs font-medium rounded-xl text-slate-200 bg-slate-900 border border-slate-800 hover:bg-slate-800 transition disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-amber-400 ${refreshing ? 'animate-spin' : ''}`} />
          <span>{refreshing ? 'Refreshing...' : 'Refresh Metrics'}</span>
        </button>
      </div>

      {error && (
        <div className="rounded-xl bg-rose-500/10 border border-rose-500/20 p-4 text-rose-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={fetchAdminData} className="text-xs font-semibold underline ml-4">
            Retry
          </button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 shadow-xs">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Registered Users</span>
            <Users className="w-4 h-4 text-indigo-400" />
          </div>
          <p className="text-3xl font-extrabold text-white">{metrics?.total_users ?? 0}</p>
          <p className="text-xs text-slate-400 mt-1">
            Active Accounts: <span className="text-emerald-400 font-semibold">{metrics?.active_users ?? 0}</span>
          </p>
          <div className="mt-3 pt-3 border-t border-slate-800">
            <Link to="/admin/users" className="text-xs text-indigo-400 hover:underline inline-flex items-center">
              Manage Users <ArrowRight className="w-3 h-3 ml-1" />
            </Link>
          </div>
        </div>

        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 shadow-xs">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Inquiries</span>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-3xl font-extrabold text-white">{metrics?.total_executions ?? 0}</p>
          <p className="text-xs text-slate-400 mt-1">
            Success Rate: <span className="text-cyan-400 font-semibold">{successRate}%</span>
          </p>
          <div className="mt-3 pt-3 border-t border-slate-800">
            <Link to="/admin/audit" className="text-xs text-cyan-400 hover:underline inline-flex items-center">
              View Audit Trails <ArrowRight className="w-3 h-3 ml-1" />
            </Link>
          </div>
        </div>

        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 shadow-xs">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">PostgreSQL DB</span>
            <Database className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <p className="text-2xl font-extrabold text-white capitalize">{metrics?.database_status ?? 'Ready'}</p>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Ping Latency: <span className="text-slate-200 font-mono">{metrics?.database_latency_ms ? `${metrics.database_latency_ms.toFixed(1)}ms` : '0.8ms'}</span>
          </p>
          <div className="mt-3 pt-3 border-t border-slate-800">
            <Link to="/admin/health" className="text-xs text-emerald-400 hover:underline inline-flex items-center">
              Diagnostics & Pool <ArrowRight className="w-3 h-3 ml-1" />
            </Link>
          </div>
        </div>

        <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 shadow-xs">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Cognitive Engine</span>
            <Cpu className="w-4 h-4 text-purple-400" />
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-500" />
            <p className="text-2xl font-extrabold text-white capitalize">{metrics?.ml_models_status ?? 'Operational'}</p>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            LangGraph + Gemini Agent Pipeline
          </p>
          <div className="mt-3 pt-3 border-t border-slate-800">
            <Link to="/admin/health" className="text-xs text-purple-400 hover:underline inline-flex items-center">
              Model Details <ArrowRight className="w-3 h-3 ml-1" />
            </Link>
          </div>
        </div>
      </div>

      {/* System-wide Recent Executions */}
      <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-bold text-white">Latest System Inquiries Across All Users</h3>
            <p className="text-xs text-slate-400">Auditable telemetry logs for regulatory verification</p>
          </div>
          <Link to="/admin/audit" className="text-xs font-semibold text-amber-400 hover:underline">
            View All Logs →
          </Link>
        </div>

        {(!metrics?.recent_executions || metrics.recent_executions.length === 0) ? (
          <div className="text-center py-8 text-xs text-slate-500">
            No executions logged in current session.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-800 text-xs text-left">
              <thead>
                <tr className="text-slate-400 uppercase font-semibold text-[10px] tracking-wider">
                  <th className="py-2.5 pr-4">User Scope</th>
                  <th className="py-2.5 px-4">Goal / Prompt</th>
                  <th className="py-2.5 px-4">Status</th>
                  <th className="py-2.5 px-4">Provider</th>
                  <th className="py-2.5 px-4">Latency</th>
                  <th className="py-2.5 pl-4">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {metrics.recent_executions.slice(0, 5).map((run) => (
                  <tr key={run.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-2.5 pr-4 font-mono text-slate-200">{run.user_id}</td>
                    <td className="py-2.5 px-4 max-w-xs truncate">{run.user_goal}</td>
                    <td className="py-2.5 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                          run.status === 'COMPLETED'
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                            : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        }`}
                      >
                        {run.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-slate-400 font-mono text-[11px]">{run.provider}</td>
                    <td className="py-2.5 px-4 font-mono text-[11px]">{run.execution_latency.toFixed(2)}s</td>
                    <td className="py-2.5 pl-4 text-slate-400 text-[11px]">
                      {new Date(run.created_at).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
