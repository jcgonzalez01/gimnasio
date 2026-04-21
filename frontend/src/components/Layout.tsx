import { Outlet, NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Users, ShieldCheck, ShoppingCart,
  Package, Receipt, Cpu, CreditCard, Menu, X, Dumbbell
} from 'lucide-react'
import { useState } from 'react'

const nav = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/members', icon: Users, label: 'Miembros' },
  { to: '/access', icon: ShieldCheck, label: 'Control de Acceso' },
  { to: '/pos', icon: ShoppingCart, label: 'Punto de Venta' },
  { to: '/products', icon: Package, label: 'Productos' },
  { to: '/sales', icon: Receipt, label: 'Ventas' },
  { to: '/plans', icon: CreditCard, label: 'Membresías' },
  { to: '/devices', icon: Cpu, label: 'Dispositivos' },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-60' : 'w-16'} bg-gray-900 flex flex-col transition-all duration-200 shrink-0`}>
        {/* Logo */}
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

        {/* Nav */}
        <nav className="flex-1 py-4 space-y-1 px-2 overflow-y-auto">
          {nav.map(({ to, icon: Icon, label }) => (
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

        {/* Footer */}
        {sidebarOpen && (
          <div className="px-4 py-3 border-t border-gray-700">
            <p className="text-gray-500 text-xs">v1.0.0 · Hikvision ISAPI</p>
          </div>
        )}
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
