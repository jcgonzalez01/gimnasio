import { Outlet, NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Users as UsersIcon, ShieldCheck, ShoppingCart,
  Package, Receipt, Cpu, CreditCard, Menu, X, Dumbbell, BarChart3,
  DoorOpen, Loader2, LogOut, UserCog, FileClock
} from 'lucide-react'
import { useState } from 'react'
import { devicesApi } from '../services/api'
import { useAuth } from '../context/AuthContext'
import type { UserRole } from '../types'

interface NavItem {
  to: string
  icon: any
  label: string
  roles?: UserRole[]   // Si se omite, todos pueden verlo
}

const nav: NavItem[] = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/members',   icon: UsersIcon,        label: 'Miembros' },
  { to: '/access',    icon: ShieldCheck,      label: 'Control de Acceso' },
  { to: '/pos',       icon: ShoppingCart,     label: 'Punto de Venta' },
  { to: '/sales',     icon: Receipt,          label: 'Ventas' },
  { to: '/products',  icon: Package,          label: 'Productos',     roles: ['admin', 'manager'] },
  { to: '/plans',     icon: CreditCard,       label: 'Membresías',    roles: ['admin', 'manager'] },
  { to: '/reports',   icon: BarChart3,        label: 'Reportes',      roles: ['admin', 'manager'] },
  { to: '/devices',   icon: Cpu,              label: 'Dispositivos',  roles: ['admin'] },
  { to: '/users',     icon: UserCog,          label: 'Usuarios',      roles: ['admin'] },
  { to: '/audit',     icon: FileClock,        label: 'Auditoría',     roles: ['admin'] },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [isOpening, setIsOpening] = useState(false)
  const { user, logout, hasRole } = useAuth()

  const visibleNav = nav.filter(item => !item.roles || hasRole(...item.roles))

  const handleOpenDoor = async () => {
    try {
      setIsOpening(true)
      const devRes = await devicesApi.list()
      const accessDevices = devRes.data.filter(d => d.is_active && d.device_type === 'access_control')
      if (accessDevices.length === 0) return
      await Promise.allSettled(accessDevices.map(d => devicesApi.openDoor(d.id)))
    } catch (error) {
      console.error('Error opening door:', error)
    } finally {
      setIsOpening(false)
    }
  }

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-60' : 'w-16'} bg-gray-900 flex flex-col transition-all duration-200 shrink-0 z-20`}>
        <div className="flex items-center gap-3 px-4 py-5 border-b border-gray-700">
          <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center shrink-0">
            <Dumbbell size={18} className="text-white" />
          </div>
          {sidebarOpen && (
            <span className="text-white font-bold text-sm leading-tight">
              GymSystem<br /><span className="text-blue-400 font-normal text-xs">Pro</span>
            </span>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="ml-auto text-gray-400 hover:text-white"
          >
            {sidebarOpen ? <X size={16} /> : <Menu size={16} />}
          </button>
        </div>

        <nav className="flex-1 py-4 space-y-1 px-2 overflow-y-auto">
          {visibleNav.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                }`
              }
            >
              <Icon size={18} className="shrink-0" />
              {sidebarOpen && <span className="truncate">{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* User + logout */}
        <div className="px-3 py-3 border-t border-gray-700">
          {sidebarOpen && user && (
            <div className="text-xs text-gray-400 mb-2 px-1">
              <div className="text-white font-medium truncate">{user.full_name || user.username}</div>
              <div className="text-gray-500 capitalize">{user.role}</div>
            </div>
          )}
          <button
            onClick={logout}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
            title="Cerrar sesión"
          >
            <LogOut size={16} />
            {sidebarOpen && <span>Cerrar sesión</span>}
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        <div className="absolute top-4 right-8 z-10">
          <button
            onClick={handleOpenDoor}
            disabled={isOpening}
            title="Abrir puerta"
            className={`flex items-center gap-2 px-5 py-2.5 rounded-full shadow-lg font-bold transition-all transform active:scale-95 ${
              isOpening
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-green-600 text-white hover:bg-green-700 hover:shadow-xl'
            }`}
          >
            {isOpening ? <Loader2 size={20} className="animate-spin" /> : <DoorOpen size={20} />}
            <span className="hidden sm:inline">ABRIR PUERTA</span>
          </button>
        </div>

        <main className="flex-1 overflow-y-auto pt-4">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
