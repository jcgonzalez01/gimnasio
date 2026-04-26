import { useEffect, useState } from 'react'
import { authApi } from '../services/api'
import type { AuditLogEntry } from '../types'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

export default function AuditLogPage() {
  const [entries, setEntries] = useState<AuditLogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [actionFilter, setActionFilter] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await authApi.auditLog({
        limit: 200,
        action: actionFilter || undefined,
      })
      setEntries(data)
    } catch {
      toast.error('Error cargando auditoría')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [actionFilter])

  const actionColor = (action: string) => {
    if (action.includes('delete') || action === 'refund') return 'bg-red-100 text-red-700'
    if (action === 'login' || action === 'login_failed') return 'bg-blue-100 text-blue-700'
    if (action === 'create') return 'bg-green-100 text-green-700'
    if (action === 'update') return 'bg-yellow-100 text-yellow-700'
    return 'bg-gray-100 text-gray-700'
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Auditoría</h1>
        <select
          value={actionFilter}
          onChange={e => setActionFilter(e.target.value)}
          className="px-3 py-2 border rounded-lg text-sm"
        >
          <option value="">Todas las acciones</option>
          <option value="login">Login</option>
          <option value="login_failed">Login fallido</option>
          <option value="create">Creación</option>
          <option value="update">Modificación</option>
          <option value="delete">Eliminación</option>
          <option value="refund">Reembolso</option>
          <option value="open_door">Apertura de puerta</option>
        </select>
      </div>

      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 text-left">
            <tr>
              <th className="px-4 py-3">Fecha</th>
              <th className="px-4 py-3">Usuario</th>
              <th className="px-4 py-3">Acción</th>
              <th className="px-4 py-3">Entidad</th>
              <th className="px-4 py-3">Resumen</th>
              <th className="px-4 py-3">IP</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={6} className="text-center py-8 text-gray-400">Cargando…</td></tr>
            ) : entries.length === 0 ? (
              <tr><td colSpan={6} className="text-center py-8 text-gray-400">Sin registros</td></tr>
            ) : entries.map(e => (
              <tr key={e.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                  {format(new Date(e.timestamp), 'dd/MM/yyyy HH:mm:ss')}
                </td>
                <td className="px-4 py-3">{e.username || '—'}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded text-xs ${actionColor(e.action)}`}>
                    {e.action}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-600">
                  {e.entity_type ? `${e.entity_type}#${e.entity_id || '?'}` : '—'}
                </td>
                <td className="px-4 py-3 text-gray-700">{e.summary || '—'}</td>
                <td className="px-4 py-3 text-gray-500 font-mono text-xs">{e.ip_address || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
