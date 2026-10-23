import React from 'react';
import { useDemo } from '../../context/DemoContext';
import { Sparkles } from 'lucide-react';

export const DemoEnvironmentBanner: React.FC = () => {
  const { isDemoMode, activePersonaId, activePersona, personas, setActivePersonaId, toggleDemoMode } =
    useDemo();

  if (!isDemoMode) {
    return (
      <div className="bg-slate-900 border-b border-slate-800 px-4 py-2 flex items-center justify-between text-xs">
        <div className="flex items-center space-x-2 text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>Live Account Telemetry Mode</span>
        </div>
        <button
          onClick={toggleDemoMode}
          className="text-xs text-indigo-400 hover:text-indigo-300 font-medium underline"
        >
          Switch to Synthetic Demo Environment
        </button>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-indigo-950/90 via-slate-900 to-slate-950 border-b border-indigo-900/40 px-4 sm:px-6 py-2.5 text-xs text-slate-300 shadow-sm">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
        {/* Left Indicator */}
        <div className="flex items-center space-x-2.5">
          <div className="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
            <Sparkles className="w-3 h-3 text-cyan-400" />
            <span>Demo Environment · Synthetic Data</span>
          </div>
          <span className="text-slate-400 hidden sm:inline text-[11px]">
            Reproducible behavioral scenarios for evaluation
          </span>
        </div>

        {/* Right Persona Selector & Switcher */}
        <div className="flex items-center space-x-3 w-full md:w-auto justify-between md:justify-end">
          <div className="flex items-center space-x-2">
            <span className="text-[11px] text-slate-400 hidden sm:inline">Active Scenario:</span>
            <select
              value={activePersonaId}
              onChange={(e) => setActivePersonaId(e.target.value)}
              className="bg-slate-900 border border-slate-700/80 hover:border-indigo-500 text-white text-xs rounded-lg px-2.5 py-1 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-medium cursor-pointer"
            >
              {personas.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.archetype})
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 bg-slate-800 text-cyan-300 rounded text-[11px] font-mono">
              {activePersona.baseline.meanFocusHours}h Focus / {activePersona.baseline.meanMeetingHours}h Mtgs
            </span>

            <button
              onClick={toggleDemoMode}
              title="Toggle to Live Account Mode"
              className="text-[11px] text-slate-400 hover:text-white px-2 py-0.5 rounded hover:bg-slate-800 transition"
            >
              Live Mode
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
