import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { DemoProvider } from './context/DemoContext';
import { ProtectedRoute, AdminRoute, PublicOnlyRoute } from './components/auth/RouteGuards';

// Public Experience Pages
import { LandingPage } from './pages/public/LandingPage';
import { SignInPage } from './pages/public/SignInPage';
import { SignUpPage } from './pages/public/SignUpPage';
import { PrivacyPage } from './pages/public/PrivacyPage';
import { TermsPage } from './pages/public/TermsPage';

// Regular User Experience
import { UserLayout } from './components/layout/UserLayout';
import { UserOverviewPage } from './pages/user/UserOverviewPage';
import { UserSettingsPage } from './pages/user/UserSettingsPage';
import { BehaviouralInsightsPage } from './pages/BehaviouralInsightsPage';
import { DriftDetectionPage } from './pages/DriftDetectionPage';
import { RecommendationsPage } from './pages/RecommendationsPage';
import { SimulationPage } from './pages/SimulationPage';
import { AgentWorkspacePage } from './pages/AgentWorkspacePage';
import { ExecutionHistoryPage } from './pages/ExecutionHistoryPage';

// Administrator Experience
import { AdminLayout } from './components/layout/AdminLayout';
import { AdminOverviewPage } from './pages/admin/AdminOverviewPage';
import { AdminHealthPage } from './pages/admin/AdminHealthPage';
import { AdminUsersPage } from './pages/admin/AdminUsersPage';
import { AdminAuditPage } from './pages/admin/AdminAuditPage';
import { AdminAnalyticsPage } from './pages/admin/AdminAnalyticsPage';
import { AdminSecurityPage } from './pages/admin/AdminSecurityPage';
import { AdminConfigurationPage } from './pages/admin/AdminConfigurationPage';

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <DemoProvider>
        <BrowserRouter>
          <Routes>
          {/* Public Experience */}
          <Route path="/" element={<LandingPage />} />
          <Route
            path="/signin"
            element={
              <PublicOnlyRoute>
                <SignInPage />
              </PublicOnlyRoute>
            }
          />
          <Route
            path="/signup"
            element={
              <PublicOnlyRoute>
                <SignUpPage />
              </PublicOnlyRoute>
            }
          />
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route path="/terms" element={<TermsPage />} />

          {/* Regular User Experience (/app/*) */}
          <Route
            path="/app"
            element={
              <ProtectedRoute>
                <UserLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<UserOverviewPage />} />
            <Route path="overview" element={<UserOverviewPage />} />
            <Route path="insights" element={<BehaviouralInsightsPage />} />
            <Route path="drift" element={<DriftDetectionPage />} />
            <Route path="recommendations" element={<RecommendationsPage />} />
            <Route path="simulation" element={<SimulationPage />} />
            <Route path="simulations" element={<SimulationPage />} />
            <Route path="agent" element={<AgentWorkspacePage />} />
            <Route path="history" element={<ExecutionHistoryPage />} />
            <Route path="settings" element={<UserSettingsPage />} />
          </Route>

          {/* Administrator Experience (/admin/*) */}
          <Route
            path="/admin"
            element={
              <AdminRoute>
                <AdminLayout />
              </AdminRoute>
            }
          >
            <Route index element={<AdminOverviewPage />} />
            <Route path="overview" element={<AdminOverviewPage />} />
            <Route path="health" element={<AdminHealthPage />} />
            <Route path="system-health" element={<AdminHealthPage />} />
            <Route path="users" element={<AdminUsersPage />} />
            <Route path="audit" element={<AdminAuditPage />} />
            <Route path="executions" element={<AdminAuditPage />} />
            <Route path="analytics" element={<AdminAnalyticsPage />} />
            <Route path="security" element={<AdminSecurityPage />} />
            <Route path="configuration" element={<AdminConfigurationPage />} />
          </Route>

          {/* Compatibility Redirects */}
          <Route path="/status" element={<Navigate to="/admin/health" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      </DemoProvider>
    </AuthProvider>
  );
};

export default App;
