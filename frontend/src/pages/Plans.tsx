import { useEffect, useState } from 'react'
import { plansApi } from '../services/api'
import type { MembershipPlan } from '../types'
import { Plus, Edit2, CreditCard } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Plans() {
  const [plans, setPlans] = useState<MembershipPlan[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<MembershipPlan | null>(null)
  const [form, setForm] = useState({
    name: '', description: '', duration_days: '30', price: '',
    color: '#4CAF50', allows_guest: false,
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

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        {plans.map(plan => (
          <div key={plan.id} className="card border-l-4" style={{ borderLeftColor: plan.color }}>
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: plan.color + '20' }}>
                  <CreditCard size={16} style={{ color: plan.color }} />
                </div>
                <h3 className="font-semibold text-gray-800">{plan.name}</h3>
              </div>
              <button onClick={() => openForm(plan)} className="text-gray-400 hover:text-blue-600">
                <Edit2 size={14} />
              </button>
            </div>
            {plan.description && (
              <p className="text-sm text-gray-500 mb-3">{plan.description}</p>
            )}
            <div className="flex items-end justify-between">
              <div>
                <p className="text-2xl font-bold text-gray-900">${plan.price.toFixed(2)}</p>
                <p className="text-xs text-gray-400">{plan.duration_days} días</p>
              </div>
              {plan.allows_guest && (
                <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">
                  Permite invitado
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="font-semibold">{editing ? 'Editar Plan' : 'Nuevo Plan'}</h2>
              <button onClick={() => setShowForm(false)} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <form onSubmit={submit} className="p-6 space-y-4">
              <div>
                <label className="label">Nombre *</label>
                <input className="input" value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required />
              </div>
              <div>
                <label className="label">Descripción</label>
                <input className="input" value={form.description}
                  onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Duración (días) *</label>
                  <input type="number" className="input" value={form.duration_days}
                    onChange={e => setForm(f => ({ ...f, duration_days: e.target.value }))} required />
                </div>
                <div>
                  <label className="label">Precio *</label>
                  <input type="number" step="0.01" className="input" value={form.price}
                    onChange={e => setForm(f => ({ ...f, price: e.target.value }))} required />
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div>
                  <label className="label">Color</label>
                  <input type="color" className="h-9 w-16 rounded border border-gray-300 cursor-pointer"
                    value={form.color} onChange={e => setForm(f => ({ ...f, color: e.target.value }))} />
                </div>
                <div className="flex items-center gap-2 mt-4">
                  <input type="checkbox" id="allows_guest" checked={form.allows_guest}
                    onChange={e => setForm(f => ({ ...f, allows_guest: e.target.checked }))} />
                  <label htmlFor="allows_guest" className="text-sm text-gray-700">Permite invitado</label>
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" className="btn-secondary flex-1" onClick={() => setShowForm(false)}>Cancelar</button>
                <button type="submit" className="btn-primary flex-1">
                  {editing ? 'Actualizar' : 'Crear'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
