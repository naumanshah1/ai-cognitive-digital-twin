import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import {
  LayoutDashboard,
  BrainCircuit,
  Activity,
  Sparkles,
  Sliders,
  Bot,
  History,
  Shield,
  Settings,
  X,
  LogOut,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface UserSidebarProps {
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

interface NavItem {
  label: string;
  path: string;
  icon: React.ComponentType<{ className?: string; 'aria-hidden'?: boolean | 'true' | 'false' }>;
  description: string;
  exact?: boolean;
}

const navItems: NavItem[] = [
  {
    label: 'My Overview',
    path: '/app',
    icon: LayoutDashboard,
    description: 'Personal summary & metrics',
    exact: true,
  },
  {
    label: 'Behavioural Insights',
    path: '/app/insights',
    icon: BrainCircuit,
    description: 'Baseline metrics & telemetry',
  },
  {
    label: 'Drift Detection',
    path: '/app/drift',
    icon: Activity,
    description: 'Observed shift indicators',
  },
  {
    label: 'Recommendations',
    path: '/app/recommendations',
    icon: Sparkles,
    description: 'Targeted action plans',
  },
  {
    label: 'What-if Simulation',
    path: '/app/simulation',
    icon: Sliders,
    description: 'Hypothetical projections',
  },
  {
    label: 'AI Agent Workspace',
    path: '/app/agent',
    icon: Bot,
    description: 'Cognitive reasoning agent',
  },
  {
    label: 'Execution History',
    path: '/app/history',
    icon: History,
    description: 'My auditable inquiries',
  },
  {
    label: 'Account & Settings',
    path: '/app/settings',
    icon: Settings,
    description: 'Profile & security controls',
  },
];

export const UserSidebar: React.FC<UserSidebarProps> = ({ mobileOpen, onCloseMobile }) => {
  const { user, isAdmin, logout } = useAuth();

  return (
    <>
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/60 backdrop-blur-sm lg:hidden"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-72 bg-slate-900 text-slate-100 flex flex-col border-r border-slate-800 transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-label="User Navigation"
      >
        {/* Brand header */}
        <div className="h-16 px-6 flex items-center justify-between border-b border-slate-800">
          <Link to="/app" className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <BrainCircuit className="w-5 h-5 text-white" aria-hidden="true" />
            </div>
            <div>
              <span className="text-base font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                Cognitive Twin
              </span>
              <span className="block text-[10px] uppercase tracking-wider font-semibold text-indigo-400 -mt-1">
                Personal Workspace
              </span>
            </div>
          </Link>
          <button
            type="button"
            onClick={onCloseMobile}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 lg:hidden focus:outline-none"
            aria-label="Close navigation"
          >
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>

        {/* Navigation links */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-1">
          <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Intelligence Modules
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.exact}
                onClick={onCloseMobile}
                className={({ isActive }) =>
                  `group flex items-start px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-indigo-600/15 text-indigo-300 border border-indigo-500/30 shadow-xs'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
                  }`
                }
              >
                <Icon className="w-4 h-4 mt-0.5 shrink-0 transition-colors" aria-hidden="true" />
                <div className="ml-3">
                  <span className="block font-semibold text-slate-200 group-hover:text-white">
                    {item.label}
                  </span>
                  <span className="block text-[11px] text-slate-400 font-normal">
                    {item.description}
                  </span>
                </div>
              </NavLink>
            );
          })}

          {/* Admin console link if user is administrator */}
          {isAdmin && (
            <div className="pt-4 mt-4 border-t border-slate-800">
              <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-amber-400/90 flex items-center">
                <Shield className="w-3 h-3 mr-1.5" />
                Administrative Access
              </div>
              <Link
                to="/admin"
                onClick={onCloseMobile}
                className="group flex items-center px-3 py-2 rounded-xl text-xs font-medium text-amber-300 hover:bg-amber-500/10 border border-amber-500/20 transition-colors"
              >
                <span>Switch to Admin Console →</span>
              </Link>
            </div>
          )}
        </div>

        {/* User Account Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/60">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3 overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center font-bold text-xs text-indigo-300 shrink-0">
                {(user?.display_name || user?.username || 'U')[0].toUpperCase()}
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-semibold text-white truncate">
                  {user?.display_name || user?.username || 'Authenticated User'}
                </p>
                <p className="text-[11px] text-slate-400 truncate">
                  {user?.email || user?.username}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={logout}
              title="Sign out"
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
              aria-label="Sign out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};
