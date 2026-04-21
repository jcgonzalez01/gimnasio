import { useEffect, useState, useRef } from 'react'
import { accessApi, devicesApi } from '../services/api'
import type { AccessLog, AccessEvent } from '../types'
import { format } from 'date-fns'
import { Wifi, WifiOff, LogIn, LogOut, User, Thermometer, QrCode, Fingerprint, KeyRound, RefreshCcw } from 'lucide-react'
import toast from 'react-hot-toast'

const getAccessIcon = (type: string) => {
  const t = type?.toLowerCase() || ''
  if (t.includes('face')) return { icon: <User size={20} />, color: 'text-purple-500' }
  if (t.includes('card')) return { icon: <QrCode size={20} />, color: 'text-blue-500' }
  if (t.includes('fingerprint')) return { icon: <Fingerprint size={20} />, color: 'text-green-500' }
  if (t.includes('pin')) return { icon: <KeyRound size={20} />, color: 'text-orange-500' }
  return { icon: <User size={20} />, color: 'text-gray-500' }
}

export default function AccessControl() {
  const [logs, setLogs] = useState<AccessLog[]>([])
  const [liveEvents, setLiveEvents] = useState<AccessEvent[]>([])
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected')
  const [isSyncing, setIsSyncing] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  const loadLogs = async () => {
    try {
      const res = await accessApi.getLogs({ limit: 50 })
      setLogs(res.data)
    } catch {
      toast.error('Error al cargar registros')
    }
  }

  const handleSyncEvents = async () => {
    try {
      setIsSyncing(true)
      // Buscamos el primer dispositivo activo para sincronizar
      const devRes = await devicesApi.list()
      const activeDev = devRes.data.find(d => d.is_active)
      
      if (!activeDev) {
        toast.error('No hay dispositivos activos para sincronizar')
        return
      }

      const res = await devicesApi.pullEvents(activeDev.id, 24) // Últimas 24h
      toast.success(`Sincronización completa: ${res.data.new_logs_saved} nuevos eventos`)
      loadLogs()
    } catch (error) {
      console.error('Error sincronizando:', error)
      toast.error('Error al sincronizar eventos del dispositivo')
    } finally {
      setIsSyncing(false)
    }
  }

  useEffect(() => {
    loadLogs()
    connectWS()
    return () => { wsRef.current?.close() }
  }, [])

  const connectWS = () => {
    setWsStatus('connecting')
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    
    // Si estamos en desarrollo (port 5173), apuntamos al 8000 del backend.
    // En producción (Nginx), el mismo host maneja el proxy de /api/access/ws.
    let host = window.location.host
    if (host.includes(':5173')) {
      host = host.replace(':5173', ':8000')
    }
    
    const wsUrl = `${protocol}://${host}/api/access/ws`
    const ws = new WebSocket(wsUrl)
    console.log('WS Connect:', wsUrl)
    wsRef.current = ws

    ws.onopen = () => setWsStatus('connected')
    ws.onclose = () => {
      setWsStatus('disconnected')
      setTimeout(connectWS, 5000) // Reconectar
    }
    ws.onerror = () => setWsStatus('disconnected')
    ws.onmessage = (e) => {
      try {
        const event: AccessEvent = JSON.parse(e.data)
        if (event.event_type === 'access') {
          setLiveEvents(prev => [event, ...prev].slice(0, 5))
          setLogs(prev => [{
            id: event.log_id,
            member_id: event.member_id,
            direction: event.direction as 'in' | 'out',
            access_type: event.access_type,
            result: event.result as 'granted' | 'denied' | 'unknown',
            temperature: event.temperature,
            timestamp: event.timestamp,
            member_name: event.member_name,
            device_name: event.device_name,
          }, ...prev].slice(0, 50))

          if (event.result === 'granted') {
            toast.success(`✅ ${event.member_name || 'Visitante'} — ${event.direction === 'in' ? 'Entrada' : 'Salida'}`, {
              duration: 3000,
            })
          } else {
            toast.error(`❌ Acceso denegado — ${event.device_name || ''}`, { duration: 3000 })
          }
        }
      } catch {}
    }
  }

  const ping = () => wsRef.current?.send('ping')

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Control de Acceso</h1>
          <p className="text-gray-500 text-sm">Monitor en tiempo real · Hikvision ISAPI</p>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={handleSyncEvents}
            disabled={isSyncing}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              isSyncing 
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
                : 'bg-blue-50 text-blue-600 hover:bg-blue-100'
            }`}
          >
            <RefreshCcw size={16} className={isSyncing ? 'animate-spin' : ''} />
            {isSyncing ? 'Sincronizando...' : 'Sincronizar Eventos'}
          </button>
          
          <div className="flex items-center gap-2 border-l pl-4">
            {wsStatus === 'connected' ? (
              <span className="flex items-center gap-1.5 text-green-600 text-sm font-medium">
                <Wifi size={16} /> Conectado
              </span>
            ) : wsStatus === 'connecting' ? (
              <span className="flex items-center gap-1.5 text-yellow-500 text-sm">
                <Wifi size={16} /> Conectando...
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-red-500 text-sm cursor-pointer" onClick={connectWS}>
                <WifiOff size={16} /> Desconectado — Click para reconectar
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Eventos en vivo */}
      {liveEvents.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wide">En Vivo</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {liveEvents.map((event, i) => (
              <div key={i}
                className={`p-4 rounded-xl border-2 shadow-sm flex items-center gap-4 ${
                  event.result === 'granted'
                    ? 'border-green-200 bg-green-50'
                    : 'border-red-200 bg-red-50'
                }`}
                style={{ opacity: 1 - i * 0.15 }}
              >
                {event.photo_path ? (
                  <img src={event.photo_path} alt="" className="w-14 h-14 rounded-full object-cover" />
                ) : (
                  <div className={`w-14 h-14 rounded-full bg-white flex items-center justify-center border ${getAccessIcon(event.access_type).color}`}>
                    {getAccessIcon(event.access_type).icon}
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="font-semibold truncate">
                    {event.member_name || 'Desconocido'}
                  </p>
                  {event.member_number && (
                    <p className="text-xs text-gray-500">{event.member_number}</p>
                  )}
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`text-xs font-medium ${
                      event.direction === 'in' ? 'text-blue-600' : 'text-purple-600'
                    }`}>
                      {event.direction === 'in' ? <LogIn size={12} className="inline" /> : <LogOut size={12} className="inline" />}
                      {' '}{event.direction === 'in' ? 'Entrada' : 'Salida'}
                    </span>
                    {event.temperature && (
                      <span className="text-xs text-orange-500 flex items-center gap-0.5">
                        <Thermometer size={10} /> {event.temperature}°C
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-400">
                    {event.device_location || event.device_name || 'Dispositivo'}
                  </p>
                </div>
                <div className={`text-2xl ${event.result === 'granted' ? 'text-green-500' : 'text-red-500'}`}>
                  {event.result === 'granted' ? '✓' : '✗'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Historial */}
      <div className="card p-0 overflow-hidden">
        <div className="px-4 py-3 border-b bg-gray-50 flex items-center justify-between">
          <h2 className="font-semibold text-gray-700">Historial de Accesos</h2>
          <button className="text-sm text-blue-600 hover:underline" onClick={loadLogs}>
            Actualizar
          </button>
        </div>
        <div className="overflow-y-auto max-h-[500px] scrollbar-thin">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-white border-b">
              <tr>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Miembro</th>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Dispositivo</th>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Tipo</th>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Resultado</th>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Fecha/Hora</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {logs.length === 0 ? (
                <tr><td colSpan={5} className="text-center py-12 text-gray-400">Sin registros</td></tr>
              ) : logs.map(log => (
                <tr key={log.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2.5 font-medium">{log.member_name || '—'}</td>
                  <td className="px-4 py-2.5 text-gray-500">{log.device_name || '—'}</td>
                  <td className="px-4 py-2.5">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      log.direction === 'in' ? 'bg-blue-50 text-blue-600' : 'bg-purple-50 text-purple-600'
                    }`}>
                      {log.direction === 'in' ? '↑' : '↓'} {log.access_type || 'face'}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      log.result === 'granted'
                        ? 'bg-green-100 text-green-700'
                        : log.result === 'denied'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {log.result === 'granted' ? 'Permitido' : log.result === 'denied' ? 'Denegado' : 'Desconocido'}
                    </span>
                    {log.temperature && (
                      <span className="ml-1 text-xs text-orange-500">{log.temperature}°C</span>
                    )}
                  </td>
                  <td className="px-4 py-2.5 text-gray-500">
                    {format(new Date(log.timestamp), 'dd/MM/yyyy HH:mm:ss')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
