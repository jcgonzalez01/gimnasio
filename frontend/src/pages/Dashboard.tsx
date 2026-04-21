import { useEffect, useState } from 'react'
import { posApi } from '../services/api'
import type { DashboardStats, AccessLog } from '../types'
import { accessApi } from '../services/api'
import {
  Users, TrendingUp, DollarSign, AlertTriangle,
  UserCheck, LogIn, Calendar, Wifi
} from 'lucide-react'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ReactNode
  color: string
  alert?: boolean
}

function StatCard({ title, value, subtitle, icon, color, alert }: StatCardProps) {
  return (
    <div className={`card flex items-center gap-4 ${alert ? 'border-l-4 border-l-orange-400' : ''}`}>
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${color}`}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-500">{title}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        {subtitle && <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [recentLogs, setRecentLogs] = useState<AccessLog[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      posApi.getDashboard(),
      accessApi.getLogs({ limit: 10 }),
    ]).then(([statsRes, logsRes]) => {
      setStats(statsRes.data)
      setRecentLogs(logsRes.data)
    }).finally(() => setLoading(false))
  }, [])

  const fmt = (n: number) => new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(n)

  if (loading) return (
    <div className="p-8 flex items-center justify-center h-full">
      <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full" />
    </div>
  )

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 text-sm mt-1">
          {format(new Date(), "EEEE d 'de' MMMM, yyyy", { locale: es })}
        </p>
      </div>

      {stats && (
        <>
          {/* Stats grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Total Miembros"
              value={stats.total_members}
              icon={<Users size={20} className="text-blue-600" />}
              color="bg-blue-50"
              subtitle={`${stats.active_members} activos`}
            />
            <StatCard
              title="Entradas Hoy"
              value={stats.entries_today}
              icon={<LogIn size={20} className="text-green-600" />}
              color="bg-green-50"
              subtitle={`${stats.entries_this_month} este mes`}
            />
            <StatCard
              title="Ventas Hoy"
              value={fmt(stats.sales_today)}
              icon={<DollarSign size={20} className="text-purple-600" />}
              color="bg-purple-50"
              subtitle={`${fmt(stats.sales_this_month)} este mes`}
            />
            <StatCard
              title="Por Vencer"
              value={stats.memberships_expiring_soon}
              icon={<Calendar size={20} className="text-orange-500" />}
              color="bg-orange-50"
              subtitle="membresías (7 días)"
              alert={stats.memberships_expiring_soon > 0}
            />
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Miembros Activos"
              value={stats.active_members}
              icon={<UserCheck size={20} className="text-teal-600" />}
              color="bg-teal-50"
            />
            <StatCard
              title="Membresías Vencidas"
              value={stats.expired_members}
              icon={<AlertTriangle size={20} className="text-red-500" />}
              color="bg-red-50"
              alert={stats.expired_members > 0}
            />
            <StatCard
              title="Stock Bajo"
              value={stats.low_stock_products}
              icon={<TrendingUp size={20} className="text-yellow-600" />}
              color="bg-yellow-50"
              alert={stats.low_stock_products > 0}
              subtitle="productos a reponer"
            />
            <StatCard
              title="Ventas del Mes"
              value={fmt(stats.sales_this_month)}
              icon={<DollarSign size={20} className="text-indigo-600" />}
              color="bg-indigo-50"
            />
          </div>
        </>
      )}

      {/* Últimos accesos */}
      <div className="card">
        <h2 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <Wifi size={16} className="text-blue-500" />
          Últimos Accesos
        </h2>
        {recentLogs.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">Sin registros de acceso</p>
        ) : (
          <div className="space-y-2">
            {recentLogs.map(log => (
              <div key={log.id}
                className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
                <div className={`w-2 h-2 rounded-full shrink-0 ${
                  log.result === 'granted' ? 'bg-green-500' : 'bg-red-500'
                }`} />
                <div className="flex-1 min-w-0">
                  <span className="font-medium text-sm">
                    {log.member_name || 'Desconocido'}
                  </span>
                  {log.device_name && (
                    <span className="text-gray-400 text-xs ml-2">· {log.device_name}</span>
                  )}
                </div>
                <div className="text-right shrink-0">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                    log.result === 'granted'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-red-100 text-red-700'
                  }`}>
                    {log.direction === 'in' ? '↑ Entrada' : '↓ Salida'}
                  </span>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {format(new Date(log.timestamp), 'HH:mm:ss')}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
