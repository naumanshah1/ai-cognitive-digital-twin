/**
 * Centralized typed HTTP API client for AI Cognitive Digital Twin backend.
 */

import type {
  AdminAnalyticsResponse,
  AdminAuditListResponse,
  AdminConfigurationResponse,
  AdminOverviewMetrics,
  AdminSecurityResponse,
  AdminSystemDiagnostics,
  AdminUserItem,
  AdminUserListResponse,
  AgentRunRequest,
  AgentRunResponse,
  ApiErrorDetail,
  AuthResponse,
  ChangePasswordRequest,
  HealthResponse,
  HistoryDetailResponse,
  HistoryListResponse,
  LoginRequest,
  ReadinessResponse,
  RegisterRequest,
  UserProfile,
} from '../types/api'
import { getStoredToken } from './auth'

export class ApiClientError extends Error {
  public status: number
  public errorCode: string
  public details?: Record<string, unknown> | null

  constructor(status: number, message: string, errorCode: string = 'API_ERROR', details?: Record<string, unknown> | null) {
    super(message)
    this.name = 'ApiClientError'
    this.status = status
    this.errorCode = errorCode
    this.details = details
  }
}

export class ApiClient {
  private baseUrl: string

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000')
    // Remove trailing slash
    if (this.baseUrl.endsWith('/')) {
      this.baseUrl = this.baseUrl.slice(0, -1)
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    customToken?: string
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const token = customToken !== undefined ? customToken : getStoredToken()

    const headers: Record<string, string> = {
      Accept: 'application/json',
      ...(options.headers as Record<string, string>),
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    if (options.body && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json'
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      })

      // Parse JSON payload safely
      let data: unknown
      const contentType = response.headers.get('content-type')
      if (contentType && contentType.includes('application/json')) {
        data = await response.json()
      } else {
        const text = await response.text()
        data = { message: text }
      }

      if (!response.ok) {
        const errorData = data as Partial<ApiErrorDetail>
        const message =
          errorData.message || `Request failed with HTTP status ${response.status}`
        const code = errorData.error_code || `HTTP_${response.status}`
        throw new ApiClientError(response.status, message, code, errorData.details)
      }

      return data as T
    } catch (err) {
      if (err instanceof ApiClientError) {
        throw err
      }
      // Network or connection error (e.g. backend offline)
      throw new ApiClientError(
        0,
        `Network or connection failure: Unable to communicate with backend at ${this.baseUrl}. Please verify the service is running.`,
        'NETWORK_ERROR'
      )
    }
  }

  // --- Health Endpoints ---

  public async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health')
  }

  public async getReadiness(): Promise<ReadinessResponse> {
    return this.request<ReadinessResponse>('/health/ready')
  }

  // --- Authentication Endpoints ---

  public async register(payload: RegisterRequest): Promise<AuthResponse> {
    return this.request<AuthResponse>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }

  public async login(payload: LoginRequest): Promise<AuthResponse> {
    return this.request<AuthResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  }

  public async logout(token?: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(
      '/api/v1/auth/logout',
      {
        method: 'POST',
      },
      token
    )
  }

  public async getAuthMe(token?: string): Promise<UserProfile> {
    return this.request<UserProfile>('/api/v1/auth/me', {}, token)
  }

  public async changePassword(payload: ChangePasswordRequest, token?: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(
      '/api/v1/auth/change-password',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      token
    )
  }

  // --- Admin Operational Endpoints ---

  public async getAdminOverview(token?: string): Promise<AdminOverviewMetrics> {
    return this.request<AdminOverviewMetrics>('/api/v1/admin/overview', {}, token)
  }

  public async getAdminUsers(limit: number = 20, offset: number = 0, token?: string): Promise<AdminUserListResponse> {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
    return this.request<AdminUserListResponse>(`/api/v1/admin/users?${params.toString()}`, {}, token)
  }

  public async getAdminAudit(limit: number = 20, offset: number = 0, token?: string): Promise<AdminAuditListResponse> {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
    return this.request<AdminAuditListResponse>(`/api/v1/admin/audit?${params.toString()}`, {}, token)
  }

  public async getAdminSystem(token?: string): Promise<AdminSystemDiagnostics> {
    return this.request<AdminSystemDiagnostics>('/api/v1/admin/system', {}, token)
  }

  public async getAdminAnalytics(token?: string): Promise<AdminAnalyticsResponse> {
    return this.request<AdminAnalyticsResponse>('/api/v1/admin/analytics', {}, token)
  }

  public async getAdminSecurity(token?: string): Promise<AdminSecurityResponse> {
    return this.request<AdminSecurityResponse>('/api/v1/admin/security', {}, token)
  }

  public async getAdminConfiguration(token?: string): Promise<AdminConfigurationResponse> {
    return this.request<AdminConfigurationResponse>('/api/v1/admin/configuration', {}, token)
  }

  public async updateUserRole(userId: string, role: string, token?: string): Promise<AdminUserItem> {
    return this.request<AdminUserItem>(
      `/api/v1/admin/users/${encodeURIComponent(userId)}/role`,
      {
        method: 'POST',
        body: JSON.stringify({ role }),
      },
      token
    )
  }

  // --- User Profile Endpoints ---

  public async getCurrentUser(token?: string): Promise<UserProfile> {
    return this.request<UserProfile>('/api/v1/users/me', {}, token)
  }

  public async getUserById(userId: string): Promise<UserProfile> {
    return this.request<UserProfile>(`/api/v1/users/${encodeURIComponent(userId)}`)
  }

  // --- Agent Endpoints ---

  public async runAgent(payload: AgentRunRequest, token?: string): Promise<AgentRunResponse> {
    return this.request<AgentRunResponse>(
      '/api/v1/agent/run',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      token
    )
  }

  public getBaseUrl(): string {
    return this.baseUrl
  }

  // --- History Endpoints ---

  public async getHistory(limit: number = 20, offset: number = 0, token?: string): Promise<HistoryListResponse> {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    })
    return this.request<HistoryListResponse>(`/api/v1/agent/history?${params.toString()}`, {}, token)
  }

  public async getExecutionHistory(
    opts: { limit?: number; offset?: number; page?: number; status?: string } = {},
    token?: string
  ): Promise<HistoryListResponse> {
    const limit = opts.limit ?? 20
    const offset = opts.offset ?? (opts.page && opts.page > 1 ? (opts.page - 1) * limit : 0)
    return this.getHistory(limit, offset, token)
  }

  public async getHistoryDetail(requestId: string, token?: string): Promise<HistoryDetailResponse> {
    return this.request<HistoryDetailResponse>(
      `/api/v1/agent/history/${encodeURIComponent(requestId)}`,
      {},
      token
    )
  }

  public async getExecutionDetail(requestId: string, token?: string): Promise<HistoryDetailResponse> {
    return this.getHistoryDetail(requestId, token)
  }
}

export const api = new ApiClient()
export const apiClient = api

