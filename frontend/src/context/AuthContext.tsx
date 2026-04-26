import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { authApi, tokenStorage } from '../services/api'
import type { AuthUser, UserRole } from '../types'

interface AuthCtx {
  user: AuthUser | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  refresh: () => Promise<void>
  hasRole: (...roles: UserRole[]) => boolean
}

const AuthContext = createContext<AuthCtx | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  const refresh = async () => {
    if (!tokenStorage.get()) {
      setUser(null)
      return
    }
    try {
      const { data } = await authApi.me()
      setUser(data)
    } catch {
      tokenStorage.clear()
      setUser(null)
    }
  }

  useEffect(() => {
    refresh().finally(() => setLoading(false))
  }, [])

  const login = async (username: string, password: string) => {
    const { data } = await authApi.login(username, password)
    tokenStorage.set(data.access_token)
    setUser(data.user)
  }

  const logout = () => {
    tokenStorage.clear()
    setUser(null)
    window.location.href = '/login'
  }

  const hasRole = (...roles: UserRole[]) => {
    if (!user) return false
    if (user.role === 'admin') return true
    return roles.includes(user.role)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refresh, hasRole }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
