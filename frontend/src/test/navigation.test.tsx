import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Sidebar } from '../components/layout/Sidebar';
import { Header } from '../components/layout/Header';
import { AuthProvider } from '../context/AuthContext';
import { apiClient } from '../services/api';

describe('Navigation and Layout Unit Tests', () => {
  beforeEach(() => {
    vi.spyOn(apiClient, 'getHealth').mockResolvedValue({
      status: 'ok',
      environment: 'test',
      version: '1.0.0',
    });
    vi.spyOn(apiClient, 'getCurrentUser').mockResolvedValue({
      id: 'synthetic_user_00',
      username: 'user00',
      display_name: 'Synthetic Twin 00',
      is_active: true,
      created_at: new Date().toISOString(),
      roles: ['admin'],
      authorized_scopes: ['*'],
    });
  });

  it('renders all 8 primary navigation links in Sidebar', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Sidebar mobileOpen={false} onCloseMobile={vi.fn()} />
      </MemoryRouter>
    );

    expect(screen.getByRole('link', { name: /overview/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /behavioural insights/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /drift detection/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /recommendations/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /what-if simulation/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /ai agent workspace/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /execution history/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /system status/i })).toBeInTheDocument();
  });

  it('renders brand heading and non-causal disclaimer in Sidebar', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <Sidebar mobileOpen={false} onCloseMobile={vi.fn()} />
      </MemoryRouter>
    );

    expect(screen.getByText('Cognitive Twin')).toBeInTheDocument();
    expect(
      screen.getByText(/predictions & simulations are non-causal estimates/i)
    ).toBeInTheDocument();
  });

  it('renders Header with target user selector and persona switcher', async () => {
    render(
      <AuthProvider>
        <Header onOpenMobile={vi.fn()} />
      </AuthProvider>
    );

    expect(screen.getByLabelText(/select target user/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/select authentication persona/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/api: healthy/i)).toBeInTheDocument();
    });
  });

  it('switches persona and updates target user in Header', async () => {
    render(
      <AuthProvider>
        <Header onOpenMobile={vi.fn()} />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/api: healthy/i)).toBeInTheDocument();
    });

    const userSelect = screen.getByLabelText(/select target user/i) as HTMLSelectElement;
    fireEvent.change(userSelect, { target: { value: 'user_05' } });
    expect(userSelect.value).toBe('user_05');

    const personaSelect = screen.getByLabelText(/select authentication persona/i) as HTMLSelectElement;
    fireEvent.change(personaSelect, { target: { value: 'dev-admin-token' } });
    expect(personaSelect.value).toBe('dev-admin-token');
  });
});
