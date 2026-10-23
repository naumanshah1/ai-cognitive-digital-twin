import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ApiClient, ApiClientError } from '../services/api';

describe('ApiClient Unit Tests', () => {
  let client: ApiClient;
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    client = new ApiClient('http://test-server:8000');
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it('constructs correct API URL and headers', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({ status: 'ok', environment: 'test', version: '1.0.0' }),
    });
    globalThis.fetch = mockFetch;

    const result = await client.getHealth();

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const [url, options] = mockFetch.mock.calls[0];
    expect(url).toBe('http://test-server:8000/health');
    expect(options.headers).toMatchObject({
      Accept: 'application/json',
    });
    expect(result.status).toBe('ok');
  });

  it('injects Authorization Bearer token header when provided', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({ id: 'user_00', username: 'user00', display_name: 'User', is_active: true, created_at: '', roles: ['user'], authorized_scopes: [] }),
    });
    globalThis.fetch = mockFetch;

    await client.getCurrentUser('secret-token-xyz');

    const [, options] = mockFetch.mock.calls[0];
    expect(options.headers['Authorization']).toBe('Bearer secret-token-xyz');
  });

  it('handles HTTP 401 Unauthorized with ApiClientError', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({ error_code: 'UNAUTHORIZED', message: 'Token invalid or expired' }),
    });

    await expect(client.getCurrentUser('bad-token')).rejects.toThrow(ApiClientError);
    try {
      await client.getCurrentUser('bad-token');
    } catch (err: unknown) {
      const apiErr = err as ApiClientError;
      expect(apiErr.status).toBe(401);
      expect(apiErr.errorCode).toBe('UNAUTHORIZED');
      expect(apiErr.message).toContain('Token invalid or expired');
    }
  });

  it('handles HTTP 403 Forbidden cross-user access attempts', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({ error_code: 'FORBIDDEN', message: 'Principal not authorized for target user' }),
    });

    await expect(client.runAgent({ goal: 'Test', target_user_id: 'user_99' })).rejects.toThrow(ApiClientError);
    try {
      await client.runAgent({ goal: 'Test', target_user_id: 'user_99' });
    } catch (err: unknown) {
      const apiErr = err as ApiClientError;
      expect(apiErr.status).toBe(403);
      expect(apiErr.errorCode).toBe('FORBIDDEN');
    }
  });

  it('handles HTTP 422 Unprocessable Entity validation errors', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({ error_code: 'VALIDATION_ERROR', message: 'goal too short', details: { loc: ['body', 'goal'] } }),
    });

    try {
      await client.runAgent({ goal: 'hi' });
      expect.fail('Should have thrown ApiClientError');
    } catch (err: unknown) {
      const apiErr = err as ApiClientError;
      expect(apiErr.status).toBe(422);
      expect(apiErr.message).toBe('goal too short');
      expect(apiErr.details).toBeDefined();
    }
  });

  it('handles HTTP 429 Rate Limiting with appropriate error code', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 429,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({ error_code: 'RATE_LIMIT_EXCEEDED', message: 'Rate limit of 60 req/min exceeded' }),
    });

    try {
      await client.getHealth();
      expect.fail('Should have thrown ApiClientError');
    } catch (err: unknown) {
      const apiErr = err as ApiClientError;
      expect(apiErr.status).toBe(429);
      expect(apiErr.errorCode).toBe('RATE_LIMIT_EXCEEDED');
    }
  });

  it('handles HTTP 500 and 503 Internal / Service Unavailable failures', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: async () => ({ error_code: 'SERVICE_UNAVAILABLE', message: 'Database pool connection timed out' }),
    });

    try {
      await client.getReadiness();
      expect.fail('Should have thrown ApiClientError');
    } catch (err: unknown) {
      const apiErr = err as ApiClientError;
      expect(apiErr.status).toBe(503);
      expect(apiErr.errorCode).toBe('SERVICE_UNAVAILABLE');
    }
  });

  it('handles network connection failures when backend is offline (status 0)', async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));

    try {
      await client.getHealth();
      expect.fail('Should have thrown ApiClientError');
    } catch (err: unknown) {
      const apiErr = err as ApiClientError;
      expect(apiErr.status).toBe(0);
      expect(apiErr.errorCode).toBe('NETWORK_ERROR');
      expect(apiErr.message).toContain('Network or connection failure');
    }
  });
});
