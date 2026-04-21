import { useEffect, useState } from 'react'
import { posApi } from '../services/api'
import type { Product, ProductCategory } from '../types'
import { Plus, Edit2, Package, AlertTriangle } from 'lucide-react'
import toast from 'react-hot-toast'

export default function Products() {
  const [products, setProducts] = useState<Product[]>([])
  const [categories, setCategories] = useState<ProductCategory[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Product | null>(null)
  const [form, setForm] = useState({
    name: '', description: '', price: '', cost: '', stock: '0',
    min_stock: '5', category_id: '', is_service: false, sku: '',
  })

  const load = () => {
    Promise.all([posApi.getProducts(), posApi.getCategories()])
      .then(([pRes, cRes]) => { setProducts(pRes.data); setCategories(cRes.data) })
  }

  useEffect(() => { load() }, [])

  const openForm = (product?: Product) => {
    if (product) {
      setEditing(product)
      setForm({
        name: product.name, description: product.description || '',
        price: String(product.price), cost: String(product.cost || ''),
        stock: String(product.stock), min_stock: String(product.min_stock),
        category_id: String(product.category_id || ''),
        is_service: product.is_service, sku: product.sku || '',
      })
    } else {
      setEditing(null)
      setForm({ name: '', description: '', price: '', cost: '', stock: '0', min_stock: '5', category_id: '', is_service: false, sku: '' })
    }
    setShowForm(true)
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    const data = {
      name: form.name, description: form.description || undefined,
      price: parseFloat(form.price), cost: form.cost ? parseFloat(form.cost) : undefined,
      stock: parseInt(form.stock), min_stock: parseInt(form.min_stock),
      category_id: form.category_id ? parseInt(form.category_id) : undefined,
      is_service: form.is_service, sku: form.sku || undefined,
    }
    try {
      if (editing) {
        await posApi.updateProduct(editing.id, data)
        toast.success('Producto actualizado')
      } else {
        await posApi.createProduct(data)
        toast.success('Producto creado')
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
          <h1 className="text-2xl font-bold text-gray-900">Productos e Inventario</h1>
          <p className="text-gray-500 text-sm">{products.length} productos</p>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={() => openForm()}>
          <Plus size={16} /> Nuevo Producto
        </button>
      </div>

      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Producto</th>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Categoría</th>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Precio</th>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Stock</th>
              <th className="text-left px-4 py-3 text-gray-500 font-medium">Tipo</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {products.map(p => (
              <tr key={p.id} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                      <Package size={14} className="text-gray-400" />
                    </div>
                    <div>
                      <p className="font-medium">{p.name}</p>
                      {p.sku && <p className="text-xs text-gray-400">{p.sku}</p>}
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3 text-gray-500">{p.category?.name || '—'}</td>
                <td className="px-4 py-3 font-medium">${p.price.toFixed(2)}</td>
                <td className="px-4 py-3">
                  {p.is_service ? (
                    <span className="text-gray-400">—</span>
                  ) : (
                    <div className="flex items-center gap-1">
                      <span className={p.stock <= p.min_stock ? 'text-orange-600 font-medium' : 'text-gray-700'}>
                        {p.stock}
                      </span>
                      {p.stock <= p.min_stock && p.stock > 0 && (
                        <AlertTriangle size={12} className="text-orange-400" />
                      )}
                      {p.stock === 0 && (
                        <span className="text-xs text-red-500 ml-1">Agotado</span>
                      )}
                    </div>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    p.is_service ? 'bg-purple-50 text-purple-600' : 'bg-gray-50 text-gray-500'
                  }`}>
                    {p.is_service ? 'Servicio' : 'Producto'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <button onClick={() => openForm(p)}
                    className="text-gray-400 hover:text-blue-600 p-1">
                    <Edit2 size={14} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="font-semibold">{editing ? 'Editar Producto' : 'Nuevo Producto'}</h2>
              <button onClick={() => setShowForm(false)} className="text-gray-400 hover:text-gray-600">✕</button>
            </div>
            <form onSubmit={submit} className="p-6 space-y-4">
              <div>
                <label className="label">Nombre *</label>
                <input className="input" value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Precio *</label>
                  <input type="number" step="0.01" className="input" value={form.price}
                    onChange={e => setForm(f => ({ ...f, price: e.target.value }))} required />
                </div>
                <div>
                  <label className="label">Costo</label>
                  <input type="number" step="0.01" className="input" value={form.cost}
                    onChange={e => setForm(f => ({ ...f, cost: e.target.value }))} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">SKU</label>
                  <input className="input" value={form.sku}
                    onChange={e => setForm(f => ({ ...f, sku: e.target.value }))} />
                </div>
                <div>
                  <label className="label">Categoría</label>
                  <select className="input" value={form.category_id}
                    onChange={e => setForm(f => ({ ...f, category_id: e.target.value }))}>
                    <option value="">Sin categoría</option>
                    {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <input type="checkbox" id="is_service" checked={form.is_service}
                  onChange={e => setForm(f => ({ ...f, is_service: e.target.checked }))} />
                <label htmlFor="is_service" className="text-sm text-gray-700">Es un servicio (no maneja stock)</label>
              </div>
              {!form.is_service && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">Stock Actual</label>
                    <input type="number" className="input" value={form.stock}
                      onChange={e => setForm(f => ({ ...f, stock: e.target.value }))} />
                  </div>
                  <div>
                    <label className="label">Stock Mínimo</label>
                    <input type="number" className="input" value={form.min_stock}
                      onChange={e => setForm(f => ({ ...f, min_stock: e.target.value }))} />
                  </div>
                </div>
              )}
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
