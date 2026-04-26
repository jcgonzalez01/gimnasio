import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { membersApi } from '../services/api'
import type { Member, MemberListItem } from '../types'
import { Plus, Search, ScanFace, User, ChevronRight, Pencil, Trash2 } from 'lucide-react'
import { format } from 'date-fns'
import toast from 'react-hot-toast'
import MemberForm from '../components/MemberForm'
import DeleteConfirmationModal from '../components/DeleteConfirmationModal'

export default function Members() {
  const [members, setMembers]             = useState<MemberListItem[]>([])
  const [loading, setLoading]             = useState(true)
  const [search, setSearch]               = useState('')
  const [statusFilter, setStatusFilter]   = useState('')
  const [showForm, setShowForm]           = useState(false)
  const [editingMember, setEditingMember] = useState<Member | null>(null)
  const [loadingEdit, setLoadingEdit]     = useState<number | null>(null)
  const navigate = useNavigate()

  // Estado para el modal de borrado
  const [deleteModal, setDeleteModal] = useState<{
    isOpen: boolean;
    member: MemberListItem | null;
    impact?: any;
    loading: boolean;
  }>({
    isOpen: false,
    member: null,
    loading: false
  })

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

  const handleDeleteClick = (e: React.MouseEvent, m: MemberListItem) => {
    e.stopPropagation()
    if (m.has_active_membership) {
      toast.error('No se puede eliminar: tiene membresía activa vigente', { duration: 4000 })
      return
    }
    setDeleteModal({
      isOpen: true,
      member: m,
      loading: false
    })
  }

  const confirmDelete = async (force: boolean) => {
    if (!deleteModal.member) return
    setDeleteModal(prev => ({ ...prev, loading: true }))
    try {
      await membersApi.delete(deleteModal.member.id, force)
      toast.success(`🗑️ ${deleteModal.member.first_name} eliminado`)
      setDeleteModal({ isOpen: false, member: null, loading: false })
      load()
    } catch (err: any) {
      if (err.response?.status === 409) {
        // El backend indica que hay historial y requiere force
        setDeleteModal(prev => ({
          ...prev,
          loading: false,
          impact: err.response.data.detail // El backend envía el objeto de impacto en detail en este caso
            ? err.response.data
            : { history: true, detail: err.response.data.detail, items: [] }
        }))
        // Si el backend envió el payload de assess_member directamente en detail o como root
        const data = err.response.data;
        if (data.requires_force) {
           setDeleteModal(prev => ({ ...prev, impact: data, loading: false }));
        } else {
           toast.error(data.detail || 'Error de conflicto');
           setDeleteModal(prev => ({ ...prev, loading: false }));
        }
      } else {
        const msg = err.response?.data?.detail || 'Error al eliminar'
        toast.error(msg)
        setDeleteModal(prev => ({ ...prev, loading: false }))
      }
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
                <td className="px-4 py-3">
                  <p>{m.email || '—'}</p>
                  <p className="text-gray-400 text-xs">{m.phone || ''}</p>
                </td>
                <td className="px-4 py-3">{statusBadge(m.status)}</td>
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
                <td className="px-4 py-3">
                  {m.face_enrolled ? (
                    <span className="flex items-center gap-1 text-green-600 text-xs font-medium">
                      <ScanFace size={14} /> Enrolado
                    </span>
                  ) : (
                    <span className="text-gray-400 text-xs">—</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={e => openEdit(e, m)}
                      disabled={loadingEdit === m.id}
                      className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                      {loadingEdit === m.id
                        ? <span className="w-3.5 h-3.5 border-2 border-blue-300 border-t-blue-600 rounded-full animate-spin block" />
                        : <Pencil size={14} />}
                    </button>
                    <button
                      onClick={e => handleDeleteClick(e, m)}
                      className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                      <Trash2 size={14} />
                    </button>
                    <ChevronRight size={14} className="text-gray-300 ml-1" />
                  </div>
                  <div className="flex justify-end group-hover:hidden">
                    <ChevronRight size={16} className="text-gray-300" />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showForm && (
        <MemberForm
          onClose={() => setShowForm(false)}
          onSaved={() => { setShowForm(false); load() }}
        />
      )}

      {editingMember && (
        <MemberForm
          member={editingMember}
          onClose={() => setEditingMember(null)}
          onSaved={() => { setEditingMember(null); load() }}
        />
      )}

      <DeleteConfirmationModal
        isOpen={deleteModal.isOpen}
        title="Eliminar Miembro"
        message={`¿Estás seguro de que deseas eliminar a "${deleteModal.member?.first_name} ${deleteModal.member?.last_name}"?`}
        impact={deleteModal.impact}
        isLoading={deleteModal.loading}
        onConfirm={confirmDelete}
        onCancel={() => setDeleteModal({ isOpen: false, member: null, loading: false })}
      />
    </div>
  )
}
