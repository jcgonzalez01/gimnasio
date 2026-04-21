import { useEffect, useState } from 'react'
import { devicesApi } from '../services/api'
import type { HikvisionDevice } from '../types'
import { Plus, Wifi, WifiOff, DoorOpen, Trash2, RefreshCw, Bug, Radio, ChevronDown, ChevronUp, Users, Bell } from 'lucide-react'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

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
  const [eventServerPort, setEventServerPort] = useState('8000')
  const [eventSlot, setEventSlot] = useState('1')
  const [savingEvents, setSavingEvents] = useState(false)
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
        // Mostrar respuesta real del dispositivo para depuración
        const detail = res.data.response
          ? `HTTP ${res.data.status}: ${res.data.response}`
          : res.data.error ?? 'Sin respuesta del dispositivo'
        toast.error(`❌ ${device.name}: ${detail}`, { duration: 8000 })
        console.error('open-door response:', res.data)
      }
    } catch (err: any) {
      toast.error(`Error: ${err?.response?.data?.detail ?? err?.message ?? 'desconocido'}`)
    }
  }

  const deleteDevice = async (device: HikvisionDevice) => {
    if (!confirm(`¿Eliminar dispositivo "${device.name}"?`)) return
    try {
      await devicesApi.delete(device.id)
      toast.success('Dispositivo eliminado')
      load()
    } catch {
      toast.error('Error al eliminar')
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
    if (!confirm(`¿Sincronizar TODOS los miembros al dispositivo "${device.name}"?\n\nEsto registrará a cada miembro en el dispositivo (sin acceso si no tienen membresía activa).`)) return
    setSyncing(device.id)
    toast(`👥 Sincronizando miembros en ${device.name}…`, { duration: 4000 })
    try {
      const res = await devicesApi.syncMembers(device.id)
      setSyncReport(res.data)
      const { ok, failed, total } = res.data
      if (failed === 0) {
        toast.success(`✅ ${ok}/${total} miembros sincronizados en ${device.name}`)
      } else {
        toast.error(`⚠️ ${ok} OK · ${failed} fallaron en ${device.name}`, { duration: 6000 })
      }
    } catch (err: any) {
      toast.error('Error al sincronizar: ' + (err?.response?.data?.detail ?? err?.message ?? ''))
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
        toast.success(`✅ Eventos configurados — el dispositivo enviará accesos a http://${eventServerIp}:${eventServerPort}/api/access/hikvision-webhook`)
        setConfiguringEvents(null)
      } else {
        toast.error(`Error HTTP ${res.data.status}: ${res.data.body?.slice(0, 120)}`, { duration: 8000 })
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Error al configurar')
    } finally {
      setSavingEvents(false)
    }
  }

  const runCommsLog = async (device: HikvisionDevice) => {
    setCommsLoading(device.id)
    setExpandedEntry(null)
    const memberId = commsMemberId ? parseInt(commsMemberId) : undefined
    const note = memberId ? ` (foto miembro #${memberId})` : ' (imagen sintética)'
    toast(`📡 Ejecutando diagnóstico completo${note}… puede tardar 20–30s`, { duration: 5000 })
    try {
      const res = await devicesApi.commsLog(device.id, memberId)
      setCommsReport(res.data)
    } catch (err: any) {
      toast.error('Error al obtener log: ' + (err?.response?.data?.detail ?? err?.message ?? ''))
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

      {/* Info ISAPI */}
      <div className="p-4 bg-blue-50 rounded-xl border border-blue-100 text-sm text-blue-700">
        <p className="font-medium mb-1">Configuración requerida en el dispositivo Hikvision:</p>
        <ul className="list-disc list-inside space-y-0.5 text-blue-600">
          <li>Activar ISAPI: Configuration → Network → Advanced → Integration Protocol → ISAPI</li>
          <li>Para recibir eventos en tiempo real: configurar el webhook a <code className="bg-blue-100 px-1 rounded">http://[IP_SERVIDOR]/api/access/hikvision-webhook</code></li>
          <li>Crear una librería facial (Face Library) con el mismo ID configurado abajo</li>
        </ul>
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
                  {d.is_active ? (
                    <Wifi size={16} className="text-green-500" />
                  ) : (
                    <WifiOff size={16} className="text-gray-400" />
                  )}
                  <h3 className="font-semibold text-gray-800">{d.name}</h3>
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  {d.ip_address}:{d.port} · {d.username}
                </p>
                {d.location && (
                  <p className="text-xs text-gray-400">📍 {d.location}</p>
                )}
                <div className="flex gap-2 mt-2 text-xs text-gray-400">
                  <span className="bg-gray-50 px-2 py-0.5 rounded">
                    {d.device_type === 'access_control' ? 'Control Acceso' : 'Cámara'}
                  </span>
                  <span className="bg-gray-50 px-2 py-0.5 rounded">
                    {d.direction === 'in' ? 'Entrada' : d.direction === 'out' ? 'Salida' : 'Entrada/Salida'}
                  </span>
                  <span className="bg-gray-50 px-2 py-0.5 rounded">FaceLib: {d.face_lib_id}</span>
                </div>
                {d.model && (
                  <p className="text-xs text-gray-400 mt-1">
                    {d.model} {d.firmware && `· fw: ${d.firmware}`}
                  </p>
                )}
                {d.last_heartbeat && (
                  <p className="text-xs text-green-500 mt-1">
                    Último contacto: {format(new Date(d.last_heartbeat), 'dd/MM/yy HH:mm')}
                  </p>
                )}
              </div>

              <div className="flex flex-col gap-1 items-end">
                <div className="flex gap-1">
                  <button
                    onClick={() => testDevice(d)}
                    disabled={testing === d.id}
                    title="Probar conexión"
                    className="p-2 text-gray-400 hover:text-blue-600 rounded-lg hover:bg-blue-50 transition-colors">
                    <RefreshCw size={14} className={testing === d.id ? 'animate-spin' : ''} />
                  </button>
                  {d.device_type === 'access_control' && (
                    <button
                      onClick={() => openDoor(d)}
                      title="Abrir puerta"
                      className="p-2 text-gray-400 hover:text-green-600 rounded-lg hover:bg-green-50 transition-colors">
                      <DoorOpen size={14} />
                    </button>
                  )}
                  <button
                    onClick={() => runDebug(d)}
                    disabled={debugging === d.id}
                    title="Diagnóstico de puerta"
                    className="p-2 text-gray-400 hover:text-orange-500 rounded-lg hover:bg-orange-50 transition-colors">
                    <Bug size={14} className={debugging === d.id ? 'animate-pulse' : ''} />
                  </button>
                  <button
                    onClick={() => runSyncMembers(d)}
                    disabled={syncing === d.id}
                    title="Sincronizar todos los miembros al dispositivo"
                    className="p-2 text-gray-400 hover:text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors">
                    <Users size={14} className={syncing === d.id ? 'animate-pulse text-indigo-500' : ''} />
                  </button>
                  <button
                    onClick={() => runCommsLog(d)}
                    disabled={commsLoading === d.id}
                    title="Log de comunicación — agrega ID de miembro abajo para usar foto real"
                    className="p-2 text-gray-400 hover:text-purple-600 rounded-lg hover:bg-purple-50 transition-colors">
                    <Radio size={14} className={commsLoading === d.id ? 'animate-pulse text-purple-500' : ''} />
                  </button>
                  <button
                    onClick={() => { setConfiguringEvents(d); setEventServerIp('') }}
                    title="Configurar eventos en tiempo real (HTTP push)"
                    className="p-2 text-gray-400 hover:text-yellow-600 rounded-lg hover:bg-yellow-50 transition-colors">
                    <Bell size={14} />
                  </button>
                  <button
                    onClick={() => deleteDevice(d)}
                    title="Eliminar"
                    className="p-2 text-gray-400 hover:text-red-600 rounded-lg hover:bg-red-50 transition-colors">
                    <Trash2 size={14} />
                  </button>
                </div>
                {/* Input de miembro para diagnóstico 📡 */}
                <div className="flex items-center gap-1.5">
                  <input
                    type="number"
                    placeholder="ID miembro (📡)"
                    value={commsMemberId}
                    onChange={e => setCommsMemberId(e.target.value)}
                    className="w-36 text-xs border border-gray-200 rounded px-2 py-1 text-gray-500
                               focus:outline-none focus:border-purple-400 focus:text-gray-700"
                    min="1"
                  />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* ── Modal: Resultado de sincronización de miembros ──────────────────── */}
      {syncReport && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <div>
                <h2 className="font-semibold flex items-center gap-2">
                  <Users size={16} className="text-indigo-500" />
                  Sincronización: {syncReport.device}
                </h2>
                <p className="text-sm text-gray-500 mt-0.5">
                  <span className="text-green-600 font-medium">{syncReport.ok} OK</span>
                  {syncReport.failed > 0 && (
                    <span className="text-red-500 font-medium ml-2">{syncReport.failed} fallaron</span>
                  )}
                  <span className="text-gray-400 ml-2">· {syncReport.total} total</span>
                </p>
              </div>
              <button onClick={() => setSyncReport(null)}
                className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
            </div>
            <div className="overflow-y-auto flex-1 p-4 space-y-2">
              {syncReport.results.map((r, i) => (
                <div key={i} className={`flex items-center justify-between px-3 py-2 rounded-lg border text-sm ${
                  r.registered ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-100'
                }`}>
                  <div className="flex items-center gap-3">
                    <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
                      r.registered ? 'bg-green-200 text-green-700' : 'bg-red-200 text-red-700'
                    }`}>
                      {r.registered ? '✓' : '✗'}
                    </span>
                    <div>
                      <p className="font-medium text-gray-800">{r.name}</p>
                      <p className="text-xs text-gray-400">{r.member_no} · ID: {r.member_id}</p>
                    </div>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    r.has_access
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-gray-100 text-gray-500'
                  }`}>
                    {r.has_access ? '🔓 Con acceso' : '🔒 Sin membresía'}
                  </span>
                </div>
              ))}
            </div>
            <div className="px-6 py-3 border-t bg-gray-50 rounded-b-xl">
              <p className="text-xs text-gray-400">
                Los miembros con membresía activa se registraron con acceso habilitado.
                Los demás se registraron bloqueados hasta asignarles una membresía.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Modal de diagnóstico */}
      {debugReport && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <div>
                <h2 className="font-semibold flex items-center gap-2">
                  <Bug size={16} className="text-orange-500" /> Diagnóstico: {debugReport.device}
                </h2>
                <p className="text-xs text-gray-400 mt-0.5 font-mono">{debugReport.url}</p>
              </div>
              <button onClick={() => setDebugReport(null)} className="text-gray-400 hover:text-gray-600 text-xl">✕</button>
            </div>
            <div className="p-6 space-y-3">
              <p className="text-sm font-medium text-gray-600">Intentos de apertura (en orden):</p>
              {debugReport.results.map((r, i) => (
                <div key={i} className={`p-3 rounded-lg border text-sm font-mono ${
                  r.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-100'
                }`}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-gray-700">{i + 1}. {r.label}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      r.success ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}>
                      {r.success ? '✓ OK' : `HTTP ${r.status ?? 'ERR'}`}
                    </span>
                  </div>
                  {r.body && <p className="text-xs text-gray-600 break-all">{r.body}</p>}
                  {r.error && <p className="text-xs text-red-600">{r.error}</p>}
                </div>
              ))}
              {debugReport.capabilities && (
                <div className="mt-4">
                  <p className="text-sm font-medium text-gray-600 mb-1">Capabilities del dispositivo:</p>
                  <pre className="text-xs bg-gray-50 border rounded p-3 overflow-x-auto whitespace-pre-wrap break-all">
                    {debugReport.capabilities}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── Modal: Log de comunicación completo ──────────────────────────────── */}
      {commsReport && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-950 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-3 border-b border-gray-800">
              <div>
                <h2 className="font-semibold text-white flex items-center gap-2">
                  <Radio size={16} className="text-purple-400" />
                  Comunicación: <span className="text-purple-300">{commsReport.device}</span>
                </h2>
                <p className="text-xs text-gray-500 mt-0.5 font-mono">
                  {commsReport.ip}:{commsReport.port} · {commsReport.timestamp.slice(0,19).replace('T',' ')} UTC
                </p>
                <div className="flex flex-wrap gap-2 mt-1">
                  {commsReport.real_libs?.map(lib => (
                    <span key={lib.FDID}
                      className="text-[10px] px-2 py-0.5 rounded-full bg-purple-900 text-purple-300 font-mono">
                      FDID={lib.FDID} · {lib.faceLibType}
                    </span>
                  ))}
                  {commsReport.using_real_photo ? (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-green-900 text-green-300 font-mono">
                      📸 Foto real · miembro #{commsReport.test_member_id}
                    </span>
                  ) : (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-yellow-900 text-yellow-300 font-mono">
                      ⚠️ Imagen sintética (sin cara)
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-400">
                  {commsReport.log.filter(e => e.ok).length}/{commsReport.log.length} OK
                </span>
                <button onClick={() => setCommsReport(null)}
                  className="text-gray-500 hover:text-white text-xl leading-none">✕</button>
              </div>
            </div>

            {/* Log entries */}
            <div className="overflow-y-auto flex-1 p-3 space-y-2 font-mono text-xs">
              {commsReport.log.map((entry, i) => {
                const expanded = expandedEntry === i
                const statusColor = entry.ok
                  ? 'text-green-400'
                  : entry.status && entry.status >= 400
                    ? 'text-red-400'
                    : entry.status
                      ? 'text-yellow-400'
                      : 'text-red-500'
                const borderColor = entry.ok
                  ? 'border-green-800'
                  : entry.status && entry.status >= 400
                    ? 'border-red-900'
                    : 'border-gray-800'

                return (
                  <div key={i}
                    className={`rounded-lg border ${borderColor} bg-gray-900 overflow-hidden`}>
                    {/* Row header */}
                    <button
                      className="w-full flex items-center gap-3 px-3 py-2 hover:bg-gray-800 transition-colors text-left"
                      onClick={() => setExpandedEntry(expanded ? null : i)}>
                      {/* Step number */}
                      <span className="text-gray-600 w-4 shrink-0">{i + 1}</span>
                      {/* Method badge */}
                      <span className={`shrink-0 px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        entry.method === 'GET'    ? 'bg-blue-900 text-blue-300' :
                        entry.method === 'POST'   ? 'bg-green-900 text-green-300' :
                        entry.method === 'PUT'    ? 'bg-yellow-900 text-yellow-300' :
                        'bg-red-900 text-red-300'
                      }`}>{entry.method}</span>
                      {/* Label */}
                      <span className="text-gray-200 flex-1 truncate">{entry.label}</span>
                      {/* Status */}
                      <span className={`shrink-0 font-bold ${statusColor}`}>
                        {entry.status ?? 'ERR'}
                      </span>
                      {/* Latency */}
                      <span className="shrink-0 text-gray-600 w-16 text-right">{entry.ms}ms</span>
                      {/* Expand icon */}
                      {expanded
                        ? <ChevronUp size={12} className="text-gray-500 shrink-0" />
                        : <ChevronDown size={12} className="text-gray-500 shrink-0" />}
                    </button>

                    {/* Expanded detail */}
                    {expanded && (
                      <div className="border-t border-gray-800 px-3 py-3 space-y-2">
                        <div>
                          <p className="text-gray-500 mb-1">URL</p>
                          <p className="text-blue-300 break-all">{entry.url}</p>
                        </div>
                        {entry.req_body && (
                          <div>
                            <p className="text-gray-500 mb-1">REQUEST BODY</p>
                            <pre className="bg-gray-800 rounded p-2 text-gray-300 overflow-x-auto whitespace-pre-wrap break-all text-[11px]">
                              {(() => {
                                try { return JSON.stringify(JSON.parse(entry.req_body), null, 2) }
                                catch { return entry.req_body }
                              })()}
                            </pre>
                          </div>
                        )}
                        <div>
                          <p className={`mb-1 ${entry.ok ? 'text-green-500' : 'text-red-500'}`}>
                            RESPONSE {entry.status ?? 'ERROR'}
                          </p>
                          <pre className={`rounded p-2 overflow-x-auto whitespace-pre-wrap break-all text-[11px] ${
                            entry.ok ? 'bg-green-950 text-green-300' : 'bg-red-950 text-red-300'
                          }`}>
                            {(() => {
                              try { return JSON.stringify(JSON.parse(entry.res_body), null, 2) }
                              catch { return entry.res_body || '(sin respuesta)' }
                            })()}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>

            {/* Footer resumen */}
            <div className="px-5 py-3 border-t border-gray-800 flex flex-wrap gap-3">
              {commsReport.log.map((e, i) => (
                <button key={i}
                  onClick={() => { setExpandedEntry(i); document.querySelector(`[data-entry="${i}"]`)?.scrollIntoView() }}
                  title={e.label}
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    e.ok
                      ? 'bg-green-900 text-green-300'
                      : e.status
                        ? 'bg-red-900 text-red-300'
                        : 'bg-gray-800 text-gray-500'
                  }`}>
                  {i + 1} {e.status ?? '!'}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Modal: Configurar eventos en tiempo real ──────────────────────────── */}
      {configuringEvents && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="font-semibold flex items-center gap-2">
                <Bell size={16} className="text-yellow-500" />
                Eventos en Tiempo Real — {configuringEvents.name}
              </h2>
              <button onClick={() => setConfiguringEvents(null)}
                className="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <div className="p-6 space-y-5">
              <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200 text-sm text-yellow-800">
                <p className="font-medium mb-1">¿Qué hace esto?</p>
                <p>Configura el dispositivo Hikvision para enviar automáticamente cada evento de acceso (cara, tarjeta) al backend. No necesitas polling — el dispositivo avisa solo.</p>
              </div>

              <div>
                <label className="label">IP de esta PC en tu red local *</label>
                <input
                  className="input"
                  placeholder="Ej: 192.168.1.10"
                  value={eventServerIp}
                  onChange={e => setEventServerIp(e.target.value)}
                />
                <p className="text-xs text-gray-400 mt-1">
                  Ejecuta <code className="bg-gray-100 px-1 rounded">ipconfig</code> (Windows) para ver tu IPv4 local
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Puerto del backend</label>
                  <input
                    className="input"
                    type="number"
                    value={eventServerPort}
                    onChange={e => setEventServerPort(e.target.value)}
                  />
                </div>
                <div>
                  <label className="label">Ranura (1–8)</label>
                  <input
                    className="input"
                    type="number"
                    min={1} max={8}
                    value={eventSlot}
                    onChange={e => setEventSlot(e.target.value)}
                  />
                </div>
              </div>

              {eventServerIp && (
                <div className="p-3 bg-gray-50 rounded-lg border text-xs text-gray-500">
                  El dispositivo enviará eventos a:<br />
                  <code className="text-blue-600 font-medium">
                    http://{eventServerIp}:{eventServerPort}/api/access/hikvision-webhook
                  </code>
                </div>
              )}

              <div className="flex gap-3">
                <button className="btn-secondary flex-1"
                  onClick={() => setConfiguringEvents(null)}>
                  Cancelar
                </button>
                <button
                  className="btn-primary flex-1 flex items-center justify-center gap-2"
                  disabled={!eventServerIp || savingEvents}
                  onClick={saveEventConfig}>
                  {savingEvents
                    ? <><span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" /> Configurando...</>
                    : <><Bell size={14} /> Configurar dispositivo</>}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="font-semibold">Agregar Dispositivo Hikvision</h2>
              <button onClick={() => setShowForm(false)} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <form onSubmit={submit} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="label">Nombre del Dispositivo *</label>
                  <input className="input" placeholder="Ej: Entrada Principal"
                    value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required />
                </div>
                <div>
                  <label className="label">IP / Host *</label>
                  <input className="input" placeholder="192.168.1.100"
                    value={form.ip_address} onChange={e => setForm(f => ({ ...f, ip_address: e.target.value }))} required />
                </div>
                <div>
                  <label className="label">Puerto</label>
                  <input type="number" className="input" value={form.port}
                    onChange={e => setForm(f => ({ ...f, port: e.target.value }))} />
                </div>
                <div>
                  <label className="label">Usuario</label>
                  <input className="input" value={form.username}
                    onChange={e => setForm(f => ({ ...f, username: e.target.value }))} />
                </div>
                <div>
                  <label className="label">Contraseña *</label>
                  <input type="password" className="input" value={form.password}
                    onChange={e => setForm(f => ({ ...f, password: e.target.value }))} required />
                </div>
                <div>
                  <label className="label">Tipo</label>
                  <select className="input" value={form.device_type}
                    onChange={e => setForm(f => ({ ...f, device_type: e.target.value }))}>
                    <option value="access_control">Control de Acceso</option>
                    <option value="camera">Cámara</option>
                  </select>
                </div>
                <div>
                  <label className="label">Dirección</label>
                  <select className="input" value={form.direction}
                    onChange={e => setForm(f => ({ ...f, direction: e.target.value }))}>
                    <option value="both">Entrada y Salida</option>
                    <option value="in">Solo Entrada</option>
                    <option value="out">Solo Salida</option>
                  </select>
                </div>
                <div>
                  <label className="label">Ubicación</label>
                  <input className="input" placeholder="Ej: Puerta Norte"
                    value={form.location} onChange={e => setForm(f => ({ ...f, location: e.target.value }))} />
                </div>
                <div>
                  <label className="label">ID Librería Facial</label>
                  <input className="input" value={form.face_lib_id}
                    onChange={e => setForm(f => ({ ...f, face_lib_id: e.target.value }))} />
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
    </div>
  )
}
