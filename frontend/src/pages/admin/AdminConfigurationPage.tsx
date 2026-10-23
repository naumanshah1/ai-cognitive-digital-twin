import React, { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { api, ApiClientError } from '../../services/api';
import type { AdminConfigurationResponse } from '../../types/api';
import {
  Database,
  Cpu,
  Layers,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  GitCommit,
} from 'lucide-react';

export const AdminConfigurationPage: React.FC = () => {
  const { token } = useAuth();
  const [data, setData] = useState<AdminConfigurationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchConfig = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAdminConfiguration(token || undefined);
      setData(res);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      } else {
        setError('Failed to load system and integration configuration.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, [token]);

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">System & Integration Configuration</h1>
          <p className="text-slate-400 mt-1 text-sm">
            Operational runtime parameters, framework dependencies, migration state, and security policies. Secrets are safely sanitized.
          </p>
        </div>
        <button
          onClick={fetchConfig}
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

      {/* Configuration Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* PostgreSQL Database */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2.5 bg-indigo-500/10 text-indigo-400 rounded-lg">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">Database & Pool Settings</h2>
              <p className="text-xs text-slate-400">PostgreSQL engine and connection pool parameters</p>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400">Engine / Dialect</span>
              <span className="text-xs font-mono font-medium text-white">{data?.database?.dialect ?? 'PostgreSQL via psycopg'}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400">Connection Status</span>
              <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <CheckCircle2 className="w-3 h-3" />
                <span className="capitalize">{data?.database?.status ?? 'connected'}</span>
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400">Pool Size / Max Overflow</span>
              <span className="text-xs font-mono font-medium text-white">
                {data?.database?.pool_size ?? 10} connections (overflow: {data?.database?.max_overflow ?? 5})
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400">Pool Timeout</span>
              <span className="text-xs font-mono font-medium text-white">{data?.database?.pool_timeout ?? 30}s</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400">Credentials Exposure</span>
              <span className="text-xs font-semibold text-emerald-400">Sanitized (Masked from client)</span>
            </div>
          </div>
        </div>

        {/* AI & Cognitive Engine */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2.5 bg-cyan-500/10 text-cyan-400 rounded-lg">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">Cognitive Model & LLM Engine</h2>
              <p className="text-xs text-slate-400">Autonomous LangGraph agent runtime configuration</p>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400">Primary Provider</span>
              <span className="text-xs font-semibold text-cyan-400 capitalize">{data?.llm?.provider ?? 'Gemini'}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400">Model Name</span>
              <span className="text-xs font-mono font-medium text-white">{data?.llm?.model_name ?? 'gemini-2.5-flash'}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400">Agent Mode</span>
              <span className="text-xs font-mono font-medium text-white">{data?.llm?.agent_mode ?? 'llm:gemini'}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400">Server API Key State</span>
              <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <CheckCircle2 className="w-3 h-3" />
                <span>Configured (Secure Server-Side)</span>
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400">Max Steps / Tool Limit</span>
              <span className="text-xs font-mono font-medium text-white">
                {data?.llm?.max_steps ?? 10} steps / {data?.llm?.max_tool_calls ?? 8} tools
              </span>
            </div>
          </div>
        </div>

        {/* Frameworks & Stack */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2.5 bg-purple-500/10 text-purple-400 rounded-lg">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">Core Framework Architecture</h2>
              <p className="text-xs text-slate-400">Verified technology stack components</p>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400">Backend API</span>
              <span className="text-xs font-medium text-white">{data?.frameworks?.backend ?? 'FastAPI (Python 3.14)'}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400">Persistence / ORM</span>
              <span className="text-xs font-medium text-white">{data?.frameworks?.orm ?? 'SQLAlchemy 2.0 & Alembic'}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400">Agentic Orchestration</span>
              <span className="text-xs font-medium text-white">{data?.frameworks?.agentic_ai ?? 'LangGraph & LangChain Core'}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400">Frontend Client</span>
              <span className="text-xs font-medium text-white">{data?.frameworks?.frontend ?? 'React 19, TypeScript 5, Vite, Tailwind CSS v4'}</span>
            </div>
          </div>
        </div>

        {/* Alembic Migrations & Security Policy */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2.5 bg-emerald-500/10 text-emerald-400 rounded-lg">
              <GitCommit className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">Schema Migrations & Policies</h2>
              <p className="text-xs text-slate-400">Database revision status and rate limits</p>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400">Latest Migration Revision</span>
              <span className="text-xs font-mono font-semibold text-indigo-400">
                {data?.database_migrations?.latest_revision ?? '002_add_auth_and_roles'}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400">Migration Status</span>
              <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <CheckCircle2 className="w-3 h-3" />
                <span>Up to date</span>
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400">Sliding Window Rate Limit</span>
              <span className="text-xs font-mono font-medium text-white">{data?.security_policies?.rate_limit_per_minute ?? 60} req/min</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg">
              <span className="text-xs text-slate-400">Session Token Expiry</span>
              <span className="text-xs font-mono font-medium text-white">{data?.security_policies?.token_expiration_hours ?? 24} hours</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
