import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Menu, Shield, LogOut, ArrowLeft } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';

interface AdminHeaderProps {
  onOpenMobile: () => void;
}

export const AdminHeader: React.FC<AdminHeaderProps> = ({ onOpenMobile }) => {
  const { user, logout } = useAuth();
  const [systemState, setSystemState] = useState<'operational' | 'degraded' | 'checking'>('checking');

  useEffect(() => {
    let mounted = true;
    const checkState = async () => {
      try {
        const res = await api.getHealth();
        if (mounted) {
          setSystemState(res.status === 'ok' ? 'operational' : 'degraded');
        }
      } catch {
        if (mounted) {
          setSystemState('degraded');
        }
      }
    };
    checkState();
    const interval = setInterval(checkState, 30000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="sticky top-0 z-30 h-16 bg-slate-900 border-b border-slate-800 px-4 sm:px-6 flex items-center justify-between shadow-xs">
      <div className="flex items-center space-x-3">
        <button
          type="button"
          onClick={onOpenMobile}
          className="p-2 -ml-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 lg:hidden focus:outline-none"
          aria-label="Open mobile navigation"
        >
          <Menu className="w-5 h-5" aria-hidden="true" />
        </button>
        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
            <Shield className="w-3 h-3 mr-1" />
            Admin Scope
          </span>
          <span className="text-xs text-slate-400 hidden sm:inline">
            Operational Governance & Telemetry Control
          </span>
        </div>
      </div>

      <div className="flex items-center space-x-3 sm:space-x-4">
        {/* System Readiness Pill */}
        <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium border border-slate-700 bg-slate-950">
          <span
            className={`w-2 h-2 rounded-full ${
              systemState === 'operational'
                ? 'bg-emerald-500'
                : systemState === 'checking'
                ? 'bg-amber-400 animate-pulse'
                : 'bg-rose-500'
            }`}
          />
          <span className="text-slate-300 capitalize text-[11px]">
            Backend: {systemState}
          </span>
        </div>

        {/* Return to User Workspace */}
        <Link
          to="/app"
          className="hidden md:inline-flex items-center text-xs font-medium text-slate-300 hover:text-white px-2.5 py-1 rounded-lg border border-slate-700 hover:bg-slate-800 transition"
        >
          <ArrowLeft className="w-3 h-3 mr-1.5 text-indigo-400" />
          User Workspace
        </Link>

        {/* Current Admin Pill */}
        <div className="flex items-center space-x-2 pl-3 border-l border-slate-800">
          <div className="w-7 h-7 rounded-full bg-amber-600/30 text-amber-300 border border-amber-500/40 flex items-center justify-center font-bold text-xs">
            {(user?.display_name || user?.username || 'A')[0].toUpperCase()}
          </div>
          <div className="hidden lg:block text-left text-xs">
            <span className="font-semibold text-slate-200 block leading-tight">
              {user?.display_name || user?.username}
            </span>
            <span className="text-[10px] text-amber-400 block leading-tight">
              Administrator
            </span>
          </div>
        </div>

        {/* Sign Out */}
        <button
          type="button"
          onClick={logout}
          className="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
          title="Sign out of administrator console"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Sign Out</span>
        </button>
      </div>
    </header>
  );
};
