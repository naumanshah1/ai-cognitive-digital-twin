import React from 'react';
import { Link } from 'react-router-dom';
import { BrainCircuit, ArrowLeft, AlertTriangle, FileText, CheckCircle2 } from 'lucide-react';

export const TermsPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-200">
      <nav className="border-b border-slate-900 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
              <BrainCircuit className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-white">Cognitive Twin</span>
          </Link>
          <Link to="/" className="text-xs font-medium text-slate-400 hover:text-white flex items-center">
            <ArrowLeft className="w-3.5 h-3.5 mr-1" />
            Back to Home
          </Link>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="border-b border-slate-900 pb-8 mb-10">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-4">
            <FileText className="w-3.5 h-3.5" />
            <span>Product Terms & Research Disclaimer</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Terms of Use
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Last updated: October 2026 • Cognitive Twin Behavioural Intelligence Prototype
          </p>
        </div>

        <div className="space-y-8 text-sm text-slate-300 leading-relaxed">
          <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
            <h2 className="text-base font-semibold text-white flex items-center mb-3">
              <AlertTriangle className="w-4 h-4 text-amber-400 mr-2" />
              1. Non-Clinical & Non-Causal Prototype Scope
            </h2>
            <p>
              Cognitive Twin is an experimental research system for evaluating automated behavioural intelligence algorithms. <strong>The system does not provide medical, clinical, psychological, or psychiatric diagnosis or therapy.</strong> Statistical drift indicators and counterfactual what-if simulations represent correlational approximations derived from computational models and synthetic benchmarks. They are not guarantees of future human performance or mental wellbeing.
            </p>
          </section>

          <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
            <h2 className="text-base font-semibold text-white flex items-center mb-3">
              <CheckCircle2 className="w-4 h-4 text-indigo-400 mr-2" />
              2. Acceptable Use
            </h2>
            <p>
              Users agree to use the Cognitive Twin service solely for authorized educational, research, and self-reflection evaluation purposes. Attempting to bypass role-based access restrictions, access other users' audit trails, or overload backend APIs through automated probing is strictly prohibited.
            </p>
          </section>

          <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
            <h2 className="text-base font-semibold text-white flex items-center mb-3">
              <FileText className="w-4 h-4 text-indigo-400 mr-2" />
              3. Service Availability & Modifications
            </h2>
            <p>
              As an active developmental prototype, features and model endpoints may be modified, refined, or taken offline for maintenance without prior notice. Operational diagnostics and database health metrics are reserved for system administrators.
            </p>
          </section>

          <div className="pt-6 border-t border-slate-900 flex justify-between items-center text-xs text-slate-500">
            <span>Cognitive Twin Prototype Terms</span>
            <Link to="/privacy" className="text-indigo-400 hover:underline">View Privacy Policy →</Link>
          </div>
        </div>
      </main>
    </div>
  );
};
