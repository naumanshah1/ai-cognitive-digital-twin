import React, { useState, useEffect } from 'react';
import { Menu, User, Shield, Activity } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { apiClient } from '../../services/api';
import { DEV_PERSONAS } from '../../services/auth';
import type { DevPersona } from '../../services/auth';

interface HeaderProps {
  onOpenMobile: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenMobile }) => {
  const { token, user, targetUserId, setTargetUserId, switchPersona, setManualToken } = useAuth();
  const [healthStatus, setHealthStatus] = useState<'healthy' | 'unhealthy' | 'checking'>('checking');
  const [isEditingToken, setIsEditingToken] = useState(false);
  const [tokenInput, setTokenInput] = useState(token || '');

  useEffect(() => {
    let mounted = true;
    const checkLiveness = async () => {
      try {
        const res = await apiClient.getHealth();
        if (mounted) {
          setHealthStatus(res.status === 'ok' ? 'healthy' : 'unhealthy');
        }
      } catch {
        if (mounted) {
          setHealthStatus('unhealthy');
        }
      }
    };

    checkLiveness();
    const interval = setInterval(checkLiveness, 30000); // Check every 30s
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleCustomTokenSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setManualToken((tokenInput || '').trim());
    setIsEditingToken(false);
  };

  const isAdmin = user?.roles?.includes('admin') || user?.roles?.includes('researcher');

  return (
    <header className="sticky top-0 z-30 h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-4 sm:px-6 flex items-center justify-between shadow-xs">
      <div className="flex items-center space-x-3">
        <button
          type="button"
          onClick={onOpenMobile}
          className="p-2 -ml-2 rounded-lg text-slate-500 hover:text-slate-700 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-white dark:hover:bg-slate-800 lg:hidden focus:outline-none focus:ring-2 focus:ring-indigo-500"
          aria-label="Open mobile navigation"
        >
          <Menu className="w-5 h-5" aria-hidden="true" />
        </button>
        <div className="hidden sm:flex items-center space-x-2 text-xs text-slate-500 dark:text-slate-400">
          <Activity className="w-4 h-4 text-indigo-500" aria-hidden="true" />
          <span>Active Endpoint:</span>
          <code className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 font-mono text-slate-700 dark:text-slate-300">
            {apiClient.getBaseUrl()}
          </code>
        </div>
      </div>

      <div className="flex items-center space-x-3 sm:space-x-4">
        {/* Liveness Indicator */}
        <div
          className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium border"
          title={`Backend status: ${healthStatus}`}
        >
          <span
            className={`w-2 h-2 rounded-full ${
              healthStatus === 'healthy'
                ? 'bg-emerald-500 animate-pulse'
                : healthStatus === 'checking'
                ? 'bg-amber-400 animate-ping'
                : 'bg-rose-500'
            }`}
          />
          <span className="text-slate-600 dark:text-slate-300 capitalize text-[11px]">
            API: {healthStatus}
          </span>
        </div>

        {/* Target Synthetic User Selector */}
        <div className="flex items-center space-x-1.5">
          <label htmlFor="target-user-select" className="text-xs font-medium text-slate-600 dark:text-slate-300 hidden md:inline">
            Target User:
          </label>
          <select
            id="target-user-select"
            value={targetUserId}
            onChange={(e) => setTargetUserId(e.target.value)}
            className="text-xs font-medium px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            aria-label="Select target user"
          >
            {Array.from({ length: 10 }, (_, i) => {
              const uid = `user_${i.toString().padStart(2, '0')}`;
              return (
                <option key={uid} value={uid}>
                  {uid} {uid === user?.id ? '(Current Self)' : ''}
                </option>
              );
            })}
          </select>
        </div>

        {/* Persona / Dev Auth Switcher */}
        <div className="flex items-center space-x-1.5">
          <label htmlFor="auth-persona-select" className="sr-only">
            Auth Persona
          </label>
          <select
            id="auth-persona-select"
            value={DEV_PERSONAS.some((p: DevPersona) => p.token === token) ? (token || '') : 'custom'}
            onChange={(e) => {
              const val = e.target.value;
              if (val === 'custom') {
                setIsEditingToken(true);
              } else {
                switchPersona(val);
              }
            }}
            className="text-xs font-medium px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            aria-label="Select Authentication Persona"
          >
            {DEV_PERSONAS.map((p: DevPersona) => (
              <option key={p.token} value={p.token}>
                {p.label} ({p.role})
              </option>
            ))}
            <option value="custom">Custom Token...</option>
          </select>

          {/* User profile pill */}
          <div className="hidden xl:flex items-center space-x-1 px-2.5 py-1 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 rounded-lg text-xs font-medium border border-indigo-200 dark:border-indigo-800">
            <User className="w-3.5 h-3.5" aria-hidden="true" />
            <span>{user ? `${user.id} (${user.roles.join(', ')})` : 'Unauthenticated'}</span>
            {isAdmin && <Shield className="w-3 h-3 text-amber-500" aria-label="Admin" />}
          </div>
        </div>
      </div>

      {/* Custom Token Modal / Input Overlay */}
      {isEditingToken && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl shadow-xl max-w-md w-full p-6 border border-slate-200 dark:border-slate-800">
            <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100">
              Custom Bearer Token
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Enter a custom bearer token to test authorization headers, malformed tokens, or invalid credentials.
            </p>
            <form onSubmit={handleCustomTokenSubmit} className="mt-4 space-y-4">
              <div>
                <label htmlFor="custom-token-input" className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                  Token String
                </label>
                <input
                  id="custom-token-input"
                  type="text"
                  value={tokenInput}
                  onChange={(e) => setTokenInput(e.target.value)}
                  className="mt-1 block w-full px-3 py-2 text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono"
                  placeholder="e.g. dev-synthetic-00 or Bearer-xyz"
                />
              </div>
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setIsEditingToken(false)}
                  className="px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-xs"
                >
                  Apply Token
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </header>
  );
};
