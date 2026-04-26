import { useEffect, useState } from 'react'
import { posApi } from '../services/api'
import type { DashboardStats, AccessLog } from '../types'
import { accessApi } from '../services/api'
import {
  Users, TrendingUp, DollarSign, AlertTriangle,
  UserCheck, LogIn, Calendar, Wifi, KeyRound
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
  const [recentFaces, setRecentFaces] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      posApi.getDashboard(),
      accessApi.getRecentFaces()
    ]).then(([statsRes, facesRes]) => {
      setStats(statsRes.data)
      setRecentFaces(facesRes.data)
    }).finally(() => setLoading(false))
  }, [])

  const fmt = (n: number) => new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' }).format(n)

  const API_URL = window.location.origin.includes(':5173') 
    ? window.location.origin.replace(':5173', ':8001')
    : window.location.origin

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
              title="Aperturas Manuales"
              value={stats.manual_openings}
              icon={<KeyRound size={20} className="text-blue-600" />}
              color="bg-blue-50"
              subtitle="realizadas hoy"
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

      {/* Caras Recientes - ÚLTIMA HORA */}
      <div className="card">
        <h2 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <Users size={16} className="text-green-500" />
          Recién Llegados (Última hora)
        </h2>
        {recentFaces.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-8">No hay accesos con foto en la última hora</p>
        ) : (
          <div className="flex flex-wrap gap-4">
            {recentFaces.map(face => (
              <div key={face.id} className="flex flex-col items-center gap-1 group">
                <div className="relative">
                  <img 
                    src={face.photo_path ? `${API_URL}${face.photo_path}` : 'https://via.placeholder.com/150'}
 
                    alt={face.name}
                    className="w-16 h-16 rounded-full object-cover border-2 border-green-400 shadow-sm group-hover:scale-105 transition-transform"
                    onError={(e) => { (e.target as HTMLImageElement).src = 'https://via.placeholder.com/150?text=Error'; }}
                  />
                  <div className="absolute -bottom-1 -right-1 bg-white rounded-full p-0.5 shadow">
                    <div className="w-3 h-3 bg-green-500 rounded-full border border-white" />
                  </div>
                </div>
                <span className="text-[10px] font-bold text-gray-700 max-w-[70px] truncate">
                  {face.name.split(' ')[0]}
                </span>
                <span className="text-[9px] text-gray-400">
                  {format(new Date(face.timestamp), 'HH:mm')}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
