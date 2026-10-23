import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  BrainCircuit,
  Activity,
  Sparkles,
  Sliders,
  Bot,
  History,
  Server,
  X,
} from 'lucide-react';

interface SidebarProps {
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

interface NavItem {
  label: string;
  path: string;
  icon: React.ComponentType<{ className?: string; 'aria-hidden'?: boolean | 'true' | 'false' }>;
  description: string;
}

const navItems: NavItem[] = [
  {
    label: 'Overview',
    path: '/',
    icon: LayoutDashboard,
    description: 'System health & recent activity',
  },
  {
    label: 'Behavioural Insights',
    path: '/insights',
    icon: BrainCircuit,
    description: 'User telemetry & baseline metrics',
  },
  {
    label: 'Drift Detection',
    path: '/drift',
    icon: Activity,
    description: 'Statistical covariate shift tests',
  },
  {
    label: 'Recommendations',
    path: '/recommendations',
    icon: Sparkles,
    description: 'Targeted behavioural interventions',
  },
  {
    label: 'What-if Simulation',
    path: '/simulation',
    icon: Sliders,
    description: 'Hypothetical scenario projections',
  },
  {
    label: 'AI Agent Workspace',
    path: '/agent',
    icon: Bot,
    description: 'LangGraph multi-tool reasoning',
  },
  {
    label: 'Execution History',
    path: '/history',
    icon: History,
    description: 'Auditable runs & telemetry records',
  },
  {
    label: 'System Status',
    path: '/status',
    icon: Server,
    description: 'Readiness & database diagnostics',
  },
];

export const Sidebar: React.FC<SidebarProps> = ({ mobileOpen, onCloseMobile }) => {
  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/60 backdrop-blur-sm lg:hidden"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      {/* Sidebar container */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-72 bg-slate-900 text-slate-100 flex flex-col border-r border-slate-800 transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-label="Main Navigation"
      >
        {/* Brand header */}
        <div className="h-16 px-6 flex items-center justify-between border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Bot className="w-5 h-5 text-white" aria-hidden="true" />
            </div>
            <div>
              <h1 className="text-sm font-bold tracking-tight text-white flex items-center gap-1.5">
                Cognitive Twin
                <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  v1.0
                </span>
              </h1>
              <p className="text-[11px] text-slate-400">Autonomous Behavioural Intelligence</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onCloseMobile}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 lg:hidden focus:outline-none focus:ring-2 focus:ring-indigo-400"
            aria-label="Close navigation"
          >
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>

        {/* Navigation list */}
        <nav className="flex-1 overflow-y-auto px-4 py-4 space-y-1">
          <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Intelligence Modules
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                onClick={onCloseMobile}
                className={({ isActive }) =>
                  `flex items-start space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all group ${
                    isActive
                      ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                      : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon
                      className={`w-5 h-5 mt-0.5 shrink-0 transition-colors ${
                        isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'
                      }`}
                      aria-hidden="true"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="truncate leading-snug">{item.label}</div>
                      <div
                        className={`text-[11px] truncate ${
                          isActive ? 'text-indigo-200' : 'text-slate-400'
                        }`}
                      >
                        {item.description}
                      </div>
                    </div>
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Footnote / Disclaimer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/40 text-[11px] text-slate-400 space-y-1">
          <div className="font-medium text-slate-300">Synthetic Twin Environment</div>
          <p className="leading-tight">
            Predictions & simulations are non-causal estimates based on statistical models.
          </p>
        </div>
      </aside>
    </>
  );
};
