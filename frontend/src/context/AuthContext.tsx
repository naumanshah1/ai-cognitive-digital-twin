/**
 * Authentication and Persona Context Provider
 * Enforces authenticated identity integrity and role-based access state.
 */

import React, { createContext, useContext, useEffect, useState, useMemo } from 'react'
import { api } from '../services/api'
import {
  clearStoredAuth,
  getStoredTargetUser,
  getStoredToken,
  setStoredTargetUser,
  setStoredToken,
} from '../services/auth'
import type { UserProfile } from '../types/api'

interface AuthContextType {
  token: string | null
  user: UserProfile | null
  userProfile: UserProfile | null
  role: string | null
  isAuthenticated: boolean
  isAdmin: boolean
  loadingUser: boolean
  userError: string | null
  targetUserId: string
  setTargetUserId: (userId: string) => void
  login: (token: string, user?: UserProfile) => Promise<void>
  logout: () => void
  refreshProfile: () => Promise<void>
  switchPersona: (newToken: string) => void
  setManualToken: (newToken: string) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [token, setTokenState] = useState<string | null>(getStoredToken())
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null)
  const [loadingUser, setLoadingUser] = useState<boolean>(true)
  const [userError, setUserError] = useState<string | null>(null)
  const [adminTargetUserId, setAdminTargetUserId] = useState<string | null>(
    getStoredTargetUser()
  )

  const role = useMemo(() => {
    if (!userProfile) return null
    if (userProfile.role) return userProfile.role
    if (userProfile.roles && userProfile.roles.includes('admin')) return 'admin'
    return 'user'
  }, [userProfile])

  const isAdmin = role === 'admin'
  const isAuthenticated = Boolean(token && userProfile)

  // Identity consistency: For non-admins, targetUserId is ALWAYS strictly locked to authenticated user.id.
  // Only administrators can switch targetUserId to inspect synthetic profiles.
  const targetUserId = useMemo(() => {
    if (!userProfile) return ''
    if (isAdmin && adminTargetUserId) {
      return adminTargetUserId
    }
    return userProfile.id
  }, [userProfile, isAdmin, adminTargetUserId])

  const setTargetUserId = (newUserId: string) => {
    if (isAdmin) {
      setAdminTargetUserId(newUserId)
      setStoredTargetUser(newUserId)
    } else {
      // Regular users cannot switch target users; keep locked to own identity
      if (userProfile) {
        setAdminTargetUserId(userProfile.id)
      }
    }
  }

  const login = async (newToken: string, user?: UserProfile) => {
    setTokenState(newToken)
    setStoredToken(newToken)
    if (user) {
      setUserProfile(user)
      setLoadingUser(false)
    } else {
      await refreshProfileWithToken(newToken)
    }
  }

  const logout = () => {
    clearStoredAuth()
    setTokenState(null)
    setUserProfile(null)
    setAdminTargetUserId(null)
    setUserError(null)
  }

  const switchPersona = (newToken: string) => {
    login(newToken)
  }

  const setManualToken = (newToken: string) => {
    login(newToken)
  }

  const refreshProfileWithToken = async (activeToken: string | null) => {
    if (!activeToken) {
      setUserProfile(null)
      setLoadingUser(false)
      return
    }

    setLoadingUser(true)
    setUserError(null)
    try {
      const profile = await api.getCurrentUser(activeToken)
      setUserProfile(profile)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Authentication failed'
      setUserError(msg)
      setUserProfile(null)
    } finally {
      setLoadingUser(false)
    }
  }

  const refreshProfile = async () => {
    await refreshProfileWithToken(token)
  }

  useEffect(() => {
    refreshProfileWithToken(token)
  }, [token])

  return (
    <AuthContext.Provider
      value={{
        token,
        user: userProfile,
        userProfile,
        role,
        isAuthenticated,
        isAdmin,
        loadingUser,
        userError,
        targetUserId,
        setTargetUserId,
        login,
        logout,
        refreshProfile,
        switchPersona,
        setManualToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
