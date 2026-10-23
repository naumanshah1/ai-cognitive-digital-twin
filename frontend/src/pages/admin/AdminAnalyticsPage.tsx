import React, { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { api, ApiClientError } from '../../services/api';
import type { AdminAnalyticsResponse } from '../../types/api';
import {
  TrendingUp,
  Cpu,
  Clock,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Layers,
  BarChart3,
  Sliders,
  GitBranch,
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

export const AdminAnalyticsPage: React.FC = () => {
  const { token } = useAuth();
  const [data, setData] = useState<AdminAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAdminAnalytics(token || undefined);
      setData(res);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      } else {
        setError('Failed to load operational model analytics.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [token]);

  // Tool usage data formatted for chart
  const toolData = data?.tool_usage
    ? [
        { name: 'Drift Detect', count: data.tool_usage.detect_drift || 0, fill: '#06b6d4' },
        { name: 'Recommendations', count: data.tool_usage.generate_recommendations || 0, fill: '#6366f1' },
        { name: 'Simulation', count: data.tool_usage.simulate_what_if || 0, fill: '#a855f7' },
        { name: 'Baseline Profiling', count: data.tool_usage.profile_baseline || 0, fill: '#10b981' },
      ]
    : [];

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Model & Engine Analytics</h1>
          <p className="text-slate-400 mt-1 text-sm">
            Operational performance, latency distributions, and tool execution frequencies across the cognitive engine.
          </p>
        </div>
        <button
          onClick={fetchAnalytics}
          disabled={loading}
          className="flex items-center space-x-2 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-sm font-medium transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="flex items-center space-x-2 p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-sm">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Inquiries</span>
            <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-white">{data?.total_executions ?? '—'}</span>
            <div className="text-xs text-slate-500 mt-0.5">Across all tenant accounts</div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Execution Success Rate</span>
            <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-emerald-400">
              {data ? `${data.success_rate_percent}%` : '—'}
            </span>
            <div className="text-xs text-slate-500 mt-0.5">
              {data?.completed_executions ?? 0} successful / {data?.failed_executions ?? 0} failed
            </div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Avg Execution Latency</span>
            <div className="p-2 bg-cyan-500/10 text-cyan-400 rounded-lg">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-white">
              {data ? `${data.avg_latency_ms} ms` : '—'}
            </span>
            <div className="text-xs text-slate-500 mt-0.5">
              Median (p50): {data?.p50_latency_ms ?? 0} ms
            </div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">P95 Tail Latency</span>
            <div className="p-2 bg-amber-500/10 text-amber-400 rounded-lg">
              <Cpu className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-amber-400">
              {data ? `${data.p95_latency_ms} ms` : '—'}
            </span>
            <div className="text-xs text-slate-500 mt-0.5">95th percentile response time</div>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Execution Volume Timeline */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2.5 bg-indigo-500/10 text-indigo-400 rounded-lg">
              <BarChart3 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">Inquiry Volume Timeline</h2>
              <p className="text-xs text-slate-400">Inquiries processed over recent dates</p>
            </div>
          </div>

          <div className="h-64">
            {data?.execution_timeline && data.execution_timeline.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.execution_timeline} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 11 }} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                    labelStyle={{ color: '#e2e8f0', fontSize: '12px' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="executions"
                    stroke="#6366f1"
                    strokeWidth={2.5}
                    dot={{ fill: '#6366f1', r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">
                No execution history records available.
              </div>
            )}
          </div>
        </div>

        {/* Cognitive Tool Frequency */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2.5 bg-cyan-500/10 text-cyan-400 rounded-lg">
              <Sliders className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">Tool Invocation Breakdown</h2>
              <p className="text-xs text-slate-400">Frequency of autonomous tool calls by the LangGraph agent</p>
            </div>
          </div>

          <div className="h-64">
            {toolData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={toolData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 10 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 11 }} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                    labelStyle={{ color: '#e2e8f0', fontSize: '12px' }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]} fill="#6366f1" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">
                No tool invocation data recorded.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Model Provider & Baseline Reference */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-2.5 bg-purple-500/10 text-purple-400 rounded-lg">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">Provider Usage Distribution</h2>
              <p className="text-xs text-slate-400">Model inference providers handling queries</p>
            </div>
          </div>

          <div className="space-y-3 mt-4">
            {data?.provider_distribution &&
              Object.entries(data.provider_distribution).map(([provider, count]) => (
                <div key={provider} className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg">
                  <div className="flex items-center space-x-2.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
                    <span className="text-xs font-medium text-white capitalize">{provider}</span>
                  </div>
                  <span className="text-xs font-mono font-semibold text-slate-300">{count} calls</span>
                </div>
              ))}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
          <div className="flex items-center space-x-3 mb-4">
            <div className="p-2.5 bg-emerald-500/10 text-emerald-400 rounded-lg">
              <GitBranch className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">Research Benchmark Baselines</h2>
              <p className="text-xs text-slate-400">Calibrated benchmark scores from Milestone 4 & 7 experiments</p>
            </div>
          </div>

          <div className="space-y-3 mt-4">
            <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400">Calibrated Baseline Productivity Score</span>
              <span className="text-xs font-semibold text-white">{data?.benchmark_baseline_productivity ?? 72.4} / 100</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400">Benchmark Mean Focus Hours / Day</span>
              <span className="text-xs font-semibold text-white">{data?.benchmark_baseline_focus_hours ?? 5.2} hrs</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400">Temporal Drift Test Window</span>
              <span className="text-xs font-semibold text-white">14-day rolling baseline</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
