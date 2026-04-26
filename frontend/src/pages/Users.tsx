import { useEffect, useState } from 'react'
import { authApi } from '../services/api'
import type { AuthUser, UserRole } from '../types'
import { Plus, Edit2, Trash2, KeyRound, X } from 'lucide-react'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import DeleteConfirmationModal from '../components/DeleteConfirmationModal'

const ROLE_OPTIONS: { value: UserRole; label: string }[] = [
  { value: 'admin',     label: 'Administrador' },
  { value: 'manager',   label: 'Gerente' },
  { value: 'cashier',   label: 'Cajero' },
  { value: 'reception', label: 'Recepción' },
]

interface FormData {
  id?: number
  username: string
  email: string
  full_name: string
  role: UserRole
  password: string
  is_active: boolean
}

const emptyForm: FormData = {
  username: '', email: '', full_name: '', role: 'cashier', password: '', is_active: true,
}

export default function Users() {
  const [users, setUsers] = useState<AuthUser[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<FormData>(emptyForm)
  const [editing, setEditing] = useState(false)

  // Estado para el borrado seguro
  const [deleteModal, setDeleteModal] = useState<{
    isOpen: boolean;
    user?: AuthUser;
    impact?: any;
    loading: boolean;
  }>({ isOpen: false, loading: false });

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await authApi.listUsers()
      setUsers(data)
    } catch {
      toast.error('Error cargando usuarios')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const startCreate = () => {
    setForm(emptyForm)
    setEditing(false)
    setShowForm(true)
  }

  const startEdit = (u: AuthUser) => {
    setForm({
      id: u.id,
      username: u.username,
      email: u.email || '',
      full_name: u.full_name || '',
      role: u.role,
      password: '',
      is_active: u.is_active,
    })
    setEditing(true)
    setShowForm(true)
  }

  const submit = async () => {
    try {
      if (editing && form.id) {
        const { id: _id, ...rest } = form
        const payload: any = { ...rest }
        if (!payload.password) delete payload.password
        await authApi.updateUser(form.id, payload)
        toast.success('Usuario actualizado')
      } else {
        if (!form.password) {
          toast.error('La contraseña es obligatoria')
          return
        }
        const { id: _id, ...payload } = form
        await authApi.createUser(payload)
        toast.success('Usuario creado')
      }
      setShowForm(false)
      load()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Error guardando usuario')
    }
  }

  const handleDeleteClick = (u: AuthUser) => {
    setDeleteModal({
      isOpen: true,
      user: u,
      impact: undefined,
      loading: false
    })
  }

  const confirmDelete = async (force: boolean) => {
    if (!deleteModal.user) return
    const u = deleteModal.user
    
    setDeleteModal(prev => ({ ...prev, loading: true }))
    try {
      await authApi.deleteUser(u.id, force)
      toast.success(`Usuario "${u.username}" eliminado`)
      setDeleteModal({ isOpen: false, loading: false })
      load()
    } catch (err: any) {
      if (err.response?.status === 409 && err.response?.data?.requires_force) {
        setDeleteModal(prev => ({ 
          ...prev, 
          impact: err.response.data, 
          loading: false 
        }))
      } else {
        toast.error(err?.response?.data?.detail || 'Error al eliminar')
        setDeleteModal(prev => ({ ...prev, loading: false }))
      }
    }
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Usuarios del sistema</h1>
        <button
          onClick={startCreate}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
        >
          <Plus size={16} /> Nuevo usuario
        </button>
      </div>

      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 text-left">
            <tr>
              <th className="px-4 py-3">Usuario</th>
              <th className="px-4 py-3">Nombre</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Rol</th>
              <th className="px-4 py-3">Estado</th>
              <th className="px-4 py-3">Último ingreso</th>
              <th className="px-4 py-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={7} className="text-center py-8 text-gray-400">Cargando…</td></tr>
            ) : users.length === 0 ? (
              <tr><td colSpan={7} className="text-center py-8 text-gray-400">Sin usuarios</td></tr>
            ) : users.map(u => (
              <tr key={u.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium">{u.username}</td>
                <td className="px-4 py-3">{u.full_name || '—'}</td>
                <td className="px-4 py-3">{u.email || '—'}</td>
                <td className="px-4 py-3 capitalize">{u.role}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded text-xs ${u.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-500'}`}>
                    {u.is_active ? 'Activo' : 'Inactivo'}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-500">
                  {u.last_login ? format(new Date(u.last_login), 'dd/MM/yyyy HH:mm') : '—'}
                </td>
                <td className="px-4 py-3 text-right space-x-2">
                  <button onClick={() => startEdit(u)} className="text-blue-600 hover:text-blue-800" title="Editar">
                    <Edit2 size={16} />
                  </button>
                  <button onClick={() => handleDeleteClick(u)} className="text-red-600 hover:text-red-800" title="Eliminar">
                    <Trash2 size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="text-lg font-semibold">
                {editing ? 'Editar usuario' : 'Nuevo usuario'}
              </h2>
              <button onClick={() => setShowForm(false)}><X size={18} /></button>
            </div>
            <div className="p-6 space-y-3">
              <input
                placeholder="Usuario"
                value={form.username}
                disabled={editing}
                onChange={e => setForm({ ...form, username: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg disabled:bg-gray-100"
              />
              <input
                placeholder="Nombre completo"
                value={form.full_name}
                onChange={e => setForm({ ...form, full_name: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
              <input
                placeholder="Email"
                type="email"
                value={form.email}
                onChange={e => setForm({ ...form, email: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
              <select
                value={form.role}
                onChange={e => setForm({ ...form, role: e.target.value as UserRole })}
                className="w-full px-3 py-2 border rounded-lg"
              >
                {ROLE_OPTIONS.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
              </select>
              <div className="relative">
                <KeyRound size={14} className="absolute left-3 top-3 text-gray-400" />
                <input
                  placeholder={editing ? 'Nueva contraseña (opcional)' : 'Contraseña'}
                  type="password"
                  value={form.password}
                  onChange={e => setForm({ ...form, password: e.target.value })}
                  className="w-full pl-9 pr-3 py-2 border rounded-lg"
                />
              </div>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={e => setForm({ ...form, is_active: e.target.checked })}
                />
                Activo
              </label>
            </div>
            <div className="px-6 py-4 border-t flex justify-end gap-2">
              <button onClick={() => setShowForm(false)} className="px-4 py-2 text-gray-600">Cancelar</button>
              <button onClick={submit} className="px-4 py-2 bg-blue-600 text-white rounded-lg">Guardar</button>
            </div>
          </div>
        </div>
      )}

      <DeleteConfirmationModal
        isOpen={deleteModal.isOpen}
        title="Eliminar Usuario"
        message={`¿Estás seguro de que deseas eliminar al usuario "${deleteModal.user?.username}"?`}
        impact={deleteModal.impact}
        isLoading={deleteModal.loading}
        onConfirm={confirmDelete}
        onCancel={() => setDeleteModal({ isOpen: false, loading: false })}
      />
    </div>
  )
}
