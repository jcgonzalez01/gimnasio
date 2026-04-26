import { useEffect, useState, useRef } from 'react'
import { accessApi, devicesApi } from '../services/api'
import type { AccessLog, AccessEvent } from '../types'
import { format } from 'date-fns'
import { Wifi, WifiOff, LogIn, LogOut, User, Thermometer, QrCode, Fingerprint, KeyRound, RefreshCcw, MonitorSmartphone } from 'lucide-react'

export default function AccessControl() {
  const [logs, setLogs] = useState<(AccessLog & { photo_path?: string })[]>([])
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected')
  const [isSyncing, setIsSyncing] = useState(false)
  const [onlyWithId, setOnlyWithId] = useState(true)
  const wsRef = useRef<WebSocket | null>(null)

  const loadLogs = async () => {
    try {
      const res = await accessApi.getLogs({ limit: 100 })
      setLogs(res.data)
    } catch (err) {
      console.error('Error al cargar registros', err)
    }
  }

  const handleSyncEvents = async () => {
    try {
      setIsSyncing(true)
      const devRes = await devicesApi.list()
      const activeDev = devRes.data.find(d => d.is_active)
      
      if (!activeDev) return

      await devicesApi.pullEvents(activeDev.id, 24)
      loadLogs()
    } catch (error) {
      console.error('Error sincronizando:', error)
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
    let host = window.location.host
    if (host.includes(':5173')) {
      host = host.replace(':5173', ':8001')
    }
    
    const wsUrl = `${protocol}://${host}/api/access/ws`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => setWsStatus('connected')
    ws.onclose = () => {
      setWsStatus('disconnected')
      setTimeout(connectWS, 5000)
    }
    ws.onerror = () => setWsStatus('disconnected')
    ws.onmessage = (e) => {
      try {
        const event: AccessEvent = JSON.parse(e.data)
        if (event.event_type === 'access') {
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
            photo_path: event.photo_path,
          }, ...prev].slice(0, 100))
        }
      } catch {}
    }
  }

  const filteredLogs = onlyWithId ? logs.filter(log => log.member_id) : logs
  const lastIdentified = logs.find(log => log.member_id)
  const API_URL = window.location.origin.includes(':5173') 
    ? window.location.origin.replace(':5173', ':8001')
 
    : window.location.origin

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Control de Acceso</h1>
          <p className="text-gray-500 text-sm">Monitor en tiempo real · Hikvision ISAPI {onlyWithId ? '· Solo eventos con ID' : ''}</p>
        </div>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 cursor-pointer bg-white px-3 py-1.5 rounded-lg border text-sm hover:bg-gray-50 transition-colors">
            <input 
              type="checkbox" 
              checked={onlyWithId} 
              onChange={e => setOnlyWithId(e.target.checked)}
              className="rounded text-blue-600 focus:ring-blue-500"
            />
            <span className="text-gray-700 font-medium">Solo con ID</span>
          </label>

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
                <WifiOff size={16} /> Desconectado
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Tarjeta de Último Acceso */}
      {lastIdentified && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-1 bg-white rounded-2xl shadow-sm border overflow-hidden flex flex-col">
            <div className="aspect-square bg-gray-100 relative">
              {lastIdentified.photo_path ? (
                <img 
                  src={`${API_URL}${lastIdentified.photo_path}`} 
                  alt={lastIdentified.member_name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-300">
                  <User size={80} />
                </div>
              )}
              <div className={`absolute top-4 right-4 px-3 py-1 rounded-full text-white font-bold text-sm shadow-lg ${
                lastIdentified.result === 'granted' ? 'bg-green-500' : 'bg-red-500'
              }`}>
                {lastIdentified.result === 'granted' ? 'CONCEDIDO' : 'DENEGADO'}
              </div>
            </div>
          </div>
          <div className="md:col-span-2 bg-white rounded-2xl shadow-sm border p-6 flex flex-col justify-center space-y-4">
            <div>
              <p className="text-sm font-medium text-blue-600 uppercase tracking-wider">Último Acceso Identificado</p>
              <h2 className="text-4xl font-black text-gray-900 leading-tight">
                {lastIdentified.member_name}
              </h2>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-gray-50 rounded-xl border border-gray-100">
                <p className="text-xs text-gray-500 font-medium uppercase">Dispositivo</p>
                <p className="text-lg font-bold text-gray-800 flex items-center gap-2">
                  <MonitorSmartphone size={18} className="text-blue-500" />
                  {lastIdentified.device_name || 'Entrada'}
                </p>
              </div>
              <div className="p-3 bg-gray-50 rounded-xl border border-gray-100">
                <p className="text-xs text-gray-500 font-medium uppercase">Hora</p>
                <p className="text-lg font-bold text-gray-800">
                  {format(new Date(lastIdentified.timestamp), 'HH:mm:ss')}
                </p>
              </div>
              {lastIdentified.temperature && (
                <div className="p-3 bg-orange-50 rounded-xl border border-orange-100">
                  <p className="text-xs text-orange-600 font-medium uppercase">Temperatura</p>
                  <p className="text-lg font-bold text-orange-700 flex items-center gap-2">
                    <Thermometer size={18} />
                    {lastIdentified.temperature}°C
                  </p>
                </div>
              )}
              <div className="p-3 bg-blue-50 rounded-xl border border-blue-100">
                <p className="text-xs text-blue-600 font-medium uppercase">Tipo</p>
                <p className="text-lg font-bold text-blue-700 capitalize flex items-center gap-2">
                  <Fingerprint size={18} />
                  {lastIdentified.access_type || 'Face'}
                </p>
              </div>
            </div>
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
        <div className="overflow-y-auto max-h-[600px] scrollbar-thin">
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
              {filteredLogs.length === 0 ? (
                <tr><td colSpan={5} className="text-center py-12 text-gray-400">Sin registros {onlyWithId ? 'identificados' : ''}</td></tr>
              ) : filteredLogs.map(log => (
                <tr key={log.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2.5 font-medium">{log.member_name || (log.member_id ? 'Miembro' : 'Extraño')}</td>
                  <td className="px-4 py-2.5 text-gray-500">{log.device_name || '—'}</td>
                  <td className="px-4 py-2.5">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      log.direction === 'in' ? 'bg-blue-50 text-blue-600' : 'bg-purple-50 text-purple-600'
                    }`}>
                      {log.direction === 'in' ? '↑' : '↓'} {log.access_type || 'face'}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    {log.member_id && (
                      <span className={`text-xs px-2 py-0.5 rounded-full font-bold uppercase ${
                        log.result === 'granted'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-red-100 text-red-700'
                      }`}>
                        {log.result === 'granted' ? 'Entrada' : 'Acceso Denegado'}
                      </span>
                    )}
                    {log.temperature && (
                      <span className="ml-1 text-xs text-orange-500">{log.temperature}°C</span>
                    )}
                  </td>
                  <td className="px-4 py-2.5 text-gray-500">
                    {(() => {
                      try {
                        return format(new Date(log.timestamp), 'dd/MM/yyyy HH:mm:ss')
                      } catch (e) {
                        return String(log.timestamp)
                      }
                    })()}
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
