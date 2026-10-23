/**
 * API Type Definitions matching FastAPI Pydantic Models
 */

export interface HealthResponse {
  status: 'ok' | 'degraded' | string;
  environment: string;
  version: string;
}

export interface ReadinessComponent {
  status: 'ready' | 'unreachable' | 'degraded' | string;
  latency_ms?: number | null;
  message?: string | null;
}

export interface ReadinessResponse {
  status: 'ready' | 'unready' | string;
  environment: string;
  version: string;
  components: Record<string, ReadinessComponent>;
}

export interface UserProfile {
  id: string;
  username: string;
  display_name: string;
  email?: string | null;
  role?: string | null;
  is_active: boolean;
  created_at: string;
  roles: string[];
  authorized_scopes: string[];
}

export interface AgentRunRequest {
  goal: string;
  target_user_id?: string;
  simulation_params?: Record<string, number | string | boolean>;
  constraints?: string[];
  request_id?: string;
}

export interface RecommendationItem {
  category?: string;
  priority_score?: number;
  title?: string;
  rationale?: string;
  action?: string;
  evidence?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface SimulationResult {
  task_type?: string;
  baseline_productivity?: number;
  simulated_productivity?: number;
  delta?: number;
  features_modified?: Record<string, unknown>;
  out_of_distribution_warnings?: string[];
  non_causal_disclaimer?: string;
  [key: string]: unknown;
}

export interface VerificationData {
  is_verified: boolean;
  unsupported_claims: string[];
  disclosed_limitations: string[];
  missing_evidence?: string[];
}

export interface ExecutionTraceStep {
  step?: string;
  tool_name?: string;
  tool?: string;
  status: string;
  duration_ms?: number;
  latency?: number;
  timestamp?: number;
  [key: string]: unknown;
}

export interface AgentRunResponse {
  request_id: string;
  user_id: string;
  status: 'COMPLETED' | 'PARTIAL' | 'REJECTED' | 'FAILED' | string;
  execution_mode: string;
  provider: string;
  model: string;
  execution_latency: number;
  summary: string;
  findings: string[];
  recommendations: RecommendationItem[];
  simulation_result?: SimulationResult | null;
  verification: VerificationData;
  execution_trace_summary: ExecutionTraceStep[];
  disclaimer: string;
  error?: {
    category: string;
    message: string;
    retryable?: boolean;
  } | null;
}

export interface HistoryItem {
  id: string;
  request_id: string;
  user_id: string;
  status: string;
  user_goal: string;
  provider: string;
  model: string;
  execution_mode: string;
  execution_latency: number;
  findings_count: number;
  recommendations_count: number;
  simulation_performed: boolean;
  verification_passed: boolean;
  error_category?: string | null;
  findings_summary?: string | null;
  created_at: string;
}

export interface HistoryListResponse {
  total: number;
  limit: number;
  offset: number;
  items: HistoryItem[];
}

export interface HistoryDetailResponse extends HistoryItem {
  tools_called: Array<{
    tool_name: string;
    status: string;
    duration_ms?: number;
  }>;
  error_message?: string | null;
}

export interface ApiErrorDetail {
  error_code: string;
  message: string;
  request_id?: string | null;
  timestamp: string;
  details?: Record<string, unknown> | null;
}

// --- Authentication Types ---

export interface AuthUser {
  id: string;
  username: string;
  display_name: string;
  email?: string | null;
  role: 'user' | 'admin' | string;
  created_at: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name?: string;
  username?: string;
  display_name?: string;
}

export interface LoginRequest {
  email_or_username: string;
  password: string;
}

export interface AuthResponse {
  token: string;
  token_type: string;
  expires_in_hours: number;
  user: UserProfile;
}

// --- Admin Experience Types ---

export interface AdminOverviewMetrics {
  total_users: number;
  active_users: number;
  total_executions: number;
  completed_executions: number;
  failed_executions: number;
  database_status: string;
  database_latency_ms?: number | null;
  ml_models_status: string;
  recent_executions: HistoryItem[];
}

export interface AdminUserItem {
  id: string;
  username: string;
  display_name: string;
  email?: string | null;
  role: string;
  is_active: boolean;
  execution_count: number;
  created_at: string;
  updated_at?: string;
}

export interface AdminUserListResponse {
  total: number;
  limit: number;
  offset: number;
  items: AdminUserItem[];
}

export interface AdminAuditItem extends HistoryItem {
  error_message?: string | null;
}

export interface AdminAuditListResponse {
  total: number;
  limit: number;
  offset: number;
  items: AdminAuditItem[];
}

export interface AdminSystemDiagnostics {
  status: string;
  environment: string;
  version: string;
  database: {
    status: string;
    dialect: string;
    database_name: string;
    pool_size?: number;
    checked_in?: number;
    checked_out?: number;
    overflow?: number;
    latency_ms?: number | null;
  };
  cognitive_engine: {
    status: string;
    default_mode: string;
    gemini_key_configured: boolean;
    gemini_model_name: string;
  };
}

export interface AdminAnalyticsResponse {
  total_executions: number;
  completed_executions: number;
  failed_executions: number;
  success_rate_percent: number;
  avg_latency_ms: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  provider_distribution: Record<string, number>;
  tool_usage: Record<string, number>;
  execution_timeline: Array<{ date: string; executions: number }>;
  benchmark_baseline_productivity: number;
  benchmark_baseline_focus_hours: number;
}

export interface AdminSecurityResponse {
  total_registered_users: number;
  admin_accounts_count: number;
  regular_accounts_count: number;
  active_sessions_count: number;
  security_posture: Record<string, string>;
  recent_access_events: Array<{
    event_type: string;
    actor: string;
    role: string;
    status: string;
    timestamp?: string | null;
    description: string;
  }>;
}

export interface AdminConfigurationResponse {
  app_name: string;
  app_env: string;
  app_version: string;
  database: Record<string, any>;
  llm: Record<string, any>;
  frameworks: Record<string, any>;
  security_policies: Record<string, any>;
  database_migrations: Record<string, any>;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

