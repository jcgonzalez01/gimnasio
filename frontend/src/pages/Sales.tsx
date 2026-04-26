import { useEffect, useState } from 'react'
import { posApi } from '../services/api'
import type { Sale } from '../types'
import { format } from 'date-fns'
import { Receipt, Printer } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Sales() {
  const [sales, setSales] = useState<Sale[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<Sale | null>(null)

  useEffect(() => {
    posApi.getSales({ limit: 200 } as any)
      .then(r => setSales(r.data))
      .finally(() => setLoading(false))
  }, [])

  const payLabel = (m: string) => ({ cash: 'Efectivo', card: 'Tarjeta', transfer: 'Transferencia' }[m] || m)

  const downloadReceipt = async (sale: Sale) => {
    try {
      const res = await posApi.downloadReceipt(sale.id)
      const blob = new Blob([res.data], { type: 'application/pdf' })
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank')
      setTimeout(() => URL.revokeObjectURL(url), 60_000)
    } catch {
      toast.error('Error generando recibo')
    }
  }

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Historial de Ventas</h1>
        <p className="text-gray-500 text-sm">{sales.length} ventas</p>
      </div>

      <div className="flex gap-6">
        <div className="flex-1 card p-0 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Folio</th>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Miembro</th>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Pago</th>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Total</th>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Fecha</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {loading ? (
                <tr><td colSpan={5} className="text-center py-12 text-gray-400">Cargando...</td></tr>
              ) : sales.map(s => (
                <tr key={s.id}
                  className={`hover:bg-gray-50 cursor-pointer ${selected?.id === s.id ? 'bg-blue-50' : ''}`}
                  onClick={() => setSelected(s)}>
                  <td className="px-4 py-2.5 font-medium text-blue-600">{s.sale_number}</td>
                  <td className="px-4 py-2.5">{s.member_name || <span className="text-gray-400">—</span>}</td>
                  <td className="px-4 py-2.5 text-gray-500">{payLabel(s.payment_method)}</td>
                  <td className="px-4 py-2.5 font-bold">${s.total.toFixed(2)}</td>
                  <td className="px-4 py-2.5 text-gray-400">
                    {format(new Date(s.created_at), 'dd/MM/yy HH:mm')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {selected && (
          <div className="w-72 card h-fit">
            <div className="flex items-center gap-2 mb-4 font-semibold text-gray-700">
              <Receipt size={16} /> {selected.sale_number}
            </div>
            {selected.member_name && (
              <p className="text-sm text-gray-500 mb-3">Cliente: <span className="font-medium text-gray-700">{selected.member_name}</span></p>
            )}
            <div className="space-y-2 mb-4">
              {selected.items.map((item, i) => (
                <div key={i} className="flex justify-between text-sm">
                  <span className="text-gray-600">{item.product_name} x{item.quantity}</span>
                  <span className="font-medium">${item.total.toFixed(2)}</span>
                </div>
              ))}
            </div>
            <div className="border-t pt-3 space-y-1 text-sm">
              <div className="flex justify-between text-gray-500">
                <span>Subtotal</span><span>${selected.subtotal.toFixed(2)}</span>
              </div>
              {selected.discount > 0 && (
                <div className="flex justify-between text-green-600">
                  <span>Descuento</span><span>-${selected.discount.toFixed(2)}</span>
                </div>
              )}
              <div className="flex justify-between font-bold text-base">
                <span>Total</span><span>${selected.total.toFixed(2)}</span>
              </div>
              <p className="text-xs text-gray-400 mt-2">
                {payLabel(selected.payment_method)} · {format(new Date(selected.created_at), 'dd/MM/yyyy HH:mm')}
              </p>
            </div>
            <button
              onClick={() => downloadReceipt(selected)}
              className="w-full mt-4 flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm"
            >
              <Printer size={14} /> Imprimir / descargar PDF
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
