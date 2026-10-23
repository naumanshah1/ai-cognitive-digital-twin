import React, { useState, useEffect } from 'react';
import {
  Search,
  Shield,
  RefreshCw,
} from 'lucide-react';
import { api, ApiClientError } from '../../services/api';
import type { AdminUserItem } from '../../types/api';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';

export const AdminUsersPage: React.FC = () => {
  const [users, setUsers] = useState<AdminUserItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  const fetchUsers = async () => {
    setError(null);
    try {
      const data = await api.getAdminUsers(100, 0);
      setUsers(data.items || []);
      setTotal(data.total || 0);
    } catch (err: unknown) {
      if (err instanceof ApiClientError && err.status === 403) {
        setError('Forbidden: Administrator privileges required to manage accounts.');
      } else {
        setError('Failed to load user accounts.');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchUsers();
  };

  const filteredUsers = users.filter((u) => {
    const q = searchQuery.toLowerCase();
    return (
      u.username.toLowerCase().includes(q) ||
      u.display_name.toLowerCase().includes(q) ||
      (u.email && u.email.toLowerCase().includes(q)) ||
      u.role.toLowerCase().includes(q)
    );
  });

  if (loading) {
    return <LoadingSpinner message="Retrieving registered user accounts..." fullHeight />;
  }

  return (
    <div className="space-y-6">
      {/* Title & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            User Account Management
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-400">
            Authoritative directory of registered tenant accounts and their assigned RBAC roles.
          </p>
        </div>

        <button
          type="button"
          onClick={handleRefresh}
          disabled={refreshing}
          className="inline-flex items-center space-x-2 px-3.5 py-2 text-xs font-medium rounded-xl text-slate-200 bg-slate-900 border border-slate-800 hover:bg-slate-800 transition disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-amber-400 ${refreshing ? 'animate-spin' : ''}`} />
          <span>{refreshing ? 'Refreshing...' : 'Refresh List'}</span>
        </button>
      </div>

      {error && (
        <div className="rounded-xl bg-rose-500/10 border border-rose-500/20 p-4 text-rose-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={fetchUsers} className="text-xs font-semibold underline ml-4">
            Retry
          </button>
        </div>
      )}

      {/* Filter / Search Bar */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by name, email, username or role..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50"
          />
        </div>
        <div className="text-xs text-slate-400 font-medium">
          Showing {filteredUsers.length} of {total} accounts
        </div>
      </div>

      {/* Users Table */}
      <div className="rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-800 text-xs text-left">
            <thead className="bg-slate-950/60">
              <tr className="text-slate-400 uppercase font-semibold text-[10px] tracking-wider">
                <th className="py-3 px-4">User</th>
                <th className="py-3 px-4">Email Address</th>
                <th className="py-3 px-4">Role</th>
                <th className="py-3 px-4">Account Status</th>
                <th className="py-3 px-4">Executions</th>
                <th className="py-3 px-4">Created Date</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-8 text-slate-500 text-xs">
                    No matching user accounts found.
                  </td>
                </tr>
              ) : (
                filteredUsers.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-slate-300">
                          {item.display_name ? item.display_name[0].toUpperCase() : 'U'}
                        </div>
                        <div>
                          <p className="font-semibold text-white">{item.display_name}</p>
                          <p className="text-[11px] font-mono text-slate-400">{item.username}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-300">
                      {item.email || <span className="text-slate-600">none (synthetic)</span>}
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                          item.role === 'admin'
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                            : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                        }`}
                      >
                        {item.role === 'admin' && <Shield className="w-3 h-3 mr-1" />}
                        {item.role}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="inline-flex items-center text-xs text-emerald-400">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5" />
                        Active
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-mono font-medium text-slate-200">
                      {item.execution_count}
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 text-[11px]">
                      {new Date(item.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        type="button"
                        onClick={async () => {
                          const newRole = item.role === 'admin' ? 'user' : 'admin';
                          const confirmed = window.confirm(
                            `Are you sure you want to change ${item.display_name}'s role to ${newRole.toUpperCase()}?`
                          );
                          if (!confirmed) return;
                          try {
                            const updated = await api.updateUserRole(item.id, newRole);
                            setUsers(users.map((u) => (u.id === updated.id ? updated : u)));
                          } catch (err: unknown) {
                            if (err instanceof ApiClientError) {
                              alert(`Failed to update role: ${err.message}`);
                            } else {
                              alert('Failed to update role.');
                            }
                          }
                        }}
                        className="text-xs px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded border border-slate-700 transition"
                      >
                        {item.role === 'admin' ? 'Demote' : 'Promote'}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
