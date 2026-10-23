import React, { useState, useEffect } from 'react';
import {
  Search,
  RefreshCw,
  Bot,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { api, ApiClientError } from '../../services/api';
import type { AdminAuditItem } from '../../types/api';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';

export const AdminAuditPage: React.FC = () => {
  const [logs, setLogs] = useState<AdminAuditItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchAuditLogs = async () => {
    setError(null);
    try {
      const data = await api.getAdminAudit(50, 0);
      setLogs(data.items || []);
      setTotal(data.total || 0);
    } catch (err: unknown) {
      if (err instanceof ApiClientError && err.status === 403) {
        setError('Forbidden: Administrator privileges required to access audit trails.');
      } else {
        setError('Failed to fetch system audit logs.');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchAuditLogs();
  };

  const filteredLogs = logs.filter((log) => {
    const matchesSearch =
      log.user_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.user_goal.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.request_id.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus =
      statusFilter === 'ALL' || log.status.toUpperCase() === statusFilter;

    return matchesSearch && matchesStatus;
  });

  if (loading) {
    return <LoadingSpinner message="Retrieving auditable system logs..." fullHeight />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            System Audit & Execution Trails
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-400">
            Immutable regulatory execution history recording prompts, tool durations, and verification states across all tenants.
          </p>
        </div>

        <button
          type="button"
          onClick={handleRefresh}
          disabled={refreshing}
          className="inline-flex items-center space-x-2 px-3.5 py-2 text-xs font-medium rounded-xl text-slate-200 bg-slate-900 border border-slate-800 hover:bg-slate-800 transition disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-amber-400 ${refreshing ? 'animate-spin' : ''}`} />
          <span>{refreshing ? 'Refreshing...' : 'Refresh Logs'}</span>
        </button>
      </div>

      {error && (
        <div className="rounded-xl bg-rose-500/10 border border-rose-500/20 p-4 text-rose-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={fetchAuditLogs} className="text-xs font-semibold underline ml-4">
            Retry
          </button>
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by User ID, goal, or Request ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50"
          />
        </div>

        <div className="flex items-center space-x-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none"
          >
            <option value="ALL">All Statuses</option>
            <option value="COMPLETED">Completed</option>
            <option value="FAILED">Failed</option>
            <option value="REJECTED">Rejected</option>
          </select>

          <span className="text-xs text-slate-400 font-medium">
            Showing {filteredLogs.length} of {total} runs
          </span>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xs overflow-hidden">
        <div className="divide-y divide-slate-800/80">
          {filteredLogs.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-500">
              No audit records match current filter criteria.
            </div>
          ) : (
            filteredLogs.map((item) => {
              const isExpanded = expandedId === item.id;
              return (
                <div key={item.id} className="p-4 hover:bg-slate-800/30 transition-colors">
                  <div
                    className="flex flex-col md:flex-row md:items-center justify-between gap-3 cursor-pointer"
                    onClick={() => setExpandedId(isExpanded ? null : item.id)}
                  >
                    <div className="flex items-start space-x-3">
                      <div className="w-7 h-7 rounded-lg bg-slate-800 text-slate-300 flex items-center justify-center shrink-0 mt-0.5">
                        <Bot className="w-4 h-4 text-amber-400" />
                      </div>
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-mono text-xs font-semibold text-slate-200">
                            User: {item.user_id}
                          </span>
                          <span className="text-slate-600">•</span>
                          <span className="font-mono text-[10px] text-slate-500">
                            {item.request_id}
                          </span>
                        </div>
                        <p className="text-xs text-slate-300 mt-1 line-clamp-1 font-medium">
                          {item.user_goal}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-3 shrink-0 self-end md:self-center">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                          item.status === 'COMPLETED'
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                            : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        }`}
                      >
                        {item.status}
                      </span>
                      <span className="text-[11px] font-mono text-slate-400">
                        {item.execution_latency.toFixed(2)}s
                      </span>
                      <span className="text-[11px] text-slate-400">
                        {new Date(item.created_at).toLocaleString()}
                      </span>
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-slate-400" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-slate-400" />
                      )}
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="mt-4 pt-4 border-t border-slate-800/80 pl-10 space-y-3 text-xs">
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-slate-950 p-3 rounded-xl border border-slate-800">
                        <div>
                          <span className="text-slate-500 block text-[10px] uppercase">Provider & Model</span>
                          <span className="text-slate-200 font-mono">{item.provider} ({item.model})</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block text-[10px] uppercase">Simulation Run</span>
                          <span className="text-slate-200">{item.simulation_performed ? 'Yes' : 'No'}</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block text-[10px] uppercase">Findings Extracted</span>
                          <span className="text-slate-200">{item.findings_count}</span>
                        </div>
                        <div>
                          <span className="text-slate-500 block text-[10px] uppercase">Recommendations</span>
                          <span className="text-slate-200">{item.recommendations_count}</span>
                        </div>
                      </div>

                      {item.findings_summary && (
                        <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                          <span className="text-slate-400 font-semibold block mb-1">Execution Summary:</span>
                          <p className="text-slate-300">{item.findings_summary}</p>
                        </div>
                      )}

                      {item.error_message && (
                        <div className="bg-rose-950/30 border border-rose-900/40 p-3 rounded-xl text-rose-300">
                          <span className="font-semibold block mb-1">Error Information:</span>
                          <p className="font-mono text-[11px]">{item.error_message}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
