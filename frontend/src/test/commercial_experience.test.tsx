import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { LandingPage } from '../pages/public/LandingPage';
import { SignInPage } from '../pages/public/SignInPage';
import { SignUpPage } from '../pages/public/SignUpPage';
import { UserSidebar } from '../components/layout/UserSidebar';
import { AdminSidebar } from '../components/layout/AdminSidebar';
import { UserSettingsPage } from '../pages/user/UserSettingsPage';
import { AdminAnalyticsPage } from '../pages/admin/AdminAnalyticsPage';
import { AdminSecurityPage } from '../pages/admin/AdminSecurityPage';
import { AdminConfigurationPage } from '../pages/admin/AdminConfigurationPage';
import { AuthProvider } from '../context/AuthContext';

describe('Commercial Product Experience & Role Separation Tests', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders Public Landing Page with brand, tagline, and CTA links', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <LandingPage />
      </MemoryRouter>
    );

    expect(screen.getAllByText('Cognitive Twin').length).toBeGreaterThan(0);
    expect(screen.getByText(/understand your patterns/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /explore cognitive twin/i })).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: /sign in/i }).length).toBeGreaterThan(0);
    expect(screen.getByRole('link', { name: /get started/i })).toBeInTheDocument();
    expect(screen.getByText(/responsible ai & research integrity statement/i)).toBeInTheDocument();
  });

  it('renders SignInPage with credentials fields and test accounts', () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/signin']}>
          <SignInPage />
        </MemoryRouter>
      </AuthProvider>
    );

    expect(screen.getByLabelText(/email or username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /sign in/i }).length).toBeGreaterThan(0);
    expect(screen.getByRole('button', { name: /regular user/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /administrator/i })).toBeInTheDocument();
  });

  it('renders SignUpPage with name, email, password, and terms checkbox', () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/signup']}>
          <SignUpPage />
        </MemoryRouter>
      </AuthProvider>
    );

    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    expect(screen.getByRole('checkbox')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
  });

  it('UserSidebar contains only user modules, Account & Settings, and NO system infrastructure status', () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/app']}>
          <UserSidebar mobileOpen={false} onCloseMobile={vi.fn()} />
        </MemoryRouter>
      </AuthProvider>
    );

    expect(screen.getByText('My Overview')).toBeInTheDocument();
    expect(screen.getByText('Behavioural Insights')).toBeInTheDocument();
    expect(screen.getByText('Drift Detection')).toBeInTheDocument();
    expect(screen.getByText('Recommendations')).toBeInTheDocument();
    expect(screen.getByText('What-if Simulation')).toBeInTheDocument();
    expect(screen.getByText('AI Agent Workspace')).toBeInTheDocument();
    expect(screen.getByText('Execution History')).toBeInTheDocument();
    expect(screen.getByText('Account & Settings')).toBeInTheDocument();

    // Verify infrastructure diagnostics are NOT visible to regular users
    expect(screen.queryByText(/system status/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/readiness & database diagnostics/i)).not.toBeInTheDocument();
  });

  it('AdminSidebar displays all operational management and diagnostic modules', () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/admin']}>
          <AdminSidebar mobileOpen={false} onCloseMobile={vi.fn()} />
        </MemoryRouter>
      </AuthProvider>
    );

    expect(screen.getByText('Admin Overview')).toBeInTheDocument();
    expect(screen.getByText('System Health')).toBeInTheDocument();
    expect(screen.getByText('User Management')).toBeInTheDocument();
    expect(screen.getByText('Audit History')).toBeInTheDocument();
    expect(screen.getByText('Analytics & Performance')).toBeInTheDocument();
    expect(screen.getByText('Security & Access')).toBeInTheDocument();
    expect(screen.getByText('Configuration')).toBeInTheDocument();
    expect(screen.getByText('Return to User Workspace')).toBeInTheDocument();
  });

  it('renders UserSettingsPage with profile and password update forms', () => {
    render(
      <AuthProvider>
        <MemoryRouter>
          <UserSettingsPage />
        </MemoryRouter>
      </AuthProvider>
    );

    expect(screen.getByText('Account & Privacy Settings')).toBeInTheDocument();
    expect(screen.getByText('Personal Profile')).toBeInTheDocument();
    expect(screen.getByText('Security & Password')).toBeInTheDocument();
    expect(screen.getByText('Responsible AI & Data Privacy Boundaries')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /update password/i })).toBeInTheDocument();
  });

  it('renders AdminAnalyticsPage with KPI titles', () => {
    render(
      <AuthProvider>
        <MemoryRouter>
          <AdminAnalyticsPage />
        </MemoryRouter>
      </AuthProvider>
    );

    expect(screen.getByText('Model & Engine Analytics')).toBeInTheDocument();
    expect(screen.getByText('Total Inquiries')).toBeInTheDocument();
    expect(screen.getByText('Execution Success Rate')).toBeInTheDocument();
    expect(screen.getByText('Avg Execution Latency')).toBeInTheDocument();
  });

  it('renders AdminSecurityPage with security posture and audit elements', () => {
    render(
      <AuthProvider>
        <MemoryRouter>
          <AdminSecurityPage />
        </MemoryRouter>
      </AuthProvider>
    );

    expect(screen.getByText('Security & Access Governance')).toBeInTheDocument();
    expect(screen.getByText('Total Registered Accounts')).toBeInTheDocument();
    expect(screen.getByText('Privileged Administrators')).toBeInTheDocument();
    expect(screen.getByText('Active Cryptographic & Security Controls')).toBeInTheDocument();
  });

  it('renders AdminConfigurationPage with integration sections', () => {
    render(
      <AuthProvider>
        <MemoryRouter>
          <AdminConfigurationPage />
        </MemoryRouter>
      </AuthProvider>
    );

    expect(screen.getByText('System & Integration Configuration')).toBeInTheDocument();
    expect(screen.getByText('Database & Pool Settings')).toBeInTheDocument();
    expect(screen.getByText('Cognitive Model & LLM Engine')).toBeInTheDocument();
    expect(screen.getByText('Core Framework Architecture')).toBeInTheDocument();
  });
});

