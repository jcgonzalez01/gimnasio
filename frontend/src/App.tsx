import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Members from './pages/Members'
import MemberDetail from './pages/MemberDetail'
import AccessControl from './pages/AccessControl'
import POS from './pages/POS'
import Products from './pages/Products'
import Sales from './pages/Sales'
import Devices from './pages/Devices'
import Plans from './pages/Plans'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="members" element={<Members />} />
        <Route path="members/:id" element={<MemberDetail />} />
        <Route path="access" element={<AccessControl />} />
        <Route path="pos" element={<POS />} />
        <Route path="products" element={<Products />} />
        <Route path="sales" element={<Sales />} />
        <Route path="devices" element={<Devices />} />
        <Route path="plans" element={<Plans />} />
      </Route>
    </Routes>
  )
}
