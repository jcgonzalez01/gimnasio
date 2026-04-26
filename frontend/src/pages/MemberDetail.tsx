import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { membersApi, plansApi, accessApi, devicesApi, authApi } from '../services/api'
import type { Member, MembershipPlan, AccessLog, HikvisionDevice, AssignMembershipResponse, AuthUser } from '../types'
import {
  ArrowLeft, Camera, ScanFace, ShieldOff, Plus,
  User, Phone, Mail, MapPin, AlertTriangle, MonitorSmartphone,
  CalendarClock, CheckSquare, Square, Receipt, Wifi, WifiOff, CheckCircle2, XCircle, Trash2
} from 'lucide-react'
import { format, addDays } from 'date-fns'
import toast from 'react-hot-toast'

export default function MemberDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [member, setMember] = useState<Member | null>(null)
  const [plans, setPlans] = useState<MembershipPlan[]>([])
  const [logs, setLogs] = useState<AccessLog[]>([])
  const [devices, setDevices] = useState<HikvisionDevice[]>([])
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [showMembershipForm, setShowMembershipForm] = useState(false)
  const [showEnrollForm, setShowEnrollForm] = useState(false)
  const [showReceipt, setShowReceipt] = useState(false)
  const [receipt, setReceipt] = useState<AssignMembershipResponse | null>(null)
  const [enrolling, setEnrolling]         = useState(false)
  const [enrollResult, setEnrollResult]   = useState<any[] | null>(null)
  const [enrollResultTitle, setEnrollResultTitle] = useState('')
  const [assigning, setAssigning]         = useState(false)
  const [capturing, setCapturing]         = useState<number | null>(null)
  const [resettingFace, setResettingFace] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  // Membresía form
  const [memForm, setMemForm] = useState({
    plan_id: 0, payment_method: 'cash', start_date: format(new Date(), 'yyyy-MM-dd')
  })

  // Enrolamiento form
  const today = format(new Date(), 'yyyy-MM-dd')
  const nextYear = format(addDays(new Date(), 365), 'yyyy-MM-dd')
  const [enrollForm, setEnrollForm] = useState({
    begin_date: today,
    end_date: nextYear,
    selectedDevices: [] as number[],   // vacío = todos
  })

  const load = async () => {
    if (!id) return
    setLoading(true)
    console.log('Cargando datos del miembro ID:', id)
    
    try {
      // 1. Cargar datos básicos del miembro (Obligatorio)
      try {
        const mRes = await membersApi.get(Number(id))
        setMember(mRes.data)
      } catch (err) {
        console.error('Error cargando datos básicos del miembro:', err)
        toast.error('No se pudo encontrar al miembro')
        setLoading(false)
        return
      }

      // 2. Cargar el resto de información (Opcional, no detiene la carga si falla algo)
      const results = await Promise.allSettled([
        plansApi.list(),
        accessApi.getLogs({ member_id: Number(id), limit: 20 }),
        devicesApi.list(),
        authApi.me()
      ])

      if (results[0].status === 'fulfilled') setPlans(results[0].value.data)
      else console.error('Error cargando planes:', results[0].reason)

      if (results[1].status === 'fulfilled') setLogs(results[1].value.data)
      else console.error('Error cargando logs:', results[1].reason)

      if (results[2].status === 'fulfilled') {
        const accDev = results[2].value.data.filter(d => d.device_type === 'access_control' && d.is_active)
        setDevices(accDev)
        setEnrollForm(f => ({ ...f, selectedDevices: accDev.map(d => d.id) }))
      } else console.error('Error cargando dispositivos:', results[2].reason)

      if (results[3].status === 'fulfilled') {
        setCurrentUser(results[3].value.data)
        console.log('Usuario cargado:', results[3].value.data.username)
      } else console.error('Error cargando usuario actual:', results[3].reason)

    } catch (err) {
      console.error('Error general en load:', err)
      toast.error('Error al actualizar la vista')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [id])

  // ── Foto desde archivo ──────────────────────────────────────────────────────
  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0] || !member) return
    try {
      await membersApi.uploadPhoto(member.id, e.target.files[0])
      toast.success('Foto actualizada')
      load()
    } catch {
      toast.error('Error al subir foto')
    }
  }

  // ── Foto desde cámara del dispositivo Hikvision ────────────────────────────
  const handleCaptureFromDevice = async (deviceId: number) => {
    if (!member) return
    setCapturing(deviceId)
    try {
      const res = await accessApi.capturePhotoFromDevice(deviceId, member.id)
      toast.success(`📷 Foto capturada desde ${res.data.device}`)
      load()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'No se pudo capturar la foto del dispositivo')
    } finally {
      setCapturing(null)
    }
  }

  // ── Abrir formulario de enrolamiento ───────────────────────────────────
  const openEnrollForm = () => { setShowEnrollForm(true) }

  // ── Un solo paso: Registrar usuario + Subir foto facial ─────────────────
  const handleEnrollBoth = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!member) return
    setEnrolling(true)
    toast('Procesando...')
    try {
      const deviceIds = enrollForm.selectedDevices.length === devices.length
        ? undefined
        : enrollForm.selectedDevices.join(',')

      const beginDate = `${enrollForm.begin_date}T00:00:00`
      const endDate   = `${enrollForm.end_date}T23:59:59`

      console.log('Registrando y enrolando...', { beginDate, endDate, deviceIds })
      const res = await accessApi.registerAndEnroll(member.id, { beginDate, endDate, deviceIds })
      console.log('Resultado:', res.data)

      const results = res.data.results ?? []
      const ok = results.filter((r: any) => r.face_enrolled).length

      if (ok > 0) {
        toast.success(`✅ Listo en ${ok} dispositivo(s)`)
      } else {
        toast.error('Error al procesar')
      }

      setEnrollResultTitle('Resultado')
      setEnrollResult(results)
      setShowEnrollForm(false)
      load()
    } catch (err: any) {
      console.error('Error enrolamiento:', err)
      toast.error(err.response?.data?.detail || 'Error en el proceso')
    } finally {
      setEnrolling(false)
    }
  }

  const handleUnenrollFace = async () => {
    if (!member || !confirm('¿Eliminar datos faciales del miembro?')) return
    try {
      await accessApi.unenrollFace(member.id)
      toast.success('Datos faciales eliminados')
      load()
    } catch {
      toast.error('Error al eliminar datos faciales')
    }
  }

  // Resetea el flag face_enrolled en la BD sin tocar el dispositivo
  const handleResetFaceFlag = async () => {
    if (!member) return
    if (!confirm(
      'Esto solo corrige el indicador en la base de datos.\n' +
      'No elimina datos del dispositivo.\n\n¿Continuar?'
    )) return
    setResettingFace(true)
    try {
      await membersApi.setFaceStatus(member.id, false)
      toast.success('Estado de enrolamiento corregido')
      load()
    } catch {
      toast.error('Error al actualizar estado')
    } finally {
      setResettingFace(false)
    }
  }

  const toggleDevice = (id: number) => {
    setEnrollForm(f => ({
      ...f,
      selectedDevices: f.selectedDevices.includes(id)
        ? f.selectedDevices.filter(d => d !== id)
        : [...f.selectedDevices, id],
    }))
  }

  // ── Membresía ──────────────────────────────────────────────────────────────
  const handleAssignMembership = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!member || !memForm.plan_id) return
    const plan = plans.find(p => p.id === memForm.plan_id)
    if (!plan) return
    const startDate = new Date(memForm.start_date)
    const endDate = addDays(startDate, plan.duration_days)
    setAssigning(true)
    try {
      const res = await membersApi.assignMembership(member.id, {
        member_id: member.id,
        plan_id: plan.id,
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
        price_paid: plan.price,
        payment_method: memForm.payment_method,
      })
      setShowMembershipForm(false)
      setReceipt(res.data)
      setShowReceipt(true)
      load()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Error al asignar membresía')
    } finally {
      setAssigning(false)
    }
  }

  const handleDeleteMembership = async (membershipId: number) => {
    if (!confirm('¿Estás seguro de que deseas eliminar esta membresía? Esta acción no se puede deshacer.')) return
    
    const tid = toast.loading('Eliminando membresía...')
    console.log('Intentando eliminar membresía ID:', membershipId)
    
    try {
      console.log('Llamando a api.delete para membresía:', membershipId)
      const res = await membersApi.deleteMembership(membershipId)
      console.log('Respuesta exitosa del servidor:', res.data)
      toast.success('Membresía eliminada', { id: tid })
      await load()
    } catch (err: any) {
      console.error('Error detallado al eliminar membresía:', {
        status: err.response?.status,
        data: err.response?.data,
        url: err.config?.url,
        method: err.config?.method,
        membershipId
      })
      const msg = err.response?.data?.detail || 'Error al eliminar membresía'
      toast.error(msg, { id: tid })
    }
  }

  if (loading) return (
    <div className="p-8 flex justify-center">
      <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full" />
    </div>
  )
  if (!member) return <div className="p-8 text-gray-500">Miembro no encontrado</div>

  const activeMem = member.memberships.find(
    m => m.is_active && new Date(m.start_date) <= new Date() && new Date(m.end_date) >= new Date()
  )

  const canDeleteMembership = currentUser?.role === 'admin' || currentUser?.role === 'manager'

  return (
    <div className="p-8 space-y-6 max-w-4xl">
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/members')} className="btn-secondary flex items-center gap-2">
          <ArrowLeft size={16} /> Volver
        </button>
        <h1 className="text-2xl font-bold">{member.first_name} {member.last_name}</h1>
        <span className={`badge-${member.status}`}>{member.status}</span>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Columna izquierda: foto + acciones */}
        <div className="space-y-3">
          <div className="card text-center space-y-3">
            {/* Foto */}
            <div className="relative inline-block">
              {member.photo_path ? (
                <img src={member.photo_path} alt=""
                  className="w-32 h-32 rounded-full object-cover border-4 border-gray-100 mx-auto" />
              ) : (
                <div className="w-32 h-32 rounded-full bg-gray-100 flex items-center justify-center mx-auto border-4 border-gray-100">
                  <User size={40} className="text-gray-300" />
                </div>
              )}
            </div>
            <div>
              <p className="font-bold text-lg">{member.first_name} {member.last_name}</p>
              <p className="text-gray-400 text-sm">{member.member_number}</p>
              {member.hikvision_card_no && (
                <p className="text-xs text-blue-500 font-mono mt-0.5">
                  🔑 ID Hikvision: {member.hikvision_card_no}
                </p>
              )}
            </div>

            {/* Subir foto desde archivo */}
            <input ref={fileRef} type="file" accept="image/*" className="hidden"
              onChange={handlePhotoUpload} />
            <button className="btn-secondary w-full flex items-center justify-center gap-2 text-sm"
              onClick={() => fileRef.current?.click()}>
              <Camera size={14} /> Subir Foto
            </button>

            {/* Capturar desde dispositivo */}
            {devices.length > 0 && (
              <div className="space-y-1">
                <p className="text-xs text-gray-400 font-medium text-left">Capturar desde dispositivo:</p>
                {devices.map(d => (
                  <button key={d.id}
                    onClick={() => handleCaptureFromDevice(d.id)}
                    disabled={capturing === d.id}
                    className="w-full flex items-center gap-2 text-xs px-3 py-2 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors text-left">
                    <MonitorSmartphone size={13} className="text-blue-500 shrink-0" />
                    <span className="truncate">{d.name}</span>
                    {capturing === d.id && (
                      <span className="ml-auto text-blue-400 text-[10px]">Capturando...</span>
                    )}
                  </button>
                ))}
              </div>
            )}

            {/* ── Acceso Hikvision — flujo en 2 pasos ── */}
            <div className="space-y-2 pt-1 border-t border-gray-100">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                Acceso Facial
              </p>

              {/* Estado único de enrolamiento */}
              <div className={`rounded-lg border px-3 py-2 text-xs flex items-center gap-2 ${
                member.hikvision_card_no && member.face_enrolled
                  ? 'border-green-200 bg-green-50 text-green-700'
                  : member.hikvision_card_no
                    ? 'border-orange-200 bg-orange-50 text-orange-700'
                    : 'border-gray-200 bg-gray-50 text-gray-400'
              }`}>
                {member.hikvision_card_no && member.face_enrolled ? (
                  <><CheckCircle2 size={13} className="text-green-500 shrink-0" /> Completo</>
                ) : member.hikvision_card_no ? (
                  <><XCircle size={13} className="text-orange-500 shrink-0" /> Sin foto</>
                ) : (
                  <><XCircle size={13} className="text-gray-300 shrink-0" /> No registrado</>
                )}
              </div>

              <button
                className={`btn-primary w-full flex items-center justify-center gap-2 text-sm ${
                  !member.photo_path ? 'opacity-50 cursor-not-allowed' : ''
                }`}
                onClick={openEnrollForm}
                disabled={!member.photo_path}
                title={!member.photo_path ? 'El miembro no tiene foto' : ''}>
                <ScanFace size={14} />
                {member.hikvision_card_no && member.face_enrolled
                  ? 'Actualizar en dispositivo'
                  : member.hikvision_card_no
                    ? 'Registrar + Subir foto'
                    : 'Registrar en dispositivo'}
              </button>

              {/* Eliminar / corregir */}
              {(member.hikvision_card_no || member.face_enrolled) && (
                <div className="space-y-1 pt-1 border-t border-gray-100">
                  <button
                    className="btn-danger w-full flex items-center justify-center gap-1.5 text-sm"
                    onClick={handleUnenrollFace}>
                    <ShieldOff size={13} /> Eliminar datos del dispositivo
                  </button>
                  <button
                    disabled={resettingFace}
                    className="w-full flex items-center justify-center gap-1.5 text-xs py-1.5 px-3 rounded-lg border border-orange-200 text-orange-600 hover:bg-orange-50 transition-colors"
                    onClick={handleResetFaceFlag}
                    title="Corrige el indicador en BD sin tocar el dispositivo">
                    {resettingFace
                      ? <span className="animate-spin w-3 h-3 border-2 border-orange-400 border-t-transparent rounded-full" />
                      : '⚠️'}
                    Corregir estado en BD
                  </button>
                </div>
              )}

              {!member.photo_path && (
                <p className="text-xs text-orange-500 flex items-center gap-1">
                  <AlertTriangle size={12} /> Sube una foto para poder enviarla al dispositivo
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Columna derecha: info + membresía */}
        <div className="col-span-2 space-y-4">
          <div className="card space-y-3">
            <h3 className="font-semibold text-gray-700">Información de Contacto</h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              {member.email && (
                <div className="flex items-center gap-2 text-gray-600">
                  <Mail size={14} className="text-gray-400" />
                  {member.email}
                </div>
              )}
              {member.phone && (
                <div className="flex items-center gap-2 text-gray-600">
                  <Phone size={14} className="text-gray-400" />
                  {member.phone}
                </div>
              )}
              {member.address && (
                <div className="flex items-center gap-2 text-gray-600 col-span-2">
                  <MapPin size={14} className="text-gray-400" />
                  {member.address}
                </div>
              )}
            </div>
            {member.emergency_contact && (
              <div className="pt-2 border-t text-sm">
                <span className="text-gray-500">Emergencia: </span>
                <span className="font-medium">{member.emergency_contact}</span>
                {member.emergency_phone && (
                  <span className="text-gray-400"> · {member.emergency_phone}</span>
                )}
              </div>
            )}
          </div>

          <div className="card">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-700">Membresía</h3>
              <button className="btn-primary flex items-center gap-1.5 text-sm py-1.5"
                onClick={() => setShowMembershipForm(true)}>
                <Plus size={14} /> Asignar
              </button>
            </div>
            {activeMem ? (
              <div className="p-3 bg-green-50 rounded-lg border border-green-100 flex justify-between items-center">
                <div className="flex justify-between items-start flex-1">
                  <div>
                    <p className="font-medium text-green-800">{activeMem.plan?.name}</p>
                    <p className="text-green-600 text-sm">
                      {format(new Date(activeMem.start_date), 'dd/MM/yyyy')} →{' '}
                      {format(new Date(activeMem.end_date), 'dd/MM/yyyy')}
                    </p>
                  </div>
                  <p className="font-bold text-green-700 mr-4">${activeMem.price_paid.toFixed(2)}</p>
                </div>
                {canDeleteMembership && (
                  <button 
                    onClick={() => handleDeleteMembership(activeMem.id)}
                    className="p-1.5 text-red-600 hover:bg-red-100 rounded-lg transition-colors"
                    title="Eliminar membresía"
                  >
                    <Trash2 size={16} />
                  </button>
                )}
              </div>
            ) : (
              <p className="text-gray-400 text-sm">Sin membresía activa</p>
            )}
            {member.memberships.length > (activeMem ? 1 : 0) && (
              <div className="mt-3 space-y-1">
                <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Historial</p>
                {member.memberships
                  .filter(m => !activeMem || m.id !== activeMem.id)
                  .sort((a, b) => new Date(b.end_date).getTime() - new Date(a.end_date).getTime())
                  .slice(0, 3)
                  .map(m => (
                    <div key={m.id} className="flex justify-between items-center text-xs text-gray-500 py-2 border-t">
                      <div className="flex-1">
                        <span className="font-medium">{m.plan?.name}</span>
                        <span className="mx-1">·</span>
                        <span>{format(new Date(m.start_date), 'dd/MM/yy')} → {format(new Date(m.end_date), 'dd/MM/yy')}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold">${m.price_paid.toFixed(2)}</span>
                        {canDeleteMembership && (
                          <button 
                            onClick={() => handleDeleteMembership(m.id)}
                            className="p-1 text-red-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                            title="Eliminar del historial"
                          >
                            <Trash2 size={14} />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Últimos accesos */}
      <div className="card">
        <h3 className="font-semibold text-gray-700 mb-3">Últimos Accesos ({logs.length})</h3>
        {logs.length === 0 ? (
          <p className="text-gray-400 text-sm">Sin registros</p>
        ) : (
          <div className="space-y-1 max-h-48 overflow-y-auto scrollbar-thin">
            {logs.map(log => (
              <div key={log.id}
                className="flex items-center gap-3 text-sm py-1.5 border-b border-gray-50">
                <div className={`w-2 h-2 rounded-full ${log.result === 'granted' ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-gray-500">{format(new Date(log.timestamp), 'dd/MM/yyyy HH:mm')}</span>
                <span className={`text-xs px-1.5 py-0.5 rounded ${
                  log.direction === 'in' ? 'bg-blue-50 text-blue-600' : 'bg-gray-50 text-gray-500'
                }`}>
                  {log.direction === 'in' ? 'Entrada' : 'Salida'}
                </span>
                <span className="text-gray-400">{log.access_type}</span>
                {log.device_name && <span className="text-gray-400 ml-auto">{log.device_name}</span>}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Modal: Resultado detallado de enrolamiento ───────────────────────── */}
      {enrollResult && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-950 rounded-xl shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-800">
              <h2 className="font-semibold text-white flex items-center gap-2">
                <ScanFace size={16} className="text-purple-400" />
                {enrollResultTitle || 'Resultado de Enrolamiento Facial'}
              </h2>
              <button onClick={() => setEnrollResult(null)}
                className="text-gray-500 hover:text-white text-xl">✕</button>
            </div>
            <div className="overflow-y-auto flex-1 p-4 space-y-4 font-mono text-xs">
              {enrollResult.map((r: any, di: number) => (
                <div key={di} className={`rounded-lg border p-3 ${
                  r.face_enrolled ? 'border-green-700 bg-green-950' : 'border-red-900 bg-red-950'
                }`}>
                  <div className="flex items-center gap-2 mb-3">
                    <span className={`font-bold text-sm ${r.face_enrolled ? 'text-green-400' : 'text-red-400'}`}>
                      {r.face_enrolled ? '✓' : '✗'} {r.device}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      r.user_added ? 'bg-blue-900 text-blue-300' : 'bg-gray-800 text-gray-400'
                    }`}>
                      Usuario: {r.user_added ? 'OK' : 'FALLO'}
                    </span>
                    {r.variant && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-green-900 text-green-300">
                        ✓ {r.variant}
                      </span>
                    )}
                  </div>
                  {r.attempts && r.attempts.length > 0 && (
                    <div className="space-y-1">
                      <p className="text-gray-500 mb-1">Intentos ({r.attempts.length}):</p>
                      {r.attempts.map((a: any, ai: number) => (
                        <div key={ai} className={`flex items-start gap-2 px-2 py-1 rounded ${
                          a.ok ? 'bg-green-900/40' : 'bg-gray-900'
                        }`}>
                          <span className={`shrink-0 font-bold ${a.ok ? 'text-green-400' : 'text-red-400'}`}>
                            {a.ok ? '✓' : '✗'}
                          </span>
                          <div className="flex-1 min-w-0">
                            <p className={`${a.ok ? 'text-green-300' : 'text-gray-400'}`}>{a.label}</p>
                            <p className={`break-all mt-0.5 ${a.ok ? 'text-green-500' : 'text-red-400/70'}`}>
                              HTTP {a.status ?? 'ERR'} — {(() => {
                                try { return JSON.stringify(JSON.parse(a.response), null, 0) }
                                catch { return a.response }
                              })()}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  {!r.face_enrolled && !r.attempts?.length && r.error && (
                    <p className="text-red-400 break-all">{r.error}</p>
                  )}
                </div>
              ))}
            </div>
            <div className="px-5 py-3 border-t border-gray-800 text-xs text-gray-500">
              Muestra este resultado al soporte técnico para identificar el método correcto.
            </div>
          </div>
        </div>
      )}

      {/* ── Modal: Registro / Enrolamiento facial ───────────────────────────── */}
      {showEnrollForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="font-semibold flex items-center gap-2">
                <ScanFace size={18} className="text-purple-500" />
                Registrar en dispositivo — {member.first_name}
              </h2>
              <button onClick={() => setShowEnrollForm(false)}
                className="text-gray-400 hover:text-gray-600">✕</button>
            </div>

            <form onSubmit={handleEnrollBoth}
                  className="p-6 space-y-5">

              {/* Vista previa de la foto */}
              {member.photo_path && (
                <div className="flex justify-center">
                  <img src={member.photo_path} alt=""
                    className="w-24 h-24 rounded-full object-cover border-4 border-purple-100" />
                </div>
              )}

              {/* Rango de fechas */}
              <div>
                <label className="label flex items-center gap-1.5">
                  <CalendarClock size={14} className="text-blue-500" />
                  Rango de fechas de acceso
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-gray-500 mb-1 block">Desde</label>
                    <input type="date" className="input" value={enrollForm.begin_date}
                      onChange={e => setEnrollForm(f => ({ ...f, begin_date: e.target.value }))} />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 mb-1 block">Hasta</label>
                    <input type="date" className="input" value={enrollForm.end_date}
                      onChange={e => setEnrollForm(f => ({ ...f, end_date: e.target.value }))} />
                  </div>
                </div>
                {activeMem && (
                  <button type="button"
                    className="text-xs text-blue-600 hover:underline mt-1"
                    onClick={() => setEnrollForm(f => ({
                      ...f,
                      begin_date: format(new Date(activeMem.start_date), 'yyyy-MM-dd'),
                      end_date:   format(new Date(activeMem.end_date),   'yyyy-MM-dd'),
                    }))}>
                    📋 Usar fechas de membresía activa
                  </button>
                )}
              </div>

              {/* Selección de dispositivos */}
              {devices.length > 0 && (
                <div>
                  <label className="label">
                    Dispositivos
                  </label>
                  <div className="space-y-2">
                    {devices.map(d => {
                      const selected = enrollForm.selectedDevices.includes(d.id)
                      return (
                        <button key={d.id} type="button"
                          onClick={() => toggleDevice(d.id)}
                          className={`w-full flex items-center gap-3 p-3 rounded-lg border text-left transition-colors ${
                            selected
                              ? 'border-blue-300 bg-blue-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}>
                          {selected
                            ? <CheckSquare size={16} className="text-blue-600 shrink-0" />
                            : <Square size={16} className="text-gray-300 shrink-0" />}
                          <div>
                            <p className="text-sm font-medium">{d.name}</p>
                            <p className="text-xs text-gray-400">
                              {d.ip_address}:{d.port} · {d.location || d.direction}
                            </p>
                          </div>
                        </button>
                      )
                    })}
                  </div>
                  {enrollForm.selectedDevices.length === 0 && (
                    <p className="text-xs text-orange-500 mt-1">
                      ⚠️ Selecciona al menos un dispositivo
                    </p>
                  )}
                </div>
              )}

              <p className="text-xs text-gray-400 bg-gray-50 rounded-lg p-3">
                ℹ️ Se registrará el usuario y se subirá la foto facial al dispositivo.
              </p>

              <div className="flex gap-3 pt-1">
                <button type="button" className="btn-secondary flex-1"
                  onClick={() => setShowEnrollForm(false)}>
                  Cancelar
                </button>
                <button type="submit" className="btn-primary flex-1"
                  disabled={enrolling || enrollForm.selectedDevices.length === 0}>
                  {enrolling
                    ? 'Registrando...'
                    : `Registrar + Subir foto`}
                </button>
                {member?.has_active_membership && activeMem && devices.length > 0 && (
                  <button type="button" className="btn-primary bg-green-600 hover:bg-green-700 flex-1"
                    disabled={enrolling}
                    onClick={async () => {
                      if (!member || !activeMem) return
                      setEnrolling(true)
                      try {
                        const deviceIds = enrollForm.selectedDevices.length === devices.length
                          ? undefined
                          : enrollForm.selectedDevices.join(',')
                        const beginDate = format(new Date(activeMem.start_date), 'yyyy-MM-dd') + 'T00:00:00'
                        const endDate   = format(new Date(activeMem.end_date), 'yyyy-MM-dd') + 'T23:59:59'
                        const res = await membersApi.updateValidity(member.id, { beginDate, endDate, deviceIds })
                        const results = res.data.results ?? []
                        const ok = results.filter((r: any) => r.updated).length
                        const total = results.length
                        if (ok === total && total > 0) {
                          toast.success(`✅ Fechas actualizadas en ${ok}/${total} dispositivos`)
                        } else if (ok > 0) {
                          toast(`⚠️ Actualizado parcialmente ${ok}/${total}`, { icon: '⚠️' })
                        } else {
                          toast.error('No se pudieron actualizar las fechas')
                        }
                      } catch (err: any) {
                        toast.error(err.response?.data?.detail || 'Error al actualizar fechas')
                      } finally {
                        setEnrolling(false)
                      }
                    }}>
                    🔄 Sincronizar vigencia
                  </button>
                )}
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Modal: Recibo de membresía ───────────────────────────────────────── */}
      {showReceipt && receipt && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
            {/* Encabezado */}
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="font-semibold flex items-center gap-2">
                <Receipt size={18} className="text-green-500" /> Recibo de Membresía
              </h2>
              <button onClick={() => setShowReceipt(false)}
                className="text-gray-400 hover:text-gray-600">✕</button>
            </div>

            <div className="p-6 space-y-4">
              {/* Número de venta */}
              <div className="text-center pb-2 border-b">
                <p className="text-xs text-gray-400 uppercase tracking-widest">Factura</p>
                <p className="text-2xl font-bold font-mono text-gray-800">{receipt.sale_number}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {format(new Date(), 'dd/MM/yyyy HH:mm')}
                </p>
              </div>

              {/* Cliente */}
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Cliente</span>
                <span className="font-medium">{member?.first_name} {member?.last_name}</span>
              </div>

              {/* Plan */}
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Plan</span>
                <span className="font-medium">{receipt.membership.plan?.name}</span>
              </div>

              {/* Período */}
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Período</span>
                <span className="font-medium text-right">
                  {format(new Date(receipt.membership.start_date), 'dd/MM/yyyy')}
                  {' → '}
                  {format(new Date(receipt.membership.end_date), 'dd/MM/yyyy')}
                </span>
              </div>

              {/* Método de pago */}
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Método de pago</span>
                <span className="font-medium capitalize">
                  {receipt.payment_method === 'cash' ? '💵 Efectivo'
                    : receipt.payment_method === 'card' ? '💳 Tarjeta'
                    : '🏦 Transferencia'}
                </span>
              </div>

              {/* Total */}
              <div className="flex justify-between items-center pt-3 border-t">
                <span className="text-gray-700 font-semibold">Total cobrado</span>
                <span className="text-2xl font-bold text-green-600">
                  ${receipt.sale_total.toFixed(2)}
                </span>
              </div>

              {/* Estado de acceso Hikvision */}
              <div className={`rounded-lg p-3 border text-sm ${
                receipt.access_skipped
                  ? 'bg-yellow-50 border-yellow-200'
                  : receipt.access_enrolled
                    ? 'bg-green-50 border-green-200'
                    : receipt.access_results.length > 0
                      ? 'bg-orange-50 border-orange-200'
                      : 'bg-gray-50 border-gray-200'
              }`}>
                <p className="font-medium mb-1 flex items-center gap-1.5">
                  {receipt.access_skipped ? (
                    <><AlertTriangle size={14} className="text-yellow-500" /> Acceso pendiente</>
                  ) : receipt.access_enrolled ? (
                    <><CheckCircle2 size={14} className="text-green-600" /> Acceso activado en Hikvision</>
                  ) : (
                    <><XCircle size={14} className="text-red-500" /> Error activando acceso</>
                  )}
                </p>
                {receipt.access_skipped ? (
                  <p className="text-xs text-yellow-700">
                    {member?.photo_path
                      ? 'Sin dispositivos activos configurados'
                      : 'El miembro no tiene foto — enrola la cara manualmente'}
                  </p>
                ) : (
                  <div className="space-y-1.5 mt-1">
                    {receipt.access_results.map((r, i) => (
                      <div key={i} className="text-xs">
                        <div className="flex items-center gap-2">
                          {r.face_enrolled
                            ? <Wifi size={11} className="text-green-500" />
                            : <WifiOff size={11} className="text-red-400" />}
                          <span className="font-medium">{r.device}</span>
                          <span className={r.face_enrolled ? 'text-green-600' : 'text-orange-600'}>
                            {r.face_enrolled ? '✓ Enrolado' : r.user_added ? '⚠ Usuario OK, sin foto' : '✗ Error'}
                          </span>
                        </div>
                        {!r.face_enrolled && r.error && (
                          <p className="text-gray-400 mt-0.5 ml-5 break-all line-clamp-2" title={r.error}>
                            {(() => {
                              try {
                                const j = JSON.parse(r.error)
                                const msg = j.subStatusCode || j.errorMsg || j.statusString || ''
                                return msg || r.error.slice(0, 80)
                              } catch { return r.error.slice(0, 80) }
                            })()}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="px-6 pb-6">
              <button
                className="btn-primary w-full"
                onClick={() => setShowReceipt(false)}>
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Modal: Asignar membresía ─────────────────────────────────────────── */}
      {showMembershipForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="font-semibold">Asignar Membresía</h2>
              <button onClick={() => setShowMembershipForm(false)}
                className="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <form onSubmit={handleAssignMembership} className="p-6 space-y-4">
              <div>
                <label className="label">Plan</label>
                <select className="input" value={memForm.plan_id}
                  onChange={e => setMemForm(f => ({ ...f, plan_id: Number(e.target.value) }))}>
                  <option value={0}>Seleccionar plan</option>
                  {plans.map(p => (
                    <option key={p.id} value={p.id}>
                      {p.name} — ${p.price} ({p.duration_days} días)
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Fecha de Inicio</label>
                <input type="date" className="input" value={memForm.start_date}
                  onChange={e => setMemForm(f => ({ ...f, start_date: e.target.value }))} />
              </div>
              <div>
                <label className="label">Método de Pago</label>
                <select className="input" value={memForm.payment_method}
                  onChange={e => setMemForm(f => ({ ...f, payment_method: e.target.value }))}>
                  <option value="cash">Efectivo</option>
                  <option value="card">Tarjeta</option>
                  <option value="transfer">Transferencia</option>
                </select>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" className="btn-secondary flex-1"
                  onClick={() => setShowMembershipForm(false)}>
                  Cancelar
                </button>
                <button type="submit" className="btn-primary flex-1" disabled={assigning}>
                  {assigning ? 'Procesando...' : '💳 Cobrar y Asignar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
