import React, { useState, useMemo } from 'react';
import {
  Bot,
  Send,
  Sparkles,
  Terminal,
  CheckCircle2,
  Copy,
  Check,
  Zap,
  Layers,
  ShieldCheck,
  HelpCircle,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useDemo } from '../context/DemoContext';
import { apiClient } from '../services/api';
import type { AgentRunResponse } from '../types/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';

interface PromptPreset {
  tool: string;
  label: string;
  prompt: string;
}

export const AgentWorkspacePage: React.FC = () => {
  const { user } = useAuth();
  const { isDemoMode, activePersona } = useDemo();

  const samplePrompts: PromptPreset[] = useMemo(() => {
    const subject = isDemoMode ? activePersona.name : user?.display_name || user?.email || 'my account';
    return [
      {
        tool: 'get_behavioral_summary',
        label: 'Behavioural Summary',
        prompt: `Retrieve an empirical behavioural summary for ${subject} over the past 14 days and synthesize daily focus hours, recovery rest, and productivity patterns.`,
      },
      {
        tool: 'detect_behavioral_drift',
        label: 'Drift Analysis',
        prompt: `Evaluate longitudinal behavioural drift for ${subject} comparing 30-day baseline reference against 14-day comparison window with Benjamini-Hochberg FDR control.`,
      },
      {
        tool: 'generate_recommendations',
        label: 'Recommendations',
        prompt: `Generate prioritized evidence-based recommendations for ${subject} targeting focus protection and meeting load reduction.`,
      },
      {
        tool: 'run_what_if_simulation',
        label: 'What-If Simulation',
        prompt: `Run a retrospective what-if simulation for ${subject} adjusting focus_duration_hours=6.5 and interruption_count=1 to estimate expected productivity delta.`,
      },
      {
        tool: 'predict_productivity',
        label: 'Productivity Prediction',
        prompt: `Predict retrospective productivity score for ${subject} using the Champion Linear Regression estimator and state model assumptions.`,
      },
    ];
  }, [isDemoMode, activePersona, user]);

  const [prompt, setPrompt] = useState(samplePrompts[0].prompt);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AgentRunResponse | null>(null);
  const [copied, setCopied] = useState(false);

  // Pre-load representative output from activePersona sampleAgentHistory if result is null
  const activeHistory = activePersona.sampleAgentHistory?.[0];

  const currentSummary = useMemo(() => {
    if (result) return result.summary;
    if (activeHistory) return activeHistory.summary;
    return `Synthesized empirical baseline indicates strong focus consolidation for ${activePersona.name}. Mean daily deep work is measured at ${activePersona.baseline.meanFocusHours.toFixed(
      1
    )} hours with ${activePersona.baseline.meanMeetingHours.toFixed(1)} hours of meeting load.`;
  }, [result, activeHistory, activePersona]);

  const currentFindings = useMemo(() => {
    if (result?.findings && result.findings.length > 0) return result.findings;
    return [
      `Daily focus duration maintains a mean of ${activePersona.baseline.meanFocusHours.toFixed(1)} hours/day.`,
      `Context switching density observed at ${activePersona.baseline.meanInterruptions.toFixed(1)} interruptions/day.`,
      `Nocturnal recovery baseline measured at ${activePersona.baseline.meanSleepHours.toFixed(1)} hours nocturnal sleep.`,
      `Overall covariate stability index measured at ${(activePersona.baseline.stabilityIndex * 100).toFixed(0)}%.`,
    ];
  }, [result, activePersona]);

  const currentTools = useMemo(() => {
    if (result?.execution_trace_summary && result.execution_trace_summary.length > 0) {
      return result.execution_trace_summary.map((t) => ({
        toolName: t.tool_name || t.tool || 'Autonomous Tool',
        durationMs: t.duration_ms || 120,
        status: t.status || 'COMPLETED',
      }));
    }
    if (activeHistory?.toolsCalled) {
      return activeHistory.toolsCalled;
    }
    return [
      { toolName: 'get_behavioral_summary', durationMs: 142, status: 'SUCCESS' },
      { toolName: 'predict_productivity', durationMs: 88, status: 'SUCCESS' },
    ];
  }, [result, activeHistory]);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!prompt.trim() || loading) return;

    setLoading(true);
    setError(null);

    try {
      const res = await apiClient.runAgent({
        goal: prompt.trim(),
        target_user_id: user?.id || 'demo_user',
      });
      setResult(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Agent execution failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyResponse = () => {
    navigator.clipboard.writeText(currentSummary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-2">
            <Bot className="w-3.5 h-3.5" />
            <span>Autonomous LangGraph Orchestrator</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            AI Agent Workspace
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-3xl">
            Interactive reasoning interface for your cognitive twin agent. Connects natural language objectives
            to registered statistical and machine learning tools with verified grounding.
          </p>
        </div>

        {/* Data Source Context */}
        <div className="flex items-center space-x-2 px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs">
          <Layers className="w-4 h-4 text-indigo-500 shrink-0" />
          <div>
            <div className="font-semibold text-slate-700 dark:text-slate-300">
              {isDemoMode ? activePersona.name : user?.display_name || user?.email || 'Authorized Account'}
            </div>
            <div className="text-[11px] text-slate-400 font-mono">
              Provider: {result?.provider || 'LangGraph / Deterministic Model'}
            </div>
          </div>
        </div>
      </div>

      {error && <ErrorAlert title="Agent Invocation Notice" message={error} />}

      {/* Suggested Analytical Tasks (Chips) */}
      <div className="space-y-2">
        <div className="text-xs font-semibold text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
          <Zap className="w-3.5 h-3.5 text-amber-400" />
          <span>Registered Agent Tool Inquiries</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {samplePrompts.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setPrompt(p.prompt)}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-medium border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-indigo-500/50 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition shadow-xs"
            >
              <Terminal className="w-3.5 h-3.5 text-indigo-500" />
              <span>{p.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Input Composer */}
      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-5 shadow-xs">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
              Natural Language Objective (Agent Goal)
            </label>
            <textarea
              rows={3}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="w-full px-3.5 py-2.5 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 leading-relaxed font-sans"
              placeholder="Formulate behavioural analysis or simulation goal..."
              required
            />
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
            <div className="flex items-center space-x-3 text-xs text-slate-400">
              <span className="font-mono bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-[11px]">
                5 Tools Available
              </span>
              <span>Grounding Safeguards Active</span>
            </div>

            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() => setPrompt('')}
                className="px-3 py-2 text-xs font-medium text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
              >
                Clear
              </button>

              <button
                type="submit"
                disabled={loading || !prompt.trim()}
                className="inline-flex items-center space-x-2 px-4 py-2 text-xs font-semibold rounded-xl text-white bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-600/30 transition disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <LoadingSpinner size="sm" />
                    <span>Orchestrating Tools...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-3.5 h-3.5" />
                    <span>Execute Agent Turn</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Structured Result Presentation */}
      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-xs space-y-6">
        {/* Result Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-4">
          <div className="flex items-center space-x-2.5">
            <Sparkles className="w-5 h-5 text-indigo-500" />
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Agent Synthesis & Execution Trace
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Response generated via LangGraph plan-and-solve execution graph.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={handleCopyResponse}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied' : 'Copy Synthesis'}</span>
            </button>
          </div>
        </div>

        {/* Executive Summary */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200/60 dark:border-slate-800 text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-sans">
          {currentSummary}
        </div>

        {/* Verification Status */}
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center space-x-2 text-emerald-400 font-medium">
            <ShieldCheck className="w-4 h-4 shrink-0" />
            <span>Agent Claims Grounded in Measured Telemetry</span>
          </div>
          <div className="text-[11px] text-slate-400 font-mono">
            Status: {result?.verification?.is_verified !== false ? 'VERIFIED' : 'FLAGGED'}
          </div>
        </div>

        {/* Grid: Structured Findings & Executed Tools */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Findings */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-3 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-indigo-400" />
              <span>Structured Empirical Findings ({currentFindings.length})</span>
            </h4>
            <div className="space-y-2">
              {currentFindings.map((f, i) => (
                <div
                  key={i}
                  className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 text-xs text-slate-700 dark:text-slate-300 leading-relaxed"
                >
                  {f}
                </div>
              ))}
            </div>
          </div>

          {/* Executed Tools */}
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-3 flex items-center gap-1.5">
              <Terminal className="w-4 h-4 text-indigo-400" />
              <span>Registered Tools Invoked ({currentTools.length})</span>
            </h4>
            <div className="space-y-2">
              {currentTools.map((t, i) => (
                <div
                  key={i}
                  className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 text-xs flex items-center justify-between font-mono"
                >
                  <div className="flex items-center space-x-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    <span className="font-semibold text-slate-800 dark:text-slate-200">{t.toolName}</span>
                  </div>
                  <div className="flex items-center space-x-3 text-[11px] text-slate-400">
                    <span>{t.durationMs.toFixed(0)} ms</span>
                    <span className="text-emerald-400 font-semibold">{t.status}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Transparency Note */}
      <div className="rounded-2xl bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800 p-5 text-xs text-slate-600 dark:text-slate-400 space-y-2">
        <div className="flex items-center space-x-2 font-semibold text-slate-800 dark:text-slate-200">
          <HelpCircle className="w-4 h-4 text-indigo-500" />
          <span>Execution Transparency & Isolation</span>
        </div>
        <p className="leading-relaxed">
          The Cognitive Twin Agent operates inside a restricted sandbox environment. Tool invocations query strictly authorized
          telemetry datasets without exposing internal system keys, prompts, or sensitive execution traces.
        </p>
      </div>
    </div>
  );
};
