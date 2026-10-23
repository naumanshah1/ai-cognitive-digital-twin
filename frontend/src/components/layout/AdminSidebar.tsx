import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import {
  Shield,
  Activity,
  Server,
  Users,
  FileText,
  BarChart3,
  Lock,
  Sliders,
  ArrowLeft,
  X,
  LogOut,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface AdminSidebarProps {
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

const adminNavItems = [
  {
    label: 'Admin Overview',
    path: '/admin',
    icon: Activity,
    description: 'System operational status',
    exact: true,
  },
  {
    label: 'System Health',
    path: '/admin/health',
    icon: Server,
    description: 'Database & engine diagnostics',
  },
  {
    label: 'User Management',
    path: '/admin/users',
    icon: Users,
    description: 'Registered accounts & roles',
  },
  {
    label: 'Audit History',
    path: '/admin/audit',
    icon: FileText,
    description: 'System-wide execution logs',
  },
  {
    label: 'Analytics & Performance',
    path: '/admin/analytics',
    icon: BarChart3,
    description: 'Model metrics & tool usage',
  },
  {
    label: 'Security & Access',
    path: '/admin/security',
    icon: Lock,
    description: 'Access controls & audit log',
  },
  {
    label: 'Configuration',
    path: '/admin/configuration',
    icon: Sliders,
    description: 'Integrations & runtime config',
  },
];

export const AdminSidebar: React.FC<AdminSidebarProps> = ({ mobileOpen, onCloseMobile }) => {
  const { user, logout } = useAuth();

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
        className={`fixed top-0 bottom-0 left-0 z-50 w-72 bg-slate-950 text-slate-100 flex flex-col border-r border-slate-800 transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-label="Admin Navigation"
      >
        {/* Brand header */}
        <div className="h-16 px-6 flex items-center justify-between border-b border-slate-800 bg-slate-900/40">
          <Link to="/admin" className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-amber-600 via-amber-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-amber-600/20">
              <Shield className="w-5 h-5 text-white" aria-hidden="true" />
            </div>
            <div>
              <span className="text-base font-bold tracking-tight text-white">
                Admin Console
              </span>
              <span className="block text-[10px] uppercase tracking-wider font-semibold text-amber-400 -mt-1">
                Cognitive Twin Ops
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
            Operations & Governance
          </div>
          {adminNavItems.map((item) => {
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
                      ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30 shadow-xs'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent'
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

          {/* Quick Return to Personal Workspace */}
          <div className="pt-4 mt-4 border-t border-slate-800/80">
            <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-indigo-400/90">
              User Experience
            </div>
            <Link
              to="/app"
              onClick={onCloseMobile}
              className="group flex items-center px-3 py-2 rounded-xl text-xs font-medium text-indigo-300 hover:bg-indigo-600/10 border border-indigo-500/20 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5 mr-2" />
              <span>Return to User Workspace</span>
            </Link>
          </div>
        </div>

        {/* Admin Account Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/40">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3 overflow-hidden">
              <div className="w-8 h-8 rounded-full bg-amber-600/30 border border-amber-500/40 flex items-center justify-center font-bold text-xs text-amber-300 shrink-0">
                {(user?.display_name || user?.username || 'A')[0].toUpperCase()}
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-semibold text-white truncate">
                  {user?.display_name || user?.username || 'Administrator'}
                </p>
                <p className="text-[11px] text-amber-400 font-medium truncate">
                  Authoritative Role: {user?.role || 'admin'}
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={logout}
              title="Sign out of administrator console"
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
