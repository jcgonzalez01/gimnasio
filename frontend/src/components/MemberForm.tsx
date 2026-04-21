import { useState } from 'react'
import { membersApi } from '../services/api'
import type { Member } from '../types'
import { X, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'

interface Props {
  onClose: () => void
  onSaved: () => void
  member?: Member | null   // si viene → modo edición (tipo completo)
}

export default function MemberForm({ onClose, onSaved, member }: Props) {
  const editing = !!member

  const [form, setForm] = useState({
    first_name:        member?.first_name        ?? '',
    last_name:         member?.last_name         ?? '',
    email:             member?.email             ?? '',
    phone:             member?.phone             ?? '',
    birth_date:        member?.birth_date        ? member.birth_date.slice(0, 10) : '',
    gender:            member?.gender            ?? '',
    address:           member?.address           ?? '',
    emergency_contact: member?.emergency_contact ?? '',
    emergency_phone:   member?.emergency_phone   ?? '',
    notes:             member?.notes             ?? '',
  })
  const [saving, setSaving]   = useState(false)
  const [error, setError]     = useState<string | null>(null)

  const set = (field: string, value: string) => {
    setError(null)
    setForm(f => ({ ...f, [field]: value }))
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.first_name.trim() || !form.last_name.trim()) {
      setError('Nombre y apellido son obligatorios')
      return
    }
    setSaving(true)
    setError(null)
    try {
      const payload: Record<string, any> = { ...form }
      Object.keys(payload).forEach(k => { if (payload[k] === '') payload[k] = null })

      if (editing && member) {
        await membersApi.update(member.id, payload)
        toast.success('✅ Miembro actualizado')
      } else {
        await membersApi.create(payload)
        toast.success('✅ Miembro creado correctamente')
      }
      onSaved()
    } catch (err: any) {
      const msg = err.response?.data?.detail || (editing ? 'Error al actualizar' : 'Error al crear')
      setError(msg)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="font-semibold text-lg">
            {editing ? `Editar Miembro — ${member?.first_name} ${member?.last_name}` : 'Nuevo Miembro'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={submit} className="p-6 space-y-4">
          {error && (
            <div className="flex items-start gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
              <AlertCircle size={16} className="shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Nombre *</label>
              <input className="input" placeholder="Juan" value={form.first_name}
                onChange={e => set('first_name', e.target.value)} required />
            </div>
            <div>
              <label className="label">Apellido *</label>
              <input className="input" placeholder="González" value={form.last_name}
                onChange={e => set('last_name', e.target.value)} required />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Email</label>
              <input className="input" type="email" placeholder="correo@ejemplo.com"
                value={form.email} onChange={e => set('email', e.target.value)} />
            </div>
            <div>
              <label className="label">Teléfono</label>
              <input className="input" placeholder="809-000-0000" value={form.phone}
                onChange={e => set('phone', e.target.value)} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Fecha de Nacimiento</label>
              <input className="input" type="date" value={form.birth_date}
                onChange={e => set('birth_date', e.target.value)} />
            </div>
            <div>
              <label className="label">Género</label>
              <select className="input" value={form.gender} onChange={e => set('gender', e.target.value)}>
                <option value="">Seleccionar</option>
                <option value="male">Masculino</option>
                <option value="female">Femenino</option>
                <option value="other">Otro</option>
              </select>
            </div>
          </div>

          <div>
            <label className="label">Dirección</label>
            <input className="input" placeholder="Calle, Ciudad" value={form.address}
              onChange={e => set('address', e.target.value)} />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Contacto de Emergencia</label>
              <input className="input" placeholder="Nombre" value={form.emergency_contact}
                onChange={e => set('emergency_contact', e.target.value)} />
            </div>
            <div>
              <label className="label">Teléfono Emergencia</label>
              <input className="input" placeholder="809-000-0000" value={form.emergency_phone}
                onChange={e => set('emergency_phone', e.target.value)} />
            </div>
          </div>

          <div>
            <label className="label">Notas</label>
            <textarea className="input h-20 resize-none" placeholder="Observaciones médicas, etc."
              value={form.notes} onChange={e => set('notes', e.target.value)} />
          </div>

          <div className="flex gap-3 pt-2">
            <button type="button" className="btn-secondary flex-1" onClick={onClose} disabled={saving}>
              Cancelar
            </button>
            <button type="submit" className="btn-primary flex-1" disabled={saving}>
              {saving
                ? <span className="flex items-center justify-center gap-2">
                    <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                    Guardando...
                  </span>
                : editing ? 'Guardar Cambios' : 'Crear Miembro'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
