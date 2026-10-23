import React from 'react';
import { Link } from 'react-router-dom';
import { BrainCircuit, ArrowLeft, ShieldCheck, Lock, EyeOff, Server } from 'lucide-react';

export const PrivacyPage: React.FC = () => {
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
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Privacy & Data Protection Policy</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Privacy Policy
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Last updated: October 2026 • Cognitive Twin Behavioural Intelligence Prototype
          </p>
        </div>

        <div className="space-y-8 text-sm text-slate-300 leading-relaxed">
          <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
            <h2 className="text-base font-semibold text-white flex items-center mb-3">
              <EyeOff className="w-4 h-4 text-indigo-400 mr-2" />
              1. Research Prototype & Synthetic Telemetry
            </h2>
            <p>
              Cognitive Twin is an experimental behavioral intelligence platform designed for cognitive modeling and drift evaluation. In its current implementation, the application utilizes <strong>synthetic benchmark telemetry</strong> modeled after typical computational workflows (focus hours, meeting load, context switching). It does not record keystrokes, webcam feeds, screen captures, or private personal communications.
            </p>
          </section>

          <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
            <h2 className="text-base font-semibold text-white flex items-center mb-3">
              <Lock className="w-4 h-4 text-indigo-400 mr-2" />
              2. Authentication & Credential Storage
            </h2>
            <p>
              Account passwords are cryptographically salted and hashed using industry-standard <strong>PBKDF2-HMAC-SHA256</strong> with 100,000 rounds. Plaintext passwords are never logged, persisted, or transmitted back to clients. Authentication sessions use signed JSON Web Tokens (JWT) stored in browser session storage and automatically invalidated upon sign out.
            </p>
          </section>

          <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
            <h2 className="text-base font-semibold text-white flex items-center mb-3">
              <Server className="w-4 h-4 text-indigo-400 mr-2" />
              3. Role-Based Access Isolation (RBAC)
            </h2>
            <p>
              The system implements strict server-enforced role-based access control. Regular authenticated users can only view their own behavioral baseline insights, recommendations, and execution history. Operational telemetry, server connection strings, and system health metrics are strictly segregated and restricted to authorized administrative principals.
            </p>
          </section>

          <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
            <h2 className="text-base font-semibold text-white flex items-center mb-3">
              <ShieldCheck className="w-4 h-4 text-indigo-400 mr-2" />
              4. External LLM & Agent Interactions
            </h2>
            <p>
              When utilizing the Gemini-powered cognitive reasoning agent, requests are executed via secure server-side API calls. User queries and synthetic telemetry summaries are processed according to strict data boundaries. Third-party providers do not retain user queries for model training.
            </p>
          </section>

          <div className="pt-6 border-t border-slate-900 flex justify-between items-center text-xs text-slate-500">
            <span>Cognitive Twin System Privacy Framework</span>
            <Link to="/terms" className="text-indigo-400 hover:underline">View Terms of Service →</Link>
          </div>
        </div>
      </main>
    </div>
  );
};
