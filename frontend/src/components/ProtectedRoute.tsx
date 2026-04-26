import { Navigate, useLocation } from 'react-router-dom'
import { ReactNode } from 'react'
import { useAuth } from '../context/AuthContext'
import type { UserRole } from '../types'

interface Props {
  children: ReactNode
  roles?: UserRole[]   // Si se especifica, requiere uno de estos roles (admin siempre pasa)
}

export default function ProtectedRoute({ children, roles }: Props) {
  const { user, loading, hasRole } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-400">Cargando…</div>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  if (roles && roles.length > 0 && !hasRole(...roles)) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <div className="text-center max-w-sm">
          <div className="text-4xl mb-3">🔒</div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Acceso restringido</h2>
          <p className="text-gray-500 text-sm">
            No tienes permisos para acceder a esta sección.
          </p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
