import React, { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { api, ApiClientError } from '../../services/api';
import type { AdminSecurityResponse } from '../../types/api';
import {
  ShieldCheck,
  Users,
  Lock,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  FileText,
  Activity,
} from 'lucide-react';

export const AdminSecurityPage: React.FC = () => {
  const { token } = useAuth();
  const [data, setData] = useState<AdminSecurityResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSecurity = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAdminSecurity(token || undefined);
      setData(res);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      } else {
        setError('Failed to load security posture and access events.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSecurity();
  }, [token]);

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Security & Access Governance</h1>
          <p className="text-slate-400 mt-1 text-sm">
            Cryptographic controls, active account partitioning, role enforcement, and authentication event auditing.
          </p>
        </div>
        <button
          onClick={fetchSecurity}
          disabled={loading}
          className="flex items-center space-x-2 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-sm font-medium transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="flex items-center space-x-2 p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-sm">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Account Partitioning Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Registered Accounts</span>
            <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-white">{data?.total_registered_users ?? '—'}</span>
            <div className="text-xs text-slate-500 mt-0.5">Persisted in PostgreSQL database</div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Privileged Administrators</span>
            <div className="p-2 bg-purple-500/10 text-purple-400 rounded-lg">
              <ShieldCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-purple-400">{data?.admin_accounts_count ?? '—'}</span>
            <div className="text-xs text-slate-500 mt-0.5">Assigned role: &quot;admin&quot;</div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Standard Users</span>
            <div className="p-2 bg-cyan-500/10 text-cyan-400 rounded-lg">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-cyan-400">{data?.regular_accounts_count ?? '—'}</span>
            <div className="text-xs text-slate-500 mt-0.5">Restricted strictly to personal telemetry</div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Active Accounts</span>
            <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-emerald-400">{data?.active_sessions_count ?? '—'}</span>
            <div className="text-xs text-slate-500 mt-0.5">Active authorization status</div>
          </div>
        </div>
      </div>

      {/* Security Posture Controls */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-2.5 bg-emerald-500/10 text-emerald-400 rounded-lg">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">Active Cryptographic & Security Controls</h2>
            <p className="text-xs text-slate-400">Server-enforced defense mechanisms protecting customer data and models</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data?.security_posture &&
            Object.entries(data.security_posture).map(([key, description]) => (
              <div key={key} className="p-4 bg-slate-950 border border-slate-800 rounded-lg flex items-start space-x-3">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-semibold text-white uppercase tracking-wider block mb-1">
                    {key.replace(/_/g, ' ')}
                  </span>
                  <p className="text-xs text-slate-300 leading-relaxed">{description}</p>
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* Recent Access Events */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-2.5 bg-indigo-500/10 text-indigo-400 rounded-lg">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">Authentication & Account Lifecycle Audit</h2>
            <p className="text-xs text-slate-400">Recent security events captured in audit storage</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-medium">
                <th className="pb-3 px-3">Event Type</th>
                <th className="pb-3 px-3">Actor / Email</th>
                <th className="pb-3 px-3">Assigned Role</th>
                <th className="pb-3 px-3">Status</th>
                <th className="pb-3 px-3">Timestamp</th>
                <th className="pb-3 px-3">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {data?.recent_access_events && data.recent_access_events.length > 0 ? (
                data.recent_access_events.map((evt, idx) => (
                  <tr key={idx} className="hover:bg-slate-850/50 transition-colors">
                    <td className="py-3 px-3 font-mono font-semibold text-indigo-300">{evt.event_type}</td>
                    <td className="py-3 px-3 text-white font-medium">{evt.actor}</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-300 capitalize">
                        {evt.role}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>{evt.status}</span>
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-400 font-mono text-[11px]">
                      {evt.timestamp ? new Date(evt.timestamp).toLocaleString() : 'Recent'}
                    </td>
                    <td className="py-3 px-3 text-slate-300 max-w-xs truncate">{evt.description}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500">
                    No access events recorded.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
