import React, { useState, useEffect } from 'react';
import {
  Server,
  RefreshCw,
  Database,
  Cpu,
  Activity,
  Shield,
  Clock,
  Radio,
} from 'lucide-react';
import { apiClient } from '../services/api';
import { useAuth } from '../context/AuthContext';
import type { HealthResponse, ReadinessResponse } from '../types/api';
import { StatusBadge } from '../components/common/StatusBadge';
import { ErrorAlert } from '../components/common/ErrorAlert';

export const SystemStatusPage: React.FC = () => {
  const { user, token } = useAuth();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pingMs, setPingMs] = useState<number | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const runDiagnostics = async () => {
    setLoading(true);
    setError(null);
    const start = performance.now();
    try {
      // 1. Check Liveness
      const healthRes = await apiClient.getHealth();
      setHealth(healthRes);
      const elapsed = performance.now() - start;
      setPingMs(elapsed);

      // 2. Check Readiness
      try {
        const readyRes = await apiClient.getReadiness();
        setReadiness(readyRes);
      } catch (rErr: unknown) {
        console.warn('Readiness endpoint unavailable:', rErr);
        setReadiness(null);
      }
      setLastChecked(new Date());
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Backend diagnostics failed';
      setError(msg);
      setHealth(null);
      setReadiness(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runDiagnostics();
  }, []);

  const db = readiness?.components?.database;
  const models = readiness?.components?.models;

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Server className="w-6 h-6 text-indigo-600 dark:text-indigo-400" aria-hidden="true" />
            Infrastructure & System Status
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Real-time status probes for FastAPI server, live PostgreSQL connection pool, and ML model runtime.
          </p>
        </div>

        <button
          type="button"
          onClick={runDiagnostics}
          disabled={loading}
          className="inline-flex items-center space-x-2 px-3.5 py-2 text-xs font-medium rounded-lg text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 transition shadow-xs disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-indigo-500 ${loading ? 'animate-spin' : ''}`} />
          <span>Run Probe Diagnostics</span>
        </button>
      </div>

      {error && (
        <ErrorAlert
          title="Backend Unreachable"
          message={error}
          onRetry={runDiagnostics}
        />
      )}

      {/* Primary Status Banner */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800 gap-3">
          <div className="flex items-center space-x-3">
            <div
              className={`w-3.5 h-3.5 rounded-full ${
                health?.status === 'ok' && readiness?.status === 'ready'
                  ? 'bg-emerald-500 shadow-lg shadow-emerald-500/30'
                  : health?.status === 'ok'
                  ? 'bg-amber-500 shadow-lg shadow-amber-500/30'
                  : 'bg-rose-500 shadow-lg shadow-rose-500/30'
              }`}
            />
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                {health?.status === 'ok' && readiness?.status === 'ready'
                  ? 'All Subsystems Operational'
                  : health?.status === 'ok'
                  ? 'Service Responsive (Subsystems Degraded/Partial)'
                  : 'Backend Service Offline'}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Probed endpoint: <code className="font-mono text-indigo-600 dark:text-indigo-400">{apiClient.getBaseUrl()}</code>
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-4 text-xs text-slate-400 font-mono">
            {pingMs !== null && (
              <span className="flex items-center gap-1">
                <Radio className="w-3.5 h-3.5 text-indigo-500" />
                Ping: {pingMs.toFixed(0)} ms
              </span>
            )}
            {lastChecked && (
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                {lastChecked.toLocaleTimeString()}
              </span>
            )}
          </div>
        </div>

        {/* Diagnostic Probes Table */}
        <div className="mt-5 space-y-4">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Probe Telemetry Breakdown
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* FastAPI Service Liveness */}
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                  <Activity className="w-4 h-4 text-indigo-500" />
                  FastAPI Server
                </span>
                <StatusBadge
                  status={health?.status === 'ok' ? 'completed' : 'failed'}
                  label={health?.status === 'ok' ? 'Liveness: OK' : 'Unavailable'}
                  size="sm"
                />
              </div>
              <div className="text-xs text-slate-500 space-y-1 mt-2">
                <div>Endpoint: <code className="font-mono">GET /health</code></div>
                <div>Version: <span className="font-mono">{health?.version || 'Unknown'}</span></div>
                <div>Environment: <span className="font-mono">{health?.environment || 'N/A'}</span></div>
              </div>
            </div>

            {/* PostgreSQL Readiness */}
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                  <Database className="w-4 h-4 text-indigo-500" />
                  PostgreSQL Pool
                </span>
                <StatusBadge
                  status={
                    db?.status === 'ready'
                      ? 'completed'
                      : db?.status
                      ? 'failed'
                      : 'neutral'
                  }
                  label={db?.status ? `DB: ${db.status}` : 'Status: Unknown'}
                  size="sm"
                />
              </div>
              <div className="text-xs text-slate-500 space-y-1 mt-2">
                <div>Endpoint: <code className="font-mono">GET /health/ready</code></div>
                <div>Latency: <span className="font-mono">{db?.latency_ms ? `${db.latency_ms.toFixed(1)} ms` : 'N/A'}</span></div>
                <div>Message: <span className="font-mono">{db?.message || 'Status verified'}</span></div>
              </div>
            </div>

            {/* Cognitive Models Readiness */}
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                  <Cpu className="w-4 h-4 text-indigo-500" />
                  ML Models / LLM
                </span>
                <StatusBadge
                  status={
                    models?.status === 'ready'
                      ? 'completed'
                      : models?.status === 'degraded'
                      ? 'warning'
                      : 'neutral'
                  }
                  label={models?.status ? `Models: ${models.status}` : 'Status: Unknown'}
                  size="sm"
                />
              </div>
              <div className="text-xs text-slate-500 space-y-1 mt-2">
                <div>Orchestrator: <span className="font-mono">LangGraph StateGraph</span></div>
                <div>Latency: <span className="font-mono">{models?.latency_ms ? `${models.latency_ms.toFixed(1)} ms` : 'N/A'}</span></div>
                <div>Message: <span className="font-mono">{models?.message || 'Models ready'}</span></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Security & Client Context */}
      <div className="bg-white dark:bg-slate-900 p-5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
        <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
          <Shield className="w-4 h-4 text-indigo-500" />
          Client Authentication & Authorization Context
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
            <span className="text-slate-400 block text-[11px]">Authenticated Identity</span>
            <span className="font-mono font-semibold text-slate-800 dark:text-slate-200 mt-1 block">
              {user ? user.id : 'Unauthenticated'}
            </span>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
            <span className="text-slate-400 block text-[11px]">Roles</span>
            <span className="font-mono font-semibold text-slate-800 dark:text-slate-200 mt-1 block">
              {user?.roles ? user.roles.join(', ') : 'NONE'}
            </span>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
            <span className="text-slate-400 block text-[11px]">Bearer Token Spec</span>
            <span className="font-mono text-slate-600 dark:text-slate-400 mt-1 block truncate">
              {token ? `${token.substring(0, 14)}...` : 'No Token'}
            </span>
          </div>

          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
            <span className="text-slate-400 block text-[11px]">Security Authority</span>
            <span className="text-slate-600 dark:text-slate-300 mt-1 block font-medium">
              Authoritative Backend
            </span>
          </div>
        </div>

        <div className="mt-4 p-3 rounded-lg bg-slate-50 dark:bg-slate-800/30 border border-slate-100 dark:border-slate-800 text-[11px] text-slate-400 leading-relaxed">
          <strong>Security Boundary Guarantee:</strong> The frontend never bypasses authorization. Privileged database credentials, service role tokens, and Gemini API keys are maintained exclusively on the backend server and are never present in Vite browser client builds or client-side environment files.
        </div>
      </div>
    </div>
  );
};
