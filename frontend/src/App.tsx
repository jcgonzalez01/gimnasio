import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Members from './pages/Members'
import MemberDetail from './pages/MemberDetail'
import AccessControl from './pages/AccessControl'
import POS from './pages/POS'
import Products from './pages/Products'
import Sales from './pages/Sales'
import Devices from './pages/Devices'
import Plans from './pages/Plans'
import Reports from './pages/Reports'
import Users from './pages/Users'
import AuditLogPage from './pages/AuditLog'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />

        {/* Visible para todos los autenticados */}
        <Route path="members" element={<Members />} />
        <Route path="members/:id" element={<MemberDetail />} />
        <Route path="access" element={<AccessControl />} />
        <Route path="pos" element={<POS />} />
        <Route path="sales" element={<Sales />} />

        {/* Solo admin / manager */}
        <Route path="products" element={
          <ProtectedRoute roles={['admin', 'manager']}><Products /></ProtectedRoute>
        } />
        <Route path="plans" element={
          <ProtectedRoute roles={['admin', 'manager']}><Plans /></ProtectedRoute>
        } />
        <Route path="reports" element={
          <ProtectedRoute roles={['admin', 'manager']}><Reports /></ProtectedRoute>
        } />

        {/* Solo admin */}
        <Route path="devices" element={
          <ProtectedRoute roles={['admin']}><Devices /></ProtectedRoute>
        } />
        <Route path="users" element={
          <ProtectedRoute roles={['admin']}><Users /></ProtectedRoute>
        } />
        <Route path="audit" element={
          <ProtectedRoute roles={['admin']}><AuditLogPage /></ProtectedRoute>
        } />
      </Route>
    </Routes>
  )
}
