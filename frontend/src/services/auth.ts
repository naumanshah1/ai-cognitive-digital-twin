/**
 * Client authentication and persona state management.
 * Provides session-scoped JWT persistence, authenticated identity tracking,
 * and optional development persona helpers for admin simulation.
 */

const TOKEN_KEY = 'ai_twin_auth_token';
const TARGET_USER_KEY = 'ai_twin_target_user';

export interface DevPersona {
  label: string;
  token: string;
  role: string;
  userId: string;
}

export const DEV_PERSONAS: DevPersona[] = [
  { label: 'Synthetic User 00', token: 'dev-synthetic-00', role: 'user', userId: 'synthetic_user_00' },
  { label: 'Synthetic User 01', token: 'dev-synthetic-01', role: 'user', userId: 'synthetic_user_01' },
  { label: 'Admin Researcher', token: 'dev-admin-token', role: 'admin', userId: 'admin_lead' },
];

/**
 * Returns stored JWT session token, or null if unauthenticated.
 */
export function getStoredToken(): string | null {
  try {
    const token = sessionStorage.getItem(TOKEN_KEY);
    if (token) return token;
    // In unit test environment, provide fallback mock token for isolated page tests
    if (import.meta.env.MODE === 'test') {
      return 'dev-synthetic-00';
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * Persists session token.
 */
export function setStoredToken(token: string): void {
  try {
    sessionStorage.setItem(TOKEN_KEY, token);
  } catch {
    // Ignore storage errors in restricted contexts
  }
}

/**
 * Returns target user id if explicitly set, or empty string.
 */
export function getStoredTargetUser(): string | null {
  try {
    return sessionStorage.getItem(TARGET_USER_KEY);
  } catch {
    return null;
  }
}

/**
 * Persists target user id for administrative inspection.
 */
export function setStoredTargetUser(userId: string): void {
  try {
    sessionStorage.setItem(TARGET_USER_KEY, userId);
  } catch {
    // Ignore
  }
}

/**
 * Clears all authentication and target context upon sign out.
 */
export function clearStoredAuth(): void {
  try {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(TARGET_USER_KEY);
  } catch {
    // Ignore
  }
}

