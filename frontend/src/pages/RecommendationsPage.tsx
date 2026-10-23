import React, { useState, useMemo } from 'react';
import {
  Sparkles,
  Send,
  Filter,
  Layers,
  ShieldCheck,
  Bookmark,
  BookmarkCheck,
  BarChart2,
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
} from 'recharts';
import { useAuth } from '../context/AuthContext';
import { useDemo } from '../context/DemoContext';
import { apiClient } from '../services/api';
import type { AgentRunResponse } from '../types/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';

export const RecommendationsPage: React.FC = () => {
  const { user } = useAuth();
  const { isDemoMode, activePersona } = useDemo();

  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [savedRecommendations, setSavedRecommendations] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agentResult, setAgentResult] = useState<AgentRunResponse | null>(null);

  const rawRecommendations = activePersona.recommendations;

  // Filter recommendations
  const filteredRecommendations = useMemo(() => {
    return rawRecommendations.filter((rec) => {
      const matchCat = categoryFilter === 'ALL' || rec.category === categoryFilter;
      const matchPri = priorityFilter === 'ALL' || rec.priorityLabel === priorityFilter;
      return matchCat && matchPri;
    });
  }, [rawRecommendations, categoryFilter, priorityFilter]);

  // Aggregate Category breakdown data for chart
  const categoryData = useMemo(() => {
    const counts: Record<string, number> = {
      FOCUS_ARCHITECTURE: 0,
      MEETING_HYGIENE: 0,
      RECOVERY_SLEEP: 0,
      DIGITAL_WELLBEING: 0,
    };
    rawRecommendations.forEach((r) => {
      if (counts[r.category] !== undefined) counts[r.category]++;
    });
    return [
      { name: 'Focus', count: counts.FOCUS_ARCHITECTURE, color: '#6366f1' },
      { name: 'Meetings', count: counts.MEETING_HYGIENE, color: '#06b6d4' },
      { name: 'Recovery', count: counts.RECOVERY_SLEEP, color: '#8b5cf6' },
      { name: 'Digital', count: counts.DIGITAL_WELLBEING, color: '#10b981' },
    ];
  }, [rawRecommendations]);

  // Priority count
  const highPriorityCount = useMemo(() => {
    return rawRecommendations.filter((r) => r.priorityLabel === 'HIGH').length;
  }, [rawRecommendations]);

  const handleToggleSave = (id: string) => {
    setSavedRecommendations((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const handleGenerateFresh = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const goal = `Generate updated prioritized evidence-based recommendations for ${
      user?.display_name || user?.email || activePersona.name
    } targeting focus stability, meeting load reduction, and cognitive recovery.`;

    try {
      const response = await apiClient.runAgent({
        goal,
        target_user_id: user?.id || 'demo_user',
      });
      setAgentResult(response);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Recommendation generation request failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const formatCategoryName = (cat: string) => {
    switch (cat) {
      case 'FOCUS_ARCHITECTURE':
        return 'Focus Architecture';
      case 'MEETING_HYGIENE':
        return 'Meeting Hygiene';
      case 'RECOVERY_SLEEP':
        return 'Recovery & Sleep';
      case 'DIGITAL_WELLBEING':
        return 'Digital Wellbeing';
      default:
        return cat;
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20 mb-2">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Targeted Behavioural Interventions</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            Recommendations Action Centre
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-3xl">
            Evidence-aligned behavioral adjustments synthesized from your empirical telemetry.
            Prioritized to protect deep-work focus, reduce context-switching fragmentation, and support sustainable recovery.
          </p>
        </div>

        {/* Data Source Context */}
        <div className="flex items-center space-x-2 px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs">
          <Layers className="w-4 h-4 text-purple-500 shrink-0" />
          <div>
            <div className="font-semibold text-slate-700 dark:text-slate-300">
              {isDemoMode ? activePersona.name : user?.display_name || user?.email || 'Authorized Account'}
            </div>
            <div className="text-[11px] text-slate-400 font-mono">
              {rawRecommendations.length} Calibrated Interventions
            </div>
          </div>
        </div>
      </div>

      {error && <ErrorAlert title="Recommendation Notice" message={error} />}

      {/* KPI Ribbon */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Total Interventions
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
            {rawRecommendations.length}
          </div>
          <div className="mt-1 text-[11px] text-purple-400">Grounded Actions</div>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            High Priority Actions
          </div>
          <div className="mt-2 text-2xl font-bold text-rose-500">
            {highPriorityCount}
          </div>
          <div className="mt-1 text-[11px] text-slate-400">Immediate Impact</div>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Saved to Plan
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-400">
            {Object.values(savedRecommendations).filter(Boolean).length}
          </div>
          <div className="mt-1 text-[11px] text-emerald-500">Active Commitments</div>
        </div>

        <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Grounding Status
          </div>
          <div className="mt-2 text-xl font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <span>Verified</span>
          </div>
          <div className="mt-1 text-[11px] text-slate-400">Calibrated Evidence</div>
        </div>
      </div>

      {/* Visual Domain Breakdown & Fast Synthesis Bar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Category Breakdown Bar Chart */}
        <div className="lg:col-span-2 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-xs flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2 mb-1">
              <BarChart2 className="w-5 h-5 text-purple-500" />
              Intervention Domain Breakdown
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
              Distribution of synthesized recommendations across key behavioral disciplines.
            </p>
          </div>

          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categoryData} layout="vertical" margin={{ top: 5, right: 30, left: 30, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.2} horizontal={false} />
                <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11, fill: '#64748b' }} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 11, fill: '#64748b' }} width={70} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    color: '#f8fafc',
                    fontSize: '12px',
                  }}
                  formatter={(val: unknown) => [`${val} Action(s)`, 'Count']}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-2 text-[11px] text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-800 flex justify-between">
            <span>Derived from empirical telemetry cluster analysis.</span>
            <span>Deterministic Model Output</span>
          </div>
        </div>

        {/* Quick Synthesis Form */}
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-xs flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2 mb-1">
              <Sparkles className="w-5 h-5 text-indigo-400" />
              Twin Reasoning Refresh
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
              Trigger autonomous LangGraph agent to synthesize new recommendations.
            </p>
          </div>

          <div className="space-y-4">
            <div className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-950 p-3.5 rounded-xl border border-slate-200 dark:border-slate-800">
              {agentResult
                ? agentResult.summary
                : `Current interventions are tailored to the ${activePersona.name} scenario, targeting baseline stabilization.`}
            </div>

            <button
              type="button"
              onClick={handleGenerateFresh}
              disabled={loading}
              className="w-full inline-flex items-center justify-center space-x-2 px-4 py-2.5 text-xs font-semibold rounded-xl text-white bg-purple-600 hover:bg-purple-500 shadow-md shadow-purple-600/30 transition disabled:opacity-50"
            >
              {loading ? (
                <>
                  <LoadingSpinner size="sm" />
                  <span>Synthesizing Interventions...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Synthesize Fresh Interventions</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5 mr-2">
            <Filter className="w-4 h-4 text-purple-500" />
            Filter Domain:
          </span>
          {[
            { id: 'ALL', label: 'All Domains' },
            { id: 'FOCUS_ARCHITECTURE', label: 'Focus Architecture' },
            { id: 'MEETING_HYGIENE', label: 'Meeting Hygiene' },
            { id: 'RECOVERY_SLEEP', label: 'Recovery & Sleep' },
            { id: 'DIGITAL_WELLBEING', label: 'Digital Wellbeing' },
          ].map((cat) => (
            <button
              key={cat.id}
              type="button"
              onClick={() => setCategoryFilter(cat.id)}
              className={`px-3 py-1.5 rounded-lg font-medium transition ${
                categoryFilter === cat.id
                  ? 'bg-purple-600 text-white shadow-xs'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-slate-500 dark:text-slate-400">Priority:</span>
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
          >
            <option value="ALL">All Priorities</option>
            <option value="HIGH">High Priority</option>
            <option value="MEDIUM">Medium Priority</option>
            <option value="NORMAL">Normal Priority</option>
          </select>
        </div>
      </div>

      {/* Recommendation Cards Grid */}
      {filteredRecommendations.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-400 text-sm">
          No recommendations match the selected filters.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredRecommendations.map((rec) => {
            const isSaved = !!savedRecommendations[rec.id];
            const isHigh = rec.priorityLabel === 'HIGH';

            return (
              <div
                key={rec.id}
                className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-xs flex flex-col justify-between hover:border-purple-500/40 transition"
              >
                <div>
                  {/* Card Header */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div className="flex items-center space-x-2">
                      <span
                        className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full ${
                          isHigh
                            ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            : 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
                        }`}
                      >
                        {rec.priorityLabel} PRIORITY
                      </span>
                      <span className="text-[11px] text-slate-400 font-medium">
                        {formatCategoryName(rec.category)}
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={() => handleToggleSave(rec.id)}
                      className={`p-1.5 rounded-lg transition ${
                        isSaved
                          ? 'text-purple-400 bg-purple-500/10'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                      }`}
                      title={isSaved ? 'Remove from Plan' : 'Save to Action Plan'}
                    >
                      {isSaved ? (
                        <BookmarkCheck className="w-4 h-4 text-purple-400" />
                      ) : (
                        <Bookmark className="w-4 h-4" />
                      )}
                    </button>
                  </div>

                  <h3 className="text-base font-bold text-slate-900 dark:text-white leading-snug">
                    {rec.title}
                  </h3>

                  {/* Proposed Action Box */}
                  <div className="mt-3 p-3.5 rounded-xl bg-purple-50/50 dark:bg-purple-950/20 border border-purple-200/60 dark:border-purple-900/40 text-xs text-slate-800 dark:text-purple-200 font-medium leading-relaxed">
                    <strong>Proposed Action:</strong> {rec.proposedAction}
                  </div>

                  {/* Telemetry Evidence & Rationale */}
                  <div className="mt-4 space-y-2 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                    <div>
                      <strong className="text-slate-700 dark:text-slate-300">Rationale:</strong>{' '}
                      {rec.rationale}
                    </div>
                    <div>
                      <strong className="text-slate-700 dark:text-slate-300">Telemetry Evidence:</strong>{' '}
                      {rec.evidence}
                    </div>
                  </div>
                </div>

                {/* Footer Impact Callout */}
                <div className="mt-5 pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs">
                  <div className="font-semibold text-emerald-500 dark:text-emerald-400">
                    Expected Impact: {rec.expectedImpact}
                  </div>
                  <div className="text-[11px] text-slate-400 font-mono">
                    Score: {(rec.priorityScore * 100).toFixed(0)}/100
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Responsible AI Transparency Note */}
      <div className="rounded-2xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 p-5 text-xs text-slate-600 dark:text-slate-400 space-y-2">
        <div className="flex items-center space-x-2 font-semibold text-slate-800 dark:text-slate-200">
          <HelpCircle className="w-4 h-4 text-purple-500" />
          <span>Evidence Grounding & Methodology</span>
        </div>
        <p className="leading-relaxed">
          Recommendations are synthesized by mapping personal telemetry covariates to peer-cohort benchmark clusters.
          Prioritization scores incorporate estimated productivity delta, covariate effect size, and implementation effort.
        </p>
        <p className="leading-relaxed">
          Interventions do not constitute medical, psychological, or organizational mandates. They are calibrated starting
          points for self-directed personal optimization.
        </p>
      </div>
    </div>
  );
};
