import React from 'react';
import { Link } from 'react-router-dom';
import { Menu, LogOut, Shield } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface UserHeaderProps {
  onOpenMobile: () => void;
}

export const UserHeader: React.FC<UserHeaderProps> = ({ onOpenMobile }) => {
  const { user, isAdmin, logout } = useAuth();

  return (
    <header className="sticky top-0 z-30 h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-4 sm:px-6 flex items-center justify-between shadow-xs">
      <div className="flex items-center space-x-3">
        <button
          type="button"
          onClick={onOpenMobile}
          className="p-2 -ml-2 rounded-lg text-slate-500 hover:text-slate-700 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-white dark:hover:bg-slate-800 lg:hidden focus:outline-none"
          aria-label="Open mobile navigation"
        >
          <Menu className="w-5 h-5" aria-hidden="true" />
        </button>
        <div className="text-xs text-slate-600 dark:text-slate-300 font-medium">
          Personal Behavioural Twin Workspace
        </div>
      </div>

      <div className="flex items-center space-x-3 sm:space-x-4">
        {/* Admin Switcher if role is admin */}
        {isAdmin && (
          <Link
            to="/admin"
            className="hidden sm:inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 hover:bg-amber-500/20 transition-colors"
          >
            <Shield className="w-3.5 h-3.5 mr-1.5" />
            Admin Console
          </Link>
        )}

        {/* Current User Pill */}
        <div className="flex items-center space-x-2 pl-3 border-l border-slate-200 dark:border-slate-800">
          <div className="w-7 h-7 rounded-full bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 flex items-center justify-center font-bold text-xs">
            {(user?.display_name || user?.username || 'U')[0].toUpperCase()}
          </div>
          <div className="hidden md:block text-left text-xs">
            <span className="font-semibold text-slate-800 dark:text-slate-200 block leading-tight">
              {user?.display_name || user?.username}
            </span>
            <span className="text-[10px] text-slate-400 block leading-tight">
              {user?.email || 'Authenticated User'}
            </span>
          </div>
        </div>

        {/* Sign Out */}
        <button
          type="button"
          onClick={logout}
          className="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-600 dark:text-slate-300 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          title="Sign out of personal workspace"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Sign Out</span>
        </button>
      </div>
    </header>
  );
};
