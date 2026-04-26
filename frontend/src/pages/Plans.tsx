import { useEffect, useState } from 'react'
import { plansApi } from '../services/api'
import type { MembershipPlan } from '../types'
import { Plus, Edit2, CreditCard, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import DeleteConfirmationModal from '../components/DeleteConfirmationModal'

export default function Plans() {
  const [plans, setPlans] = useState<MembershipPlan[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<MembershipPlan | null>(null)
  const [form, setForm] = useState({
    name: '', description: '', duration_days: '30', price: '',
    color: '#4CAF50', allows_guest: false,
  })

  // Estado para el modal de borrado
  const [deleteModal, setDeleteModal] = useState<{
    isOpen: boolean;
    plan: MembershipPlan | null;
    impact?: any;
    loading: boolean;
  }>({
    isOpen: false,
    plan: null,
    loading: false
  })

  const load = () => plansApi.list().then(r => setPlans(r.data))
  useEffect(() => { load() }, [])

  const openForm = (plan?: MembershipPlan) => {
    if (plan) {
      setEditing(plan)
      setForm({
        name: plan.name, description: plan.description || '',
        duration_days: String(plan.duration_days), price: String(plan.price),
        color: plan.color, allows_guest: plan.allows_guest,
      })
    } else {
      setEditing(null)
      setForm({ name: '', description: '', duration_days: '30', price: '', color: '#4CAF50', allows_guest: false })
    }
    setShowForm(true)
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    const data = {
      name: form.name, description: form.description || undefined,
      duration_days: parseInt(form.duration_days), price: parseFloat(form.price),
      color: form.color, allows_guest: form.allows_guest,
    }
    try {
      if (editing) {
        await plansApi.update(editing.id, data)
        toast.success('Plan actualizado')
      } else {
        await plansApi.create(data)
        toast.success('Plan creado')
      }
      setShowForm(false)
      load()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Error al guardar')
    }
  }

  const handleDeleteClick = (plan: MembershipPlan) => {
    setDeleteModal({
      isOpen: true,
      plan: plan,
      loading: false
    })
  }

  const confirmDelete = async (force: boolean) => {
    if (!deleteModal.plan) return
    setDeleteModal(prev => ({ ...prev, loading: true }))
    try {
      await plansApi.delete(deleteModal.plan.id, force)
      toast.success(`🗑️ Plan "${deleteModal.plan.name}" eliminado`)
      setDeleteModal({ isOpen: false, plan: null, loading: false })
      load()
    } catch (err: any) {
      if (err.response?.status === 409) {
        setDeleteModal(prev => ({
          ...prev,
          loading: false,
          impact: err.response.data.requires_force ? err.response.data : { history: true, detail: err.response.data.detail, items: [] }
        }))
      } else {
        toast.error(err.response?.data?.detail || 'Error al eliminar')
        setDeleteModal(prev => ({ ...prev, loading: false }))
      }
    }
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Planes de Membresía</h1>
          <p className="text-gray-500 text-sm">{plans.length} planes activos</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => openForm()}>
          <Plus size={16} /> Nuevo Plan
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {plans.map(plan => (
          <div key={plan.id} className="card border-l-4 group relative" style={{ borderLeftColor: plan.color }}>
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center"
                  style={{ backgroundColor: plan.color + '20' }}>
                  <CreditCard size={20} style={{ color: plan.color }} />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900">{plan.name}</h3>
                  <p className="text-[10px] text-gray-400 font-mono">ID: {plan.id}</p>
                </div>
              </div>
              <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button onClick={() => openForm(plan)} 
                  className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                  title="Editar">
                  <Edit2 size={14} />
                </button>
                <button onClick={() => handleDeleteClick(plan)} 
                  className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  title="Eliminar">
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
            {plan.description && (
              <p className="text-sm text-gray-500 mb-4 line-clamp-2 min-h-[2.5rem]">{plan.description}</p>
            )}
            <div className="flex items-end justify-between pt-2 border-t border-gray-50">
              <div>
                <p className="text-2xl font-black text-gray-900">${plan.price.toFixed(2)}</p>
                <p className="text-xs text-gray-400 font-medium">{plan.duration_days} días de acceso</p>
              </div>
              {plan.allows_guest && (
                <span className="text-[10px] font-bold uppercase tracking-wider bg-blue-50 text-blue-600 px-2 py-1 rounded-md">
                  Invitado
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b bg-gray-50">
              <h2 className="font-bold text-gray-900">{editing ? 'Editar Plan' : 'Nuevo Plan'}</h2>
              <button onClick={() => setShowForm(false)} className="text-gray-400 hover:text-gray-600 transition-colors">✕</button>
            </div>
            <form onSubmit={submit} className="p-6 space-y-4">
              <div>
                <label className="label">Nombre del Plan *</label>
                <input className="input" placeholder="Ej: Mensual VIP" value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required />
              </div>
              <div>
                <label className="label">Descripción</label>
                <textarea className="input min-h-[80px]" placeholder="Detalles de lo que incluye..." value={form.description}
                  onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Duración (días) *</label>
                  <input type="number" className="input" value={form.duration_days}
                    onChange={e => setForm(f => ({ ...f, duration_days: e.target.value }))} required />
                </div>
                <div>
                  <label className="label">Precio ($) *</label>
                  <input type="number" step="0.01" className="input" value={form.price}
                    onChange={e => setForm(f => ({ ...f, price: e.target.value }))} required />
                </div>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <label className="text-sm font-medium text-gray-700">Color</label>
                  <input type="color" className="h-8 w-12 rounded border-0 bg-transparent cursor-pointer"
                    value={form.color} onChange={e => setForm(f => ({ ...f, color: e.target.value }))} />
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" id="allows_guest" checked={form.allows_guest}
                    className="rounded text-blue-600 focus:ring-blue-500"
                    onChange={e => setForm(f => ({ ...f, allows_guest: e.target.checked }))} />
                  <label htmlFor="allows_guest" className="text-sm font-medium text-gray-700 select-none">Permite invitado</label>
                </div>
              </div>
              <div className="flex gap-3 pt-4">
                <button type="button" className="btn-secondary flex-1" onClick={() => setShowForm(false)}>Cancelar</button>
                <button type="submit" className="btn-primary flex-1">
                  {editing ? 'Actualizar' : 'Crear Plan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <DeleteConfirmationModal
        isOpen={deleteModal.isOpen}
        title="Eliminar Plan"
        message={`¿Estás seguro de que deseas eliminar el plan "${deleteModal.plan?.name}"? Esta acción no se puede deshacer.`}
        impact={deleteModal.impact}
        isLoading={deleteModal.loading}
        onConfirm={confirmDelete}
        onCancel={() => setDeleteModal({ isOpen: false, plan: null, loading: false })}
      />
    </div>
  )
}
