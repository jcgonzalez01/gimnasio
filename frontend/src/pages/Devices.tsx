import { useEffect, useState } from 'react'
import { devicesApi } from '../services/api'
import type { HikvisionDevice } from '../types'
import { Plus, Wifi, WifiOff, DoorOpen, Trash2, RefreshCw, Bug, Radio, ChevronDown, ChevronUp, Users, Bell } from 'lucide-react'
import { format } from 'date-fns'
import toast from 'react-hot-toast'
import DeleteConfirmationModal from '../components/DeleteConfirmationModal'

interface DebugResult {
  label: string; status?: number; body?: string; error?: string; success: boolean
}
interface DebugReport {
  device: string; url: string; results: DebugResult[]; capabilities: string
}

interface SyncResult {
  member_id: number; member_no: string; name: string
  has_access: boolean; registered: boolean
}
interface SyncReport {
  device: string; total: number; ok: number; failed: number; results: SyncResult[]
}

interface CommEntry {
  label: string
  method: string
  url: string
  req_body: string
  status: number | null
  res_body: string
  ms: number
  ok: boolean
}
interface RealLib { FDID: string; faceLibType: string }
interface CommsReport {
  device: string; ip: string; port: number; face_lib: string
  real_libs: RealLib[]
  using_real_photo: boolean
  test_member_id: number | null
  log: CommEntry[]
  timestamp: string
}

export default function Devices() {
  const [devices, setDevices] = useState<HikvisionDevice[]>([])
  const [showForm, setShowForm] = useState(false)
  const [debugReport, setDebugReport] = useState<DebugReport | null>(null)
  const [debugging, setDebugging] = useState<number | null>(null)
  const [testing, setTesting] = useState<number | null>(null)
  const [commsReport, setCommsReport] = useState<CommsReport | null>(null)
  const [commsLoading, setCommsLoading] = useState<number | null>(null)
  const [expandedEntry, setExpandedEntry] = useState<number | null>(null)
  const [commsMemberId, setCommsMemberId] = useState<string>('')
  const [syncReport, setSyncReport] = useState<SyncReport | null>(null)
  const [syncing, setSyncing] = useState<number | null>(null)
  const [configuringEvents, setConfiguringEvents] = useState<HikvisionDevice | null>(null)
  const [eventServerIp, setEventServerIp] = useState('')
  const [eventServerPort, setEventServerPort] = useState('8001')
  const [eventSlot, setEventSlot] = useState('1')
  const [savingEvents, setSavingEvents] = useState(false)

  // Estado para borrado
  const [deleteModal, setDeleteModal] = useState<{
    isOpen: boolean;
    device: HikvisionDevice | null;
    impact?: any;
    loading: boolean;
  }>({
    isOpen: false,
    device: null,
    loading: false
  })

  const [form, setForm] = useState({
    name: '', ip_address: '', port: '80', username: 'admin',
    password: '', device_type: 'access_control', location: '',
    direction: 'both', face_lib_id: '1',
  })

  const load = () => devicesApi.list().then(r => setDevices(r.data))
  useEffect(() => { load() }, [])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await devicesApi.create({
        ...form,
        port: parseInt(form.port),
      })
      toast.success('Dispositivo agregado')
      setShowForm(false)
      setForm({ name: '', ip_address: '', port: '80', username: 'admin', password: '', device_type: 'access_control', location: '', direction: 'both', face_lib_id: '1' })
      load()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Error al guardar')
    }
  }

  const testDevice = async (device: HikvisionDevice) => {
    setTesting(device.id)
    try {
      const res = await devicesApi.test(device.id)
      if (res.data.status === 'online') {
        toast.success(`✅ ${device.name} — Online · Modelo: ${res.data.info?.model || '?'}`)
      } else {
        toast.error(`❌ ${device.name} — Sin respuesta`)
      }
      load()
    } catch {
      toast.error('Error al conectar')
    } finally {
      setTesting(null)
    }
  }

  const openDoor = async (device: HikvisionDevice) => {
    try {
      const res = await devicesApi.openDoor(device.id)
      if (res.data.success) {
        toast.success(`🚪 Puerta abierta — ${device.name}`)
      } else {
        const detail = res.data.response
          ? `HTTP ${res.data.status}: ${res.data.response}`
          : res.data.error ?? 'Sin respuesta del dispositivo'
        toast.error(`❌ ${device.name}: ${detail}`, { duration: 8000 })
      }
    } catch (err: any) {
      toast.error(`Error: ${err?.response?.data?.detail ?? err?.message ?? 'desconocido'}`)
    }
  }

  const handleDeleteClick = (device: HikvisionDevice) => {
    setDeleteModal({
      isOpen: true,
      device: device,
      loading: false
    })
  }

  const confirmDelete = async (force: boolean) => {
    if (!deleteModal.device) return
    setDeleteModal(prev => ({ ...prev, loading: true }))
    try {
      await devicesApi.delete(deleteModal.device.id, force)
      toast.success('Dispositivo eliminado')
      setDeleteModal({ isOpen: false, device: null, loading: false })
      load()
    } catch (err: any) {
      if (err.response?.status === 409) {
        setDeleteModal(prev => ({
          ...prev,
          loading: false,
          impact: err.response.data.requires_force ? err.response.data : { history: true, detail: err.response.data.detail, items: [] }
        }))
      } else {
        toast.error('Error al eliminar')
        setDeleteModal(prev => ({ ...prev, loading: false }))
      }
    }
  }

  const runDebug = async (device: HikvisionDevice) => {
    setDebugging(device.id)
    try {
      const res = await devicesApi.debugDoor(device.id)
      setDebugReport(res.data)
    } catch (err: any) {
      toast.error('Error en debug: ' + (err?.message ?? ''))
    } finally {
      setDebugging(null)
    }
  }

  const runSyncMembers = async (device: HikvisionDevice) => {
    if (!confirm(`¿Sincronizar TODOS los miembros al dispositivo "${device.name}"?`)) return
    setSyncing(device.id)
    try {
      const res = await devicesApi.syncMembers(device.id)
      setSyncReport(res.data)
      toast.success(`Sincronización finalizada en ${device.name}`)
    } catch (err: any) {
      toast.error('Error al sincronizar')
    } finally {
      setSyncing(null)
    }
  }

  const saveEventConfig = async () => {
    if (!configuringEvents || !eventServerIp) return
    setSavingEvents(true)
    try {
      const res = await devicesApi.configureEvents(
        configuringEvents.id,
        eventServerIp,
        parseInt(eventServerPort) || 8000,
        parseInt(eventSlot) || 1,
      )
      if (res.data.success) {
        toast.success(`✅ Eventos configurados`)
        setConfiguringEvents(null)
      } else {
        toast.error(`Error HTTP ${res.data.status}`)
      }
    } catch (err: any) {
      toast.error('Error al configurar')
    } finally {
      setSavingEvents(false)
    }
  }

  const runCommsLog = async (device: HikvisionDevice) => {
    setCommsLoading(device.id)
    const memberId = commsMemberId ? parseInt(commsMemberId) : undefined
    try {
      const res = await devicesApi.commsLog(device.id, memberId)
      setCommsReport(res.data)
    } catch (err: any) {
      toast.error('Error al obtener log')
    } finally {
      setCommsLoading(null)
    }
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dispositivos Hikvision</h1>
          <p className="text-gray-500 text-sm">Control de acceso · ISAPI</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => setShowForm(true)}>
          <Plus size={16} /> Agregar Dispositivo
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {devices.length === 0 ? (
          <div className="card col-span-2 text-center py-12 text-gray-400">
            Sin dispositivos configurados
          </div>
        ) : devices.map(d => (
          <div key={d.id} className={`card border-l-4 ${d.is_active ? 'border-l-green-400' : 'border-l-gray-200'}`}>
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  {d.is_active ? <Wifi size={16} className="text-green-500" /> : <WifiOff size={16} className="text-gray-400" />}
                  <h3 className="font-semibold text-gray-800">{d.name}</h3>
                </div>
                <p className="text-sm text-gray-500 mt-1">{d.ip_address}:{d.port}</p>
              </div>

              <div className="flex gap-1">
                <button onClick={() => testDevice(d)} disabled={testing === d.id} className="p-2 text-gray-400 hover:text-blue-600 rounded-lg hover:bg-blue-50">
                  <RefreshCw size={14} className={testing === d.id ? 'animate-spin' : ''} />
                </button>
                <button onClick={() => openDoor(d)} className="p-2 text-gray-400 hover:text-green-600 rounded-lg hover:bg-green-50">
                  <DoorOpen size={14} />
                </button>
                <button onClick={() => runDebug(d)} className="p-2 text-gray-400 hover:text-orange-500 rounded-lg hover:bg-orange-50">
                  <Bug size={14} />
                </button>
                <button onClick={() => runSyncMembers(d)} className="p-2 text-gray-400 hover:text-indigo-600 rounded-lg hover:bg-indigo-50">
                  <Users size={14} />
                </button>
                <button onClick={() => runCommsLog(d)} className="p-2 text-gray-400 hover:text-purple-600 rounded-lg hover:bg-purple-50">
                  <Radio size={14} />
                </button>
                <button onClick={() => setConfiguringEvents(d)} className="p-2 text-gray-400 hover:text-yellow-600 rounded-lg hover:bg-yellow-50">
                  <Bell size={14} />
                </button>
                <button onClick={() => handleDeleteClick(d)} className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50">
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="font-semibold">Agregar Dispositivo</h2>
              <button onClick={() => setShowForm(false)} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <form onSubmit={submit} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="label">Nombre *</label>
                  <input className="input" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required />
                </div>
                <div>
                  <label className="label">IP *</label>
                  <input className="input" value={form.ip_address} onChange={e => setForm(f => ({ ...f, ip_address: e.target.value }))} required />
                </div>
                <div>
                  <label className="label">Puerto</label>
                  <input type="number" className="input" value={form.port} onChange={e => setForm(f => ({ ...f, port: e.target.value }))} />
                </div>
                <div>
                  <label className="label">Usuario</label>
                  <input className="input" value={form.username} onChange={e => setForm(f => ({ ...f, username: e.target.value }))} />
                </div>
                <div>
                  <label className="label">Contraseña *</label>
                  <input type="password" className="input" value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} required />
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" className="btn-secondary flex-1" onClick={() => setShowForm(false)}>Cancelar</button>
                <button type="submit" className="btn-primary flex-1">Agregar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <DeleteConfirmationModal
        isOpen={deleteModal.isOpen}
        title="Eliminar Dispositivo"
        message={`¿Estás seguro de que deseas eliminar el dispositivo "${deleteModal.device?.name}"?`}
        impact={deleteModal.impact}
        isLoading={deleteModal.loading}
        onConfirm={confirmDelete}
        onCancel={() => setDeleteModal({ isOpen: false, device: null, loading: false })}
      />
    </div>
  )
}
