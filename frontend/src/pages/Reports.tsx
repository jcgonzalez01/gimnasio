import { useState, useEffect } from 'react'
import api, { reportsApi } from '../services/api'
import type { ReportsDashboardStats, DailyStats, TopMember, TopProduct, AccessReport, SalesReport } from '../types'

export default function Reports() {
  const [dashboard, setDashboard] = useState<ReportsDashboardStats | null>(null)
  const [dailyStats, setDailyStats] = useState<DailyStats[]>([])
  const [topMembers, setTopMembers] = useState<TopMember[]>([])
  const [topProducts, setTopProducts] = useState<TopProduct[]>([])
  const [accessLogs, setAccessLogs] = useState<AccessReport[]>([])
  const [salesLogs, setSalesLogs] = useState<SalesReport[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'dashboard' | 'access' | 'sales'>('dashboard')
  const [daysFilter, setDaysFilter] = useState(7)

  const loadData = async () => {
    setLoading(true)
    try {
      const [dashRes, dailyRes, membersRes, productsRes, accessRes, salesRes] = await Promise.all([
        reportsApi.getDashboard(),
        reportsApi.getDailyStats(daysFilter),
        reportsApi.getTopMembers(daysFilter, 10),
        reportsApi.getTopProducts(daysFilter, 10),
        reportsApi.getAccessReport({ limit: 50 }),
        reportsApi.getSalesReport({ limit: 50 }),
      ])
      setDashboard(dashRes.data)
      setDailyStats(dailyRes.data)
      setTopMembers(membersRes.data)
      setTopProducts(productsRes.data)
      setAccessLogs(accessRes.data)
      setSalesLogs(salesRes.data)
    } catch (err) {
      console.error('Error loading reports:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [daysFilter])

  if (loading && !dashboard) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Reportes y Estadisticas</h1>
        <select
          value={daysFilter}
          onChange={(e) => setDaysFilter(Number(e.target.value))}
          className="border rounded-lg px-4 py-2"
        >
          <option value={7}>Ultimos 7 dias</option>
          <option value={14}>Ultimos 14 dias</option>
          <option value={30}>Ultimos 30 dias</option>
          <option value={60}>Ultimos 60 dias</option>
          <option value={90}>Ultimos 90 dias</option>
        </select>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Accesos Hoy"
          value={dashboard?.today_access || 0}
          subtitle={`${dashboard?.today_granted || 0} concedidos`}
          color="blue"
        />
        <StatCard
          title="Ventas Hoy"
          value={`$${(dashboard?.today_sales || 0).toFixed(2)}`}
          subtitle={`${dashboard?.today_sales ? 'transacciones' : 'sin ventas'}`}
          color="green"
        />
        <StatCard
          title="Miembros"
          value={dashboard?.total_members || 0}
          subtitle={`${dashboard?.active_members || 0} activos`}
          color="purple"
        />
        <StatCard
          title="Stock Bajo"
          value={dashboard?.low_stock_products || 0}
          subtitle="productos"
          color="red"
        />
      </div>

      <div className="flex gap-2 border-b">
        {(['dashboard', 'access', 'sales'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 font-medium border-b-2 transition-colors ${
              activeTab === tab
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab === 'dashboard' ? 'Estadisticas' : tab === 'access' ? 'Accesos' : 'Ventas'}
          </button>
        ))}
      </div>

      {activeTab === 'dashboard' && (
        <div className="grid lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Accesos por Dia</h2>
            <div className="space-y-3">
              {dailyStats.slice().reverse().map((stat) => (
                <div key={stat.date} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">{new Date(stat.date).toLocaleDateString()}</span>
                  <div className="flex items-center gap-4">
                    <span className="text-green-600 font-medium">{stat.access_granted}</span>
                    <span className="text-red-500">{stat.access_denied}</span>
                    <span className="text-gray-400">{stat.access_count} total</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Miembros mas Frecuentes</h2>
            <div className="space-y-3">
              {topMembers.map((member) => (
                <div key={member.member_id} className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{member.member_name}</p>
                    <p className="text-sm text-gray-500">{member.member_number}</p>
                  </div>
                  <span className="text-blue-600 font-bold">{member.visits} visitas</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6 lg:col-span-2">
            <h2 className="text-lg font-semibold mb-4">Productos mas Vendidos</h2>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {topProducts.map((product) => (
                <div key={product.product_id} className="border rounded-lg p-4">
                  <p className="font-medium truncate">{product.product_name}</p>
                  <p className="text-2xl font-bold text-blue-600">{product.quantity_sold}</p>
                  <p className="text-sm text-gray-500">vendidos</p>
                  <p className="text-sm text-green-600">${product.total_sales.toFixed(2)}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'access' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Fecha</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Miembro</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Tipo</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Resultado</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {accessLogs.map((log) => (
                  <tr key={log.id}>
                    <td className="px-4 py-3 text-sm">{new Date(log.timestamp).toLocaleString()}</td>
                    <td className="px-4 py-3 text-sm">{log.member_name || 'Sin identificar'}</td>
                    <td className="px-4 py-3 text-sm capitalize">{log.access_type}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        log.result === 'granted'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-red-100 text-red-700'
                      }`}>
                        {log.result}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'sales' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Fecha</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Venta</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Cliente</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Items</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Total</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-600">Pago</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {salesLogs.map((sale) => (
                  <tr key={sale.id}>
                    <td className="px-4 py-3 text-sm">{new Date(sale.created_at).toLocaleString()}</td>
                    <td className="px-4 py-3 text-sm font-mono">{sale.sale_number}</td>
                    <td className="px-4 py-3 text-sm">{sale.member_name || 'Publico general'}</td>
                    <td className="px-4 py-3 text-sm">{sale.items_count}</td>
                    <td className="px-4 py-3 text-sm font-bold text-green-600">${sale.total.toFixed(2)}</td>
                    <td className="px-4 py-3 text-sm capitalize">{sale.payment_method}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

function StatCard({ title, value, subtitle, color }: {
  title: string
  value: string | number
  subtitle: string
  color: 'blue' | 'green' | 'purple' | 'red'
}) {
  const colors = {
    blue: 'bg-blue-50 text-blue-700',
    green: 'bg-green-50 text-green-700',
    purple: 'bg-purple-50 text-purple-700',
    red: 'bg-red-50 text-red-700',
  }

  return (
    <div className={`${colors[color]} rounded-lg p-4`}>
      <p className="text-sm font-medium opacity-75">{title}</p>
      <p className="text-3xl font-bold my-1">{value}</p>
      <p className="text-xs opacity-75">{subtitle}</p>
    </div>
  )
}