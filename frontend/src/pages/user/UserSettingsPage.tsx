import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { api, ApiClientError } from '../../services/api';
import {
  User,
  Shield,
  Key,
  Database,
  Lock,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
  LogOut,
  Info,
} from 'lucide-react';

export const UserSettingsPage: React.FC = () => {
  const { userProfile, token, logout } = useAuth();

  // Password change state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (newPassword.length < 8) {
      setErrorMessage('New password must be at least 8 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setErrorMessage('New password and confirmation do not match.');
      return;
    }

    if (currentPassword === newPassword) {
      setErrorMessage('New password must be different from current password.');
      return;
    }

    setLoading(true);
    try {
      await api.changePassword(
        {
          current_password: currentPassword,
          new_password: newPassword,
        },
        token || undefined
      );

      setSuccessMessage('Password changed successfully.');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      if (err instanceof ApiClientError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Failed to change password. Please check your current password.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Account & Privacy Settings</h1>
        <p className="text-slate-400 mt-1 text-sm">
          Manage your account profile, credentials, and view research data governance policies.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Profile Details Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2.5 bg-indigo-500/10 text-indigo-400 rounded-lg">
              <User className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">Personal Profile</h2>
              <p className="text-xs text-slate-400">Authenticated user identity</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-xs font-medium text-slate-400 block mb-1">Display Name</label>
              <div className="text-sm font-medium text-white bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2.5">
                {userProfile?.display_name || userProfile?.username || 'Cognitive User'}
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-slate-400 block mb-1">Email Address</label>
              <div className="text-sm font-medium text-white bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2.5">
                {userProfile?.email || 'N/A'}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-medium text-slate-400 block mb-1">Assigned Role</label>
                <div className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  <Shield className="w-3.5 h-3.5" />
                  <span className="capitalize">{userProfile?.role || 'user'}</span>
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-slate-400 block mb-1">Account Status</label>
                <div className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Active</span>
                </div>
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-slate-400 block mb-1">Account ID</label>
              <div className="text-xs font-mono text-slate-500 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 select-all">
                {userProfile?.id || '—'}
              </div>
            </div>
          </div>
        </div>

        {/* Change Password Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
          <div className="flex items-center space-x-3 mb-6">
            <div className="p-2.5 bg-cyan-500/10 text-cyan-400 rounded-lg">
              <Key className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">Security & Password</h2>
              <p className="text-xs text-slate-400">Update your account password</p>
            </div>
          </div>

          <form onSubmit={handlePasswordChange} className="space-y-4">
            {successMessage && (
              <div className="flex items-center space-x-2 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400 text-sm">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>{successMessage}</span>
              </div>
            )}

            {errorMessage && (
              <div className="flex items-center space-x-2 p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-400 text-sm">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            <div>
              <label className="text-xs font-medium text-slate-400 block mb-1">Current Password</label>
              <div className="relative">
                <input
                  type={showCurrent ? 'text' : 'password'}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                  placeholder="Enter current password"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowCurrent(!showCurrent)}
                  className="absolute right-3 top-2.5 text-slate-500 hover:text-slate-300"
                >
                  {showCurrent ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-slate-400 block mb-1">New Password (min 8 chars)</label>
              <div className="relative">
                <input
                  type={showNew ? 'text' : 'password'}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  placeholder="Enter new password"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowNew(!showNew)}
                  className="absolute right-3 top-2.5 text-slate-500 hover:text-slate-300"
                >
                  {showNew ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-slate-400 block mb-1">Confirm New Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                placeholder="Confirm new password"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white rounded-lg font-medium text-sm transition-colors shadow-sm mt-2 flex items-center justify-center space-x-2"
            >
              <Lock className="w-4 h-4" />
              <span>{loading ? 'Updating Password...' : 'Update Password'}</span>
            </button>
          </form>
        </div>
      </div>

      {/* Research & Data Governance Notice */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2.5 bg-amber-500/10 text-amber-400 rounded-lg">
            <Info className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">Responsible AI & Data Privacy Boundaries</h2>
            <p className="text-xs text-slate-400">Understanding data boundaries and scientific limitations</p>
          </div>
        </div>

        <div className="space-y-3 text-xs text-slate-300 leading-relaxed">
          <div className="p-3.5 bg-slate-950/80 border border-slate-800/80 rounded-lg">
            <span className="font-semibold text-white block mb-1">Synthetic Data Benchmark Notice:</span>
            Cognitive Twin operates on calibrated synthetic behavioral telemetry designed for statistical algorithm validation. Metrics and interventions demonstrate pipeline capability and statistical consistency rather than validated human clinical diagnoses.
          </div>
          <div className="p-3.5 bg-slate-950/80 border border-slate-800/80 rounded-lg">
            <span className="font-semibold text-white block mb-1">Strict Isolation & Non-Causal Estimation:</span>
            Your account is cryptographically isolated on the backend. All agent queries and audit records are bound strictly to your user identifier. What-if simulation differences represent hypothetical estimates under modeled parameters and do not constitute guaranteed causal outcomes.
          </div>
        </div>

        <div className="mt-6 pt-6 border-t border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2 text-xs text-slate-400">
            <Database className="w-4 h-4 text-slate-500" />
            <span>Authenticated Data Partition: <strong className="text-white">{userProfile?.id}</strong></span>
          </div>

          <button
            onClick={logout}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-rose-950/40 text-slate-300 hover:text-rose-400 border border-slate-700 hover:border-rose-900/50 rounded-lg text-xs font-medium transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    </div>
  );
};
