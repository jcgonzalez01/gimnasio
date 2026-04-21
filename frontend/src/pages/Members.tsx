import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { membersApi } from '../services/api'
import type { Member, MemberListItem } from '../types'
import { Plus, Search, ScanFace, User, ChevronRight, Pencil, Trash2 } from 'lucide-react'
import { format } from 'date-fns'
import toast from 'react-hot-toast'
import MemberForm from '../components/MemberForm'

export default function Members() {
  const [members, setMembers]             = useState<MemberListItem[]>([])
  const [loading, setLoading]             = useState(true)
  const [search, setSearch]               = useState('')
  const [statusFilter, setStatusFilter]   = useState('')
  const [showForm, setShowForm]           = useState(false)
  const [editingMember, setEditingMember] = useState<Member | null>(null)
  const [loadingEdit, setLoadingEdit]     = useState<number | null>(null)
  const [deleting, setDeleting]           = useState<number | null>(null)
  const navigate = useNavigate()

  const load = async () => {
    setLoading(true)
    try {
      const res = await membersApi.list({ search: search || undefined, status: statusFilter || undefined })
      setMembers(res.data)
    } catch {
      toast.error('Error al cargar miembros')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [search, statusFilter])

  const openEdit = async (e: React.MouseEvent, m: MemberListItem) => {
    e.stopPropagation()
    setLoadingEdit(m.id)
    try {
      const res = await membersApi.get(m.id)
      setEditingMember(res.data)
    } catch {
      toast.error('Error al cargar datos del miembro')
    } finally {
      setLoadingEdit(null)
    }
  }

  const handleDelete = async (e: React.MouseEvent, m: MemberListItem) => {
    e.stopPropagation()
    if (m.has_active_membership) {
      toast.error('No se puede eliminar: tiene membresía activa vigente', { duration: 4000 })
      return
    }
    if (!confirm(`¿Eliminar definitivamente a "${m.first_name} ${m.last_name}"?\n\nEsta acción no se puede deshacer.`)) return
    setDeleting(m.id)
    try {
      await membersApi.delete(m.id)
      toast.success(`🗑️ ${m.first_name} ${m.last_name} eliminado`)
      load()
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Error al eliminar'
      toast.error(msg, { duration: 5000 })
    } finally {
      setDeleting(null)
    }
  }

  const statusBadge = (s: string) => {
    const map: Record<string, string> = {
      active: 'badge-active', inactive: 'badge-inactive',
      expired: 'badge-expired', suspended: 'badge-suspended',
    }
    const label: Record<string, string> = {
      active: 'Activo', inactive: 'Inactivo', expired: 'Vencido', suspended: 'Suspendido',
    }
    return <span className={map[s] || 'badge-inactive'}>{label[s] || s}</span>
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Miembros</h1>
          <p className="text-gray-500 text-sm">{members.length} registros</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setShowForm(true)}>
          <Plus size={16} /> Nuevo Miembro
        </button>
      </div>

      {/* Filtros */}
      <div className="flex gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input className="input pl-9" placeholder="Buscar por nombre, email, teléfono..."
            value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <select className="input w-40" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
          <option value="">Todos</option>
          <option value="active">Activos</option>
          <option value="expired">Vencidos</option>
          <option value="inactive">Inactivos</option>
          <option value="suspended">Suspendidos</option>
        </select>
      </div>

      {/* Tabla */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Miembro</th>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Contacto</th>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Estado</th>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Membresía</th>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Facial</th>
              <th className="px-4 py-3 text-right text-gray-500 font-medium">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {loading ? (
              <tr><td colSpan={6} className="text-center py-12 text-gray-400">Cargando...</td></tr>
            ) : members.length === 0 ? (
              <tr><td colSpan={6} className="text-center py-12 text-gray-400">Sin miembros registrados</td></tr>
            ) : members.map(m => (
              <tr key={m.id}
                  className="hover:bg-gray-50 cursor-pointer transition-colors group"
                  onClick={() => navigate(`/members/${m.id}`)}>
                {/* Foto + nombre */}
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    {m.photo_path ? (
                      <img src={m.photo_path} alt=""
                        className="w-9 h-9 rounded-full object-cover border border-gray-200" />
                    ) : (
                      <div className="w-9 h-9 rounded-full bg-gray-100 flex items-center justify-center">
                        <User size={16} className="text-gray-400" />
                      </div>
                    )}
                    <div>
                      <p className="font-medium">{m.first_name} {m.last_name}</p>
                      <p className="text-gray-400 text-xs">{m.member_number}</p>
                    </div>
                  </div>
                </td>

                {/* Contacto */}
                <td className="px-4 py-3">
                  <p>{m.email || '—'}</p>
                  <p className="text-gray-400 text-xs">{m.phone || ''}</p>
                </td>

                {/* Estado */}
                <td className="px-4 py-3">{statusBadge(m.status)}</td>

                {/* Membresía */}
                <td className="px-4 py-3">
                  {m.has_active_membership ? (
                    <div>
                      <span className="badge-active">Activa</span>
                      {m.membership_expires && (
                        <p className="text-xs text-gray-400 mt-0.5">
                          Vence: {format(new Date(m.membership_expires), 'dd/MM/yyyy')}
                        </p>
                      )}
                    </div>
                  ) : (
                    <span className="badge-expired">Sin membresía</span>
                  )}
                </td>

                {/* Facial */}
                <td className="px-4 py-3">
                  {m.face_enrolled ? (
                    <span className="flex items-center gap-1 text-green-600 text-xs font-medium">
                      <ScanFace size={14} /> Enrolado
                    </span>
                  ) : (
                    <span className="text-gray-400 text-xs">—</span>
                  )}
                </td>

                {/* Acciones */}
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {/* Editar */}
                    <button
                      onClick={e => openEdit(e, m)}
                      disabled={loadingEdit === m.id}
                      title="Editar miembro"
                      className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                      {loadingEdit === m.id
                        ? <span className="w-3.5 h-3.5 border-2 border-blue-300 border-t-blue-600 rounded-full animate-spin block" />
                        : <Pencil size={14} />}
                    </button>

                    {/* Eliminar — solo si no tiene membresía activa */}
                    <button
                      onClick={e => handleDelete(e, m)}
                      disabled={deleting === m.id || m.has_active_membership}
                      title={m.has_active_membership
                        ? 'No se puede eliminar: tiene membresía activa'
                        : 'Eliminar miembro'}
                      className={`p-1.5 rounded-lg transition-colors ${
                        m.has_active_membership
                          ? 'text-gray-200 cursor-not-allowed'
                          : deleting === m.id
                            ? 'text-red-300 cursor-wait'
                            : 'text-gray-400 hover:text-red-600 hover:bg-red-50'
                      }`}>
                      <Trash2 size={14} />
                    </button>

                    <ChevronRight size={14} className="text-gray-300 ml-1" />
                  </div>
                  {/* cuando no hay hover, mostrar solo el chevron */}
                  <div className="flex justify-end group-hover:hidden">
                    <ChevronRight size={16} className="text-gray-300" />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal nuevo miembro */}
      {showForm && (
        <MemberForm
          onClose={() => setShowForm(false)}
          onSaved={() => { setShowForm(false); load() }}
        />
      )}

      {/* Modal editar miembro */}
      {editingMember && (
        <MemberForm
          member={editingMember}
          onClose={() => setEditingMember(null)}
          onSaved={() => { setEditingMember(null); load() }}
        />
      )}
    </div>
  )
}
