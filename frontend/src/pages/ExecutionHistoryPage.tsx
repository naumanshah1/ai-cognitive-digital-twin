import React, { useState, useEffect, useMemo } from 'react';
import {
  History,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Eye,
  X,
  Terminal,
  Search,
  Filter,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useDemo } from '../context/DemoContext';
import { apiClient } from '../services/api';
import type { HistoryItem, HistoryDetailResponse } from '../types/api';
import { StatusBadge } from '../components/common/StatusBadge';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { EmptyState } from '../components/common/EmptyState';

export const ExecutionHistoryPage: React.FC = () => {
  const { user } = useAuth();
  const { isDemoMode, activePersona } = useDemo();

  const [items, setItems] = useState<HistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Detail Modal State
  const [selectedRequestId, setSelectedRequestId] = useState<string | null>(null);
  const [detail, setDetail] = useState<HistoryDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const offset = (page - 1) * limit;
      const res = await apiClient.getHistory(limit, offset);
      if (res.items && res.items.length > 0) {
        setItems(res.items);
        setTotal(res.total);
      } else if (isDemoMode && activePersona.sampleAgentHistory) {
        // Fallback to active persona's deterministic fixtures in demo mode
        const demoItems: HistoryItem[] = activePersona.sampleAgentHistory.map((h) => ({
          id: h.id,
          request_id: h.requestId,
          user_id: user?.display_name || user?.email || activePersona.name,
          user_goal: h.userGoal,
          status: h.status,
          provider: h.provider,
          model: 'gemini-1.5-pro',
          execution_mode: 'deterministic',
          execution_latency: h.executionLatency,
          findings_count: h.findingsCount,
          recommendations_count: h.recommendationsCount,
          simulation_performed: false,
          verification_passed: true,
          created_at: h.createdAt,
        }));
        setItems(demoItems);
        setTotal(demoItems.length);
      } else {
        setItems([]);
        setTotal(0);
      }
    } catch {
      // In demo mode, fallback cleanly to persona fixtures instead of breaking
      if (isDemoMode && activePersona.sampleAgentHistory) {
        const demoItems: HistoryItem[] = activePersona.sampleAgentHistory.map((h) => ({
          id: h.id,
          request_id: h.requestId,
          user_id: user?.display_name || user?.email || activePersona.name,
          user_goal: h.userGoal,
          status: h.status,
          provider: h.provider,
          model: 'gemini-1.5-pro',
          execution_mode: 'deterministic',
          execution_latency: h.executionLatency,
          findings_count: h.findingsCount,
          recommendations_count: h.recommendationsCount,
          simulation_performed: false,
          verification_passed: true,
          created_at: h.createdAt,
        }));
        setItems(demoItems);
        setTotal(demoItems.length);
      } else {
        setError('Audit records are temporarily unavailable. Please retry shortly.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [page, limit, statusFilter, user, isDemoMode, activePersona]);

  const handleInspect = async (requestId: string) => {
    setSelectedRequestId(requestId);
    setDetailLoading(true);
    setDetailError(null);

    // Check if it's a demo persona item
    const demoItem = activePersona.sampleAgentHistory?.find((h) => h.requestId === requestId);
    if (demoItem) {
      setDetail({
        id: demoItem.id,
        request_id: demoItem.requestId,
        user_id: user?.display_name || user?.email || activePersona.name,
        user_goal: demoItem.userGoal,
        status: demoItem.status,
        provider: demoItem.provider,
        model: 'gemini-1.5-pro',
        execution_mode: 'deterministic',
        execution_latency: demoItem.executionLatency,
        findings_count: demoItem.findingsCount,
        recommendations_count: demoItem.recommendationsCount,
        simulation_performed: false,
        verification_passed: true,
        findings_summary: demoItem.summary,
        tools_called: demoItem.toolsCalled.map((t) => ({
          tool_name: t.toolName,
          status: t.status,
          duration_ms: t.durationMs,
        })),
        created_at: demoItem.createdAt,
      });
      setDetailLoading(false);
      return;
    }

    try {
      const res = await apiClient.getHistoryDetail(requestId);
      setDetail(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load execution detail';
      setDetailError(msg);
    } finally {
      setDetailLoading(false);
    }
  };

  const closeDetail = () => {
    setSelectedRequestId(null);
    setDetail(null);
    setDetailError(null);
  };

  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      const matchStatus = !statusFilter || item.status.toLowerCase() === statusFilter.toLowerCase();
      const matchSearch =
        !searchQuery ||
        item.user_goal.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.request_id.toLowerCase().includes(searchQuery.toLowerCase());
      return matchStatus && matchSearch;
    });
  }, [items, statusFilter, searchQuery]);

  const totalPages = Math.ceil((filteredItems.length || total) / limit) || 1;

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-2">
            <History className="w-3.5 h-3.5" />
            <span>Searchable Analysis Records</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            Execution Audit History
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-3xl">
            Immutable PostgreSQL audit trail of reasoning queries, tool invocations, and analytical syntheses
            executed for <strong className="text-slate-800 dark:text-slate-200">{user?.display_name || user?.email || 'your account'}</strong>.
          </p>
        </div>

        <button
          type="button"
          onClick={fetchHistory}
          className="inline-flex items-center space-x-2 px-3.5 py-2 text-xs font-medium rounded-xl text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 transition shadow-xs self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5 text-indigo-500" />
          <span>Refresh Records</span>
        </button>
      </div>

      {error && <ErrorAlert title="Audit Record Notice" message={error} onRetry={fetchHistory} />}

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
        <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
          {/* Search Box */}
          <div className="relative flex-1 sm:w-64">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search goal or request ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Status Filter */}
          <div className="flex items-center space-x-2">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="text-xs font-medium px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200"
            >
              <option value="">All Statuses</option>
              <option value="completed">COMPLETED</option>
              <option value="failed">FAILED</option>
              <option value="rejected">REJECTED</option>
            </select>
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs text-slate-500 dark:text-slate-400 self-end sm:self-auto">
          <span>Page Size:</span>
          <select
            value={limit}
            onChange={(e) => {
              setLimit(Number(e.target.value));
              setPage(1);
            }}
            className="text-xs font-medium px-2 py-1 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200"
          >
            <option value={5}>5</option>
            <option value={10}>10</option>
            <option value={20}>20</option>
          </select>
          <span>Showing {filteredItems.length} records</span>
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs overflow-hidden">
        {loading ? (
          <LoadingSpinner message="Querying PostgreSQL history records..." fullHeight />
        ) : filteredItems.length === 0 ? (
          <EmptyState
            title="No Execution Records Found"
            description="No audit records match the current filters. Execute an analysis from Behavioural Insights or Agent Workspace to create entries."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400">
                <tr>
                  <th className="py-3 px-4 font-semibold">Request ID</th>
                  <th className="py-3 px-4 font-semibold">Owner</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold">Objective</th>
                  <th className="py-3 px-4 font-semibold">Findings</th>
                  <th className="py-3 px-4 font-semibold">Recs</th>
                  <th className="py-3 px-4 font-semibold">Latency</th>
                  <th className="py-3 px-4 font-semibold">Timestamp</th>
                  <th className="py-3 px-4 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {filteredItems.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-mono text-slate-700 dark:text-slate-300 truncate max-w-[120px]">
                      {item.request_id}
                    </td>
                    <td className="py-3 px-4 text-slate-700 dark:text-slate-200 font-medium">
                      {item.user_id}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={item.status} size="sm" />
                    </td>
                    <td className="py-3 px-4 text-slate-600 dark:text-slate-300 truncate max-w-[240px]" title={item.user_goal}>
                      {item.user_goal}
                    </td>
                    <td className="py-3 px-4 text-slate-500 font-mono">
                      {item.findings_count}
                    </td>
                    <td className="py-3 px-4 text-slate-500 font-mono">
                      {item.recommendations_count}
                    </td>
                    <td className="py-3 px-4 text-slate-500 font-mono">
                      {item.execution_latency !== null && item.execution_latency !== undefined
                        ? `${(item.execution_latency * 1000).toFixed(0)} ms`
                        : '—'}
                    </td>
                    <td className="py-3 px-4 text-slate-400">
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        type="button"
                        onClick={() => handleInspect(item.request_id)}
                        className="inline-flex items-center space-x-1 px-2.5 py-1 text-xs font-medium text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300 hover:bg-indigo-50 dark:hover:bg-indigo-950/40 rounded-lg transition"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Toolbar */}
        {!loading && filteredItems.length > 0 && (
          <div className="px-4 py-3 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500">
            <div>
              Showing Page <span className="font-semibold text-slate-700 dark:text-slate-300">{page}</span> of{' '}
              <span className="font-semibold text-slate-700 dark:text-slate-300">{totalPages}</span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 disabled:opacity-40 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300"
                aria-label="Previous Page"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 disabled:opacity-40 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300"
                aria-label="Next Page"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Inspect Detail Modal */}
      {selectedRequestId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] flex flex-col border border-slate-200 dark:border-slate-800 overflow-hidden">
            {/* Modal Header */}
            <div className="p-4 sm:p-6 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-indigo-500" />
                  Execution Audit Detail
                </h3>
                <span className="text-xs text-slate-400 font-mono">ID: {selectedRequestId}</span>
              </div>
              <button
                type="button"
                onClick={closeDetail}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                aria-label="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 text-xs">
              {detailLoading && <LoadingSpinner message="Fetching execution telemetry..." />}

              {detailError && <ErrorAlert title="Detail Fetch Error" message={detailError} />}

              {detail && !detailLoading && (
                <div className="space-y-4">
                  {/* Metadata strip */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-700/60">
                    <div>
                      <span className="text-slate-400 block text-[11px]">Owner</span>
                      <span className="font-semibold text-slate-700 dark:text-slate-200">
                        {detail.user_id}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[11px]">Provider / Model</span>
                      <span className="font-semibold text-slate-700 dark:text-slate-200 font-mono">
                        {detail.provider}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[11px]">Status</span>
                      <StatusBadge status={detail.status} size="sm" />
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[11px]">Latency</span>
                      <span className="font-mono text-slate-700 dark:text-slate-300">
                        {detail.execution_latency ? `${(detail.execution_latency * 1000).toFixed(0)} ms` : '—'}
                      </span>
                    </div>
                  </div>

                  {/* Objective */}
                  <div>
                    <h5 className="font-semibold text-slate-900 dark:text-white mb-1">
                      Submitted Objective:
                    </h5>
                    <div className="p-3 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 leading-relaxed font-sans">
                      {detail.user_goal}
                    </div>
                  </div>

                  {/* Findings Summary */}
                  {detail.findings_summary && (
                    <div>
                      <h5 className="font-semibold text-slate-900 dark:text-white mb-1">
                        Findings Summary:
                      </h5>
                      <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-800 dark:text-slate-200 whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto">
                        {detail.findings_summary}
                      </div>
                    </div>
                  )}

                  {/* Tools Executed Detail */}
                  <div>
                    <h5 className="font-semibold text-slate-900 dark:text-white mb-1">
                      Tools Called ({detail.tools_called?.length || 0}):
                    </h5>
                    {(!detail.tools_called || detail.tools_called.length === 0) ? (
                      <p className="text-slate-400 italic">No external tools invoked during this agent turn.</p>
                    ) : (
                      <div className="space-y-2">
                        {detail.tools_called.map((t: { tool_name: string; status: string; duration_ms?: number }, idx: number) => (
                          <div
                            key={idx}
                            className="p-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 font-mono text-[11px] flex items-center justify-between"
                          >
                            <span className="font-bold text-indigo-600 dark:text-indigo-400">
                              {t.tool_name}
                            </span>
                            <div className="flex items-center space-x-3 text-slate-400">
                              {t.duration_ms !== undefined && <span>{t.duration_ms.toFixed(0)} ms</span>}
                              <span className="text-emerald-400 font-semibold">{t.status}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 flex justify-end">
              <button
                type="button"
                onClick={closeDetail}
                className="px-4 py-2 text-xs font-medium rounded-xl text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700 transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
