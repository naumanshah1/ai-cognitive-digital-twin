import React from 'react';
import { Link } from 'react-router-dom';
import {
  BrainCircuit,
  Activity,
  Sparkles,
  Sliders,
  Bot,
  History,
  ShieldCheck,
  ArrowRight,
  TrendingUp,
  CheckCircle2,
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 selection:bg-indigo-500 selection:text-white">
      {/* Sticky Top Navigation */}
      <nav className="sticky top-0 z-50 backdrop-blur-md bg-slate-950/80 border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform duration-200">
              <BrainCircuit className="w-5 h-5 text-white" aria-hidden="true" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                Cognitive Twin
              </span>
              <span className="block text-[10px] uppercase tracking-wider font-semibold text-indigo-400 -mt-1">
                Behavioural Intelligence
              </span>
            </div>
          </Link>

          <div className="hidden md:flex items-center space-x-8 text-sm font-medium text-slate-300">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#preview" className="hover:text-white transition-colors">Preview</a>
            <a href="#how-it-works" className="hover:text-white transition-colors">How It Works</a>
            <a href="#responsible-ai" className="hover:text-white transition-colors">Responsible AI</a>
          </div>

          <div className="flex items-center space-x-4">
            <Link
              to="/signin"
              className="text-sm font-medium text-slate-300 hover:text-white px-3 py-1.5 rounded-lg transition-colors"
            >
              Sign In
            </Link>
            <Link
              to="/signup"
              className="inline-flex items-center justify-center text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 px-4 py-2 rounded-xl transition-all shadow-md shadow-indigo-600/30 hover:shadow-indigo-600/50"
            >
              Get Started
              <ArrowRight className="w-4 h-4 ml-1.5" />
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-20 pb-24 overflow-hidden border-b border-slate-900">
        {/* Ambient glow effects */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-indigo-600/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-1/3 left-1/3 -translate-x-1/2 w-[400px] h-[250px] bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 mb-6">
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
            <span>Autonomous Behavioural Intelligence Prototype</span>
          </div>

          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white max-w-4xl mx-auto leading-tight">
            Understand your patterns.{' '}
            <span className="bg-gradient-to-r from-indigo-400 via-cyan-400 to-indigo-300 bg-clip-text text-transparent">
              Shape your next move.
            </span>
          </h1>

          <p className="mt-6 text-lg sm:text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Turn behavioural signals into actionable insights with personalized analytics,
            drift detection, evidence-backed recommendations, and transparent counterfactual simulations.
          </p>

          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/signup"
              className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3.5 rounded-xl text-base font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-lg shadow-indigo-600/30 transition-all hover:-translate-y-0.5"
            >
              Explore Cognitive Twin
              <ArrowRight className="w-5 h-5 ml-2" />
            </Link>
            <a
              href="#preview"
              className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3.5 rounded-xl text-base font-medium text-slate-300 bg-slate-900/80 hover:bg-slate-800 border border-slate-800 hover:text-white transition-colors"
            >
              See How It Works
            </a>
          </div>

          <div className="mt-12 flex items-center justify-center space-x-6 text-xs text-slate-500">
            <span className="flex items-center">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 mr-1.5" />
              Role-Based Access Control
            </span>
            <span className="flex items-center">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 mr-1.5" />
              LangGraph + Gemini Agent
            </span>
            <span className="flex items-center">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 mr-1.5" />
              Synthetic Research Benchmark
            </span>
          </div>
        </div>

        {/* Product Preview Card */}
        <div id="preview" className="mt-16 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/90 shadow-2xl shadow-indigo-950/50 p-6 md:p-8 backdrop-blur-xl">
            <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 mb-6 border-b border-slate-800 gap-4">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" />
                <div>
                  <h3 className="text-sm font-semibold text-white">Live Behavioural Telemetry Preview</h3>
                  <p className="text-xs text-slate-400">Baseline vs Shift Analysis • Subject Profile: Synthetic Benchmark</p>
                </div>
              </div>
              <div className="flex items-center space-x-2 text-xs font-mono bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 text-slate-300">
                <Activity className="w-3.5 h-3.5 text-indigo-400" />
                <span>Drift Status: STABLE (p=0.482)</span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4">
                <span className="text-xs text-slate-400">Baseline Focus Window</span>
                <p className="text-2xl font-bold text-white mt-1">4.6 hrs/day</p>
                <div className="flex items-center text-xs text-emerald-400 mt-2">
                  <TrendingUp className="w-3.5 h-3.5 mr-1" />
                  <span>Optimal Circadian Range (09:00 - 13:30)</span>
                </div>
              </div>

              <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4">
                <span className="text-xs text-slate-400">Context Switching Frequency</span>
                <p className="text-2xl font-bold text-white mt-1">8.2 / hr</p>
                <div className="flex items-center text-xs text-indigo-400 mt-2">
                  <Sparkles className="w-3.5 h-3.5 mr-1" />
                  <span>Recommendation: Group 45m deep sprints</span>
                </div>
              </div>

              <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4">
                <span className="text-xs text-slate-400">What-if Simulated Delta</span>
                <p className="text-2xl font-bold text-cyan-400 mt-1">+14.2%</p>
                <div className="flex items-center text-xs text-slate-400 mt-2">
                  <Sliders className="w-3.5 h-3.5 mr-1" />
                  <span>Scenario: -20% notifications</span>
                </div>
              </div>
            </div>

            <div className="bg-indigo-950/30 border border-indigo-900/40 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div className="flex items-center space-x-3">
                <Bot className="w-5 h-5 text-indigo-400 shrink-0" />
                <span className="text-xs text-indigo-200">
                  <strong>Cognitive Agent Finding:</strong> Stable focus velocity maintained. No statistically significant drift detected across current 14-day evaluation window.
                </span>
              </div>
              <Link
                to="/signup"
                className="shrink-0 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 px-3 py-1.5 rounded-lg transition-colors"
              >
                Launch Your Twin
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-24 border-b border-slate-900 bg-slate-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-xs uppercase tracking-widest font-semibold text-indigo-400 mb-2">
              Core Capabilities
            </h2>
            <p className="text-3xl sm:text-4xl font-bold tracking-tight text-white">
              Evidence-based analytics for behavioural intelligence
            </p>
            <p className="mt-4 text-base text-slate-400">
              Each capability is grounded in statistical modelling, reproducible feature engineering, and auditable reasoning.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div className="bg-slate-900/60 border border-slate-800/90 rounded-2xl p-6 hover:border-slate-700 transition-all">
              <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-5">
                <BrainCircuit className="w-6 h-6 text-indigo-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">Behavioural Intelligence</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Establishes dynamic personal baselines across temporal patterns, focus stamina, meeting loads, and circadian rhythms.
              </p>
            </div>

            <div className="bg-slate-900/60 border border-slate-800/90 rounded-2xl p-6 hover:border-slate-700 transition-all">
              <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mb-5">
                <Activity className="w-6 h-6 text-cyan-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">Statistical Drift Detection</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Monitors behavioral distribution shifts using rigorous Kolmogorov-Smirnov statistical tests to flag emerging friction before burnout occurs.
              </p>
            </div>

            <div className="bg-slate-900/60 border border-slate-800/90 rounded-2xl p-6 hover:border-slate-700 transition-all">
              <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center mb-5">
                <Sparkles className="w-6 h-6 text-purple-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">Actionable Interventions</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Generates transparent, prioritized recommendations tied directly to quantitative telemetry metrics, without arbitrary scoring.
              </p>
            </div>

            <div className="bg-slate-900/60 border border-slate-800/90 rounded-2xl p-6 hover:border-slate-700 transition-all">
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center mb-5">
                <Sliders className="w-6 h-6 text-blue-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">What-if Scenario Simulation</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Interactively evaluate hypothetical parameter adjustments (e.g., meeting reduction) to inspect simulated productivity bounds.
              </p>
            </div>

            <div className="bg-slate-900/60 border border-slate-800/90 rounded-2xl p-6 hover:border-slate-700 transition-all">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-5">
                <Bot className="w-6 h-6 text-emerald-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">Autonomous LangGraph Agent</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Multi-step reasoning engine powered by Gemini that dynamically queries analytical tools, validates assertions, and discloses limitations.
              </p>
            </div>

            <div className="bg-slate-900/60 border border-slate-800/90 rounded-2xl p-6 hover:border-slate-700 transition-all">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mb-5">
                <History className="w-6 h-6 text-amber-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">Auditable Execution History</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Comprehensive PostgreSQL audit trails recording latency, tool invocations, prompts, and verification states for complete accountability.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-24 border-b border-slate-900 bg-slate-950/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-xs uppercase tracking-widest font-semibold text-indigo-400 mb-2">
              Methodology
            </h2>
            <p className="text-3xl sm:text-4xl font-bold tracking-tight text-white">
              How Cognitive Twin evaluates behavioural signals
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
            <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl">
              <div className="text-xs font-mono font-bold text-indigo-400 mb-2">01</div>
              <h4 className="text-sm font-semibold text-white mb-1.5">Establish Baseline</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Collects observable behavioral signals across reference timeframes to map normal variance.
              </p>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl">
              <div className="text-xs font-mono font-bold text-cyan-400 mb-2">02</div>
              <h4 className="text-sm font-semibold text-white mb-1.5">Detect Shift</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Applies two-sample KS hypothesis testing to isolate significant covariate drift from routine variance.
              </p>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl">
              <div className="text-xs font-mono font-bold text-purple-400 mb-2">03</div>
              <h4 className="text-sm font-semibold text-white mb-1.5">Generate Actions</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Synthesizes evidence-linked recommendations with prioritized scores and measurable targets.
              </p>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl">
              <div className="text-xs font-mono font-bold text-blue-400 mb-2">04</div>
              <h4 className="text-sm font-semibold text-white mb-1.5">Simulate Scenarios</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Explores counterfactual feature perturbations through predictive productivity regression models.
              </p>
            </div>

            <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl">
              <div className="text-xs font-mono font-bold text-emerald-400 mb-2">05</div>
              <h4 className="text-sm font-semibold text-white mb-1.5">Audit & Review</h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Every inquiry trace, tool execution, and limitation disclosure is logged for full user verification.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Responsible AI & Research Integrity */}
      <section id="responsible-ai" className="py-20 border-b border-slate-900 bg-slate-950">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="rounded-2xl border border-indigo-900/40 bg-gradient-to-b from-indigo-950/20 to-slate-900/50 p-8">
            <div className="flex items-center space-x-3 mb-4">
              <ShieldCheck className="w-6 h-6 text-indigo-400" />
              <h3 className="text-xl font-bold text-white">Responsible AI & Research Integrity Statement</h3>
            </div>

            <div className="space-y-4 text-sm text-slate-300 leading-relaxed">
              <p>
                <strong>Synthetic Benchmark Prototype:</strong> The current system operates strictly on reproducible synthetic behavioural telemetry datasets. It does not harvest private biometric, webcam, or keystroke data.
              </p>
              <p>
                <strong>Statistical Estimates vs Causal Truth:</strong> What-if scenario projections and drift tests are empirical statistical approximations. They are not causal guarantees or medical/psychological diagnoses.
              </p>
              <p>
                <strong>Server-Enforced Access Control:</strong> All telemetry records and audit trails are isolated by strict backend role-based access control (RBAC). Regular users have zero access to administrative infrastructure diagnostics or other users' profiles.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Final Call to Action */}
      <section className="py-24 text-center bg-gradient-to-b from-slate-950 to-slate-900/60">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Ready to explore your behavioural intelligence?
          </h2>
          <p className="mt-4 text-base text-slate-400 max-w-xl mx-auto">
            Experience personalized telemetry insights, interactive drift diagnostics, and agentic inquiry.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/signup"
              className="inline-flex items-center justify-center px-6 py-3.5 rounded-xl text-base font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-lg shadow-indigo-600/30 transition-all hover:-translate-y-0.5"
            >
              Create Account
              <ArrowRight className="w-5 h-5 ml-2" />
            </Link>
            <Link
              to="/signin"
              className="inline-flex items-center justify-center px-6 py-3.5 rounded-xl text-base font-medium text-slate-300 hover:text-white bg-slate-900 border border-slate-800 transition-colors"
            >
              Sign In to Existing Account
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-slate-900 bg-slate-950 text-slate-400 text-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center space-x-3">
            <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center">
              <BrainCircuit className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold text-slate-200">Cognitive Twin</span>
            <span className="text-xs text-slate-500">• Autonomous Behavioural Intelligence</span>
          </div>

          <div className="flex items-center space-x-6 text-xs">
            <Link to="/privacy" className="hover:text-slate-200 transition-colors">Privacy Policy</Link>
            <Link to="/terms" className="hover:text-slate-200 transition-colors">Terms of Use</Link>
            <a href="#responsible-ai" className="hover:text-slate-200 transition-colors">Ethics & AI</a>
          </div>

          <div className="text-xs text-slate-500">
            © {new Date().getFullYear()} Cognitive Twin Prototype. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
};
