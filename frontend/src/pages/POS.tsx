import { useEffect, useState } from 'react'
import { posApi, membersApi } from '../services/api'
import type { Product, MemberListItem } from '../types'
import {
  ShoppingCart, Plus, Minus, Trash2, Search,
  CreditCard, Banknote, Send, User
} from 'lucide-react'
import toast from 'react-hot-toast'

interface CartItem {
  product: Product
  quantity: number
  discount: number
}

export default function POS() {
  const [products, setProducts] = useState<Product[]>([])
  const [cart, setCart] = useState<CartItem[]>([])
  const [search, setSearch] = useState('')
  const [paymentMethod, setPaymentMethod] = useState('cash')
  const [memberSearch, setMemberSearch] = useState('')
  const [selectedMember, setSelectedMember] = useState<MemberListItem | null>(null)
  const [memberSuggestions, setMemberSuggestions] = useState<MemberListItem[]>([])
  const [globalDiscount, setGlobalDiscount] = useState(0)
  const [processing, setProcessing] = useState(false)
  const [lastSale, setLastSale] = useState<{ sale_number: string; total: number } | null>(null)

  useEffect(() => {
    posApi.getProducts().then(r => setProducts(r.data))
  }, [])

  useEffect(() => {
    if (memberSearch.length < 2) { setMemberSuggestions([]); return }
    const t = setTimeout(async () => {
      const res = await membersApi.list({ search: memberSearch })
      setMemberSuggestions(res.data.slice(0, 5))
    }, 300)
    return () => clearTimeout(t)
  }, [memberSearch])

  const filtered = products.filter(p =>
    !search || p.name.toLowerCase().includes(search.toLowerCase())
  )

  const addToCart = (product: Product) => {
    setCart(prev => {
      const existing = prev.find(i => i.product.id === product.id)
      if (existing) {
        return prev.map(i => i.product.id === product.id
          ? { ...i, quantity: i.quantity + 1 } : i)
      }
      return [...prev, { product, quantity: 1, discount: 0 }]
    })
  }

  const updateQty = (productId: number, delta: number) => {
    setCart(prev => prev
      .map(i => i.product.id === productId
        ? { ...i, quantity: Math.max(0, i.quantity + delta) } : i)
      .filter(i => i.quantity > 0)
    )
  }

  const removeFromCart = (productId: number) => {
    setCart(prev => prev.filter(i => i.product.id !== productId))
  }

  const subtotal = cart.reduce((sum, i) => sum + i.product.price * i.quantity - i.discount, 0)
  const total = Math.max(0, subtotal - globalDiscount)

  const processSale = async () => {
    if (cart.length === 0) { toast.error('Carrito vacío'); return }
    setProcessing(true)
    try {
      const res = await posApi.createSale({
        member_id: selectedMember?.id,
        payment_method: paymentMethod,
        discount: globalDiscount,
        items: cart.map(i => ({
          product_id: i.product.id,
          product_name: i.product.name,
          quantity: i.quantity,
          unit_price: i.product.price,
          discount: i.discount,
        })),
      })
      setLastSale({ sale_number: res.data.sale_number, total: res.data.total })
      setCart([])
      setGlobalDiscount(0)
      setSelectedMember(null)
      setMemberSearch('')
      toast.success(`✅ Venta ${res.data.sale_number} procesada — $${res.data.total.toFixed(2)}`)
      posApi.getProducts().then(r => setProducts(r.data))
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Error al procesar venta')
    } finally {
      setProcessing(false)
    }
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Catálogo */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="p-6 border-b bg-white space-y-3">
          <h1 className="text-xl font-bold text-gray-900">Punto de Venta</h1>
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input className="input pl-9" placeholder="Buscar producto..."
              value={search} onChange={e => setSearch(e.target.value)} />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {filtered.map(product => (
              <button key={product.id}
                onClick={() => addToCart(product)}
                disabled={!product.is_service && product.stock === 0}
                className={`p-4 rounded-xl border text-left transition-all hover:shadow-md active:scale-95 ${
                  !product.is_service && product.stock === 0
                    ? 'opacity-50 cursor-not-allowed bg-gray-50 border-gray-100'
                    : 'bg-white border-gray-100 hover:border-blue-300'
                }`}
              >
                <p className="font-medium text-sm truncate">{product.name}</p>
                {product.category && (
                  <p className="text-xs text-gray-400 mt-0.5">{product.category.name}</p>
                )}
                <p className="text-lg font-bold text-blue-600 mt-2">
                  ${product.price.toFixed(2)}
                </p>
                {!product.is_service && (
                  <p className={`text-xs mt-1 ${product.stock <= product.min_stock ? 'text-orange-500' : 'text-gray-400'}`}>
                    Stock: {product.stock}
                    {product.stock <= product.min_stock && product.stock > 0 && ' ⚠️'}
                    {product.stock === 0 && ' — Agotado'}
                  </p>
                )}
                {product.is_service && (
                  <p className="text-xs text-purple-500 mt-1">Servicio</p>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Carrito */}
      <div className="w-96 bg-white border-l flex flex-col">
        <div className="p-4 border-b">
          <div className="flex items-center gap-2 text-gray-700 font-semibold mb-3">
            <ShoppingCart size={18} />
            Carrito {cart.length > 0 && `(${cart.length})`}
          </div>

          {/* Miembro */}
          <div className="relative">
            <div className="flex items-center gap-2">
              <User size={14} className="text-gray-400 shrink-0" />
              {selectedMember ? (
                <div className="flex-1 flex items-center justify-between bg-blue-50 px-2 py-1 rounded-lg">
                  <span className="text-sm font-medium text-blue-700">
                    {selectedMember.first_name} {selectedMember.last_name}
                  </span>
                  <button onClick={() => { setSelectedMember(null); setMemberSearch('') }}
                    className="text-blue-400 hover:text-blue-600 ml-2">✕</button>
                </div>
              ) : (
                <input className="input text-sm" placeholder="Buscar miembro (opcional)"
                  value={memberSearch} onChange={e => setMemberSearch(e.target.value)} />
              )}
            </div>
            {memberSuggestions.length > 0 && !selectedMember && (
              <div className="absolute top-full left-0 right-0 bg-white border rounded-lg shadow-lg z-10 mt-1">
                {memberSuggestions.map(m => (
                  <button key={m.id}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex items-center gap-2"
                    onClick={() => { setSelectedMember(m); setMemberSearch(''); setMemberSuggestions([]) }}>
                    <span className="font-medium">{m.first_name} {m.last_name}</span>
                    <span className="text-gray-400 text-xs">{m.member_number}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Items */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {cart.length === 0 ? (
            <div className="text-center text-gray-400 py-12">
              <ShoppingCart size={32} className="mx-auto mb-2 opacity-30" />
              <p className="text-sm">Selecciona productos</p>
            </div>
          ) : cart.map(item => (
            <div key={item.product.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{item.product.name}</p>
                <p className="text-xs text-gray-400">${item.product.price.toFixed(2)} c/u</p>
              </div>
              <div className="flex items-center gap-1">
                <button onClick={() => updateQty(item.product.id, -1)}
                  className="w-6 h-6 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center">
                  <Minus size={10} />
                </button>
                <span className="w-8 text-center text-sm font-medium">{item.quantity}</span>
                <button onClick={() => updateQty(item.product.id, 1)}
                  className="w-6 h-6 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center">
                  <Plus size={10} />
                </button>
              </div>
              <p className="text-sm font-bold w-16 text-right">
                ${(item.product.price * item.quantity).toFixed(2)}
              </p>
              <button onClick={() => removeFromCart(item.product.id)}
                className="text-red-300 hover:text-red-500">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>

        {/* Totales y pago */}
        <div className="p-4 border-t space-y-3">
          {/* Descuento */}
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-500 flex-1">Descuento global:</span>
            <input type="number" min={0} value={globalDiscount}
              onChange={e => setGlobalDiscount(Number(e.target.value))}
              className="w-24 input text-right text-sm py-1" />
          </div>

          <div className="space-y-1 text-sm">
            <div className="flex justify-between text-gray-500">
              <span>Subtotal</span>
              <span>${subtotal.toFixed(2)}</span>
            </div>
            {globalDiscount > 0 && (
              <div className="flex justify-between text-green-600">
                <span>Descuento</span>
                <span>-${globalDiscount.toFixed(2)}</span>
              </div>
            )}
            <div className="flex justify-between font-bold text-lg border-t pt-2">
              <span>Total</span>
              <span>${total.toFixed(2)}</span>
            </div>
          </div>

          {/* Método de pago */}
          <div className="grid grid-cols-3 gap-2">
            {[
              { value: 'cash', label: 'Efectivo', icon: Banknote },
              { value: 'card', label: 'Tarjeta', icon: CreditCard },
              { value: 'transfer', label: 'Transf.', icon: Send },
            ].map(({ value, label, icon: Icon }) => (
              <button key={value}
                onClick={() => setPaymentMethod(value)}
                className={`py-2 rounded-lg text-xs font-medium flex flex-col items-center gap-1 transition-colors ${
                  paymentMethod === value
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}>
                <Icon size={14} />
                {label}
              </button>
            ))}
          </div>

          <button
            onClick={processSale}
            disabled={processing || cart.length === 0}
            className="w-full btn-primary py-3 text-base font-semibold disabled:opacity-50">
            {processing ? 'Procesando...' : `Cobrar $${total.toFixed(2)}`}
          </button>

          {lastSale && (
            <div className="p-2 bg-green-50 rounded-lg text-xs text-center text-green-700">
              ✅ Última venta: {lastSale.sale_number} — ${lastSale.total.toFixed(2)}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
