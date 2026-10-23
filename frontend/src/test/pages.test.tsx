import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { OverviewPage } from '../pages/OverviewPage';
import { AgentWorkspacePage } from '../pages/AgentWorkspacePage';
import { SimulationPage } from '../pages/SimulationPage';
import { DriftDetectionPage } from '../pages/DriftDetectionPage';
import { ExecutionHistoryPage } from '../pages/ExecutionHistoryPage';
import { SystemStatusPage } from '../pages/SystemStatusPage';
import { AuthProvider } from '../context/AuthContext';
import { DemoProvider } from '../context/DemoContext';
import { apiClient } from '../services/api';

describe('Page Integration and UI Tests', () => {
  beforeEach(() => {
    vi.restoreAllMocks();

    vi.spyOn(apiClient, 'getHealth').mockResolvedValue({
      status: 'ok',
      environment: 'development',
      version: '1.0.0',
    });

    vi.spyOn(apiClient, 'getReadiness').mockResolvedValue({
      status: 'ready',
      environment: 'development',
      version: '1.0.0',
      components: {
        database: { status: 'ready', latency_ms: 1.5, message: 'Connected' },
        models: { status: 'ready', latency_ms: 2.1, message: 'All models loaded' },
      },
    });

    vi.spyOn(apiClient, 'getCurrentUser').mockResolvedValue({
      id: 'synthetic_user_00',
      username: 'user00',
      display_name: 'Synthetic Twin 00',
      is_active: true,
      created_at: new Date().toISOString(),
      roles: ['user'],
      authorized_scopes: ['synthetic_user_00'],
    });

    vi.spyOn(apiClient, 'getHistory').mockResolvedValue({
      total: 1,
      limit: 10,
      offset: 0,
      items: [
        {
          id: 'hist-001',
          request_id: 'REQ-12345',
          user_id: 'synthetic_user_00',
          status: 'COMPLETED',
          user_goal: 'Analyze focus hours',
          provider: 'mock',
          model: 'champion',
          execution_mode: 'deterministic',
          execution_latency: 0.15,
          findings_count: 2,
          recommendations_count: 1,
          simulation_performed: false,
          verification_passed: true,
          error_category: null,
          findings_summary: 'Focus was 6.2 hours',
          created_at: new Date().toISOString(),
        },
      ],
    });
  });

  it('renders OverviewPage with live metrics and distinguishes liveness from readiness', async () => {
    render(
      <AuthProvider>
        <DemoProvider>
          <MemoryRouter>
            <OverviewPage />
          </MemoryRouter>
        </DemoProvider>
      </AuthProvider>
    );

    // Initial loading state can have multiple elements (e.g. text + sr-only)
    expect(screen.getAllByText(/checking backend diagnostics/i).length).toBeGreaterThan(0);

    // After resolution
    await waitFor(() => {
      expect(screen.getByText('System Overview')).toBeInTheDocument();
      expect(screen.getByText('API Service (Liveness)')).toBeInTheDocument();
      expect(screen.getByText('PostgreSQL Readiness')).toBeInTheDocument();
      expect(screen.getByText('Cognitive Model Engine')).toBeInTheDocument();
      expect(screen.getByText('REQ-12345')).toBeInTheDocument();
    });
  });

  it('renders OverviewPage error state when backend is unreachable', async () => {
    vi.spyOn(apiClient, 'getHealth').mockRejectedValue(new Error('Connection refused'));
    vi.spyOn(apiClient, 'getCurrentUser').mockRejectedValue(new Error('Offline'));

    render(
      <AuthProvider>
        <DemoProvider>
          <MemoryRouter>
            <OverviewPage />
          </MemoryRouter>
        </DemoProvider>
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Backend Connection Warning')).toBeInTheDocument();
      expect(screen.getByText(/connection refused/i)).toBeInTheDocument();
    });
  });

  it('renders AgentWorkspacePage, triggers query submission, and renders response', async () => {
    vi.spyOn(apiClient, 'runAgent').mockResolvedValue({
      request_id: 'REQ-999',
      user_id: 'synthetic_user_00',
      status: 'COMPLETED',
      execution_mode: 'deterministic',
      provider: 'mock',
      model: 'champion',
      execution_latency: 0.25,
      summary: 'Analysis completed: baseline metrics within expected bounds.',
      findings: ['Focus hours: 5.8', 'Interruption frequency: low'],
      recommendations: [{ title: 'Maintain focus blocks', category: 'Focus' }],
      verification: { is_verified: true, unsupported_claims: [], disclosed_limitations: [] },
      execution_trace_summary: [
        { tool_name: 'get_behavioral_summary', status: 'completed', duration_ms: 120 },
      ],
      disclaimer: 'Non-clinical twin simulation',
    });

    render(
      <AuthProvider>
        <DemoProvider>
          <MemoryRouter>
            <AgentWorkspacePage />
          </MemoryRouter>
        </DemoProvider>
      </AuthProvider>
    );

    expect(screen.getByText('AI Agent Workspace')).toBeInTheDocument();

    const submitBtn = screen.getByRole('button', { name: /execute agent turn/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(
        screen.getByText(/analysis completed: baseline metrics within expected bounds/i)
      ).toBeInTheDocument();
      expect(screen.getAllByText(/get_behavioral_summary/i).length).toBeGreaterThan(0);
    });
  });

  it('renders SimulationPage with parameter controls and baseline/simulated comparison', async () => {
    vi.spyOn(apiClient, 'runAgent').mockResolvedValue({
      request_id: 'REQ-SIM-1',
      user_id: 'synthetic_user_00',
      status: 'COMPLETED',
      execution_mode: 'deterministic',
      provider: 'mock',
      model: 'champion',
      execution_latency: 0.35,
      summary: 'Projected productivity score increased under scenario.',
      findings: [],
      recommendations: [],
      simulation_result: {
        task_type: 'retrospective',
        baseline_productivity: 68.2,
        simulated_productivity: 74.8,
        delta: 6.6,
        features_modified: { focus_duration_hours: 6.5 },
        out_of_distribution_warnings: [],
      },
      verification: { is_verified: true, unsupported_claims: [], disclosed_limitations: [] },
      execution_trace_summary: [],
      disclaimer: 'Non-causal simulation disclaimer',
    });

    render(
      <AuthProvider>
        <DemoProvider>
          <MemoryRouter>
            <SimulationPage />
          </MemoryRouter>
        </DemoProvider>
      </AuthProvider>
    );

    expect(screen.getByText('What-if Simulation Engine')).toBeInTheDocument();

    const runBtn = screen.getByRole('button', { name: /run model simulation/i });
    fireEvent.click(runBtn);

    await waitFor(() => {
      expect(screen.getByText(/estimated productivity impact/i)).toBeInTheDocument();
      expect(screen.getByText(/non-causal statistical disclaimer/i)).toBeInTheDocument();
    });
  });

  it('renders DriftDetectionPage and executes covariate shift test', async () => {
    vi.spyOn(apiClient, 'runAgent').mockResolvedValue({
      request_id: 'REQ-DRIFT-1',
      user_id: 'synthetic_user_00',
      status: 'COMPLETED',
      execution_mode: 'deterministic',
      provider: 'mock',
      model: 'champion',
      execution_latency: 0.45,
      summary: 'Statistical KS tests indicate no significant distribution drift.',
      findings: ['feature_focus_duration: p=0.42, no drift'],
      recommendations: [],
      verification: { is_verified: true, unsupported_claims: [], disclosed_limitations: [] },
      execution_trace_summary: [],
      disclaimer: 'Non-clinical drift test',
    });

    render(
      <AuthProvider>
        <DemoProvider>
          <MemoryRouter>
            <DriftDetectionPage />
          </MemoryRouter>
        </DemoProvider>
      </AuthProvider>
    );

    expect(screen.getByText('Behavioural Drift Detection')).toBeInTheDocument();

    const testBtn = screen.getByRole('button', { name: /re-evaluate drift hypothesis/i });
    fireEvent.click(testBtn);

    await waitFor(() => {
      expect(screen.getByText(/feature-level statistical shift diagnostics/i)).toBeInTheDocument();
      expect(screen.getByText(/statistical methodology & scientific transparency/i)).toBeInTheDocument();
    });
  });

  it('renders ExecutionHistoryPage and opens inspect modal on click', async () => {
    vi.spyOn(apiClient, 'getHistoryDetail').mockResolvedValue({
      id: 'hist-001',
      request_id: 'REQ-12345',
      user_id: 'synthetic_user_00',
      status: 'COMPLETED',
      user_goal: 'Analyze focus hours',
      provider: 'mock',
      model: 'champion',
      execution_mode: 'deterministic',
      execution_latency: 0.15,
      findings_count: 2,
      recommendations_count: 1,
      simulation_performed: false,
      verification_passed: true,
      findings_summary: 'Detailed focus hours breakdown',
      created_at: new Date().toISOString(),
      tools_called: [{ tool_name: 'get_behavioral_summary', status: 'completed', duration_ms: 45 }],
      error_message: null,
    });

    render(
      <AuthProvider>
        <DemoProvider>
          <MemoryRouter>
            <ExecutionHistoryPage />
          </MemoryRouter>
        </DemoProvider>
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Execution Audit History')).toBeInTheDocument();
      expect(screen.getByText('REQ-12345')).toBeInTheDocument();
    });

    const inspectBtn = screen.getByRole('button', { name: /inspect/i });
    fireEvent.click(inspectBtn);

    await waitFor(() => {
      expect(screen.getByText('Execution Audit Detail')).toBeInTheDocument();
      expect(screen.getByText('Detailed focus hours breakdown')).toBeInTheDocument();
    });
  });

  it('renders SystemStatusPage with detailed diagnostic subsystem probes', async () => {
    render(
      <AuthProvider>
        <DemoProvider>
          <MemoryRouter>
            <SystemStatusPage />
          </MemoryRouter>
        </DemoProvider>
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Infrastructure & System Status')).toBeInTheDocument();
      expect(screen.getByText('All Subsystems Operational')).toBeInTheDocument();
      expect(screen.getByText('FastAPI Server')).toBeInTheDocument();
      expect(screen.getByText('PostgreSQL Pool')).toBeInTheDocument();
      expect(screen.getByText('ML Models / LLM')).toBeInTheDocument();
    });
  });
});
