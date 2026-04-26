import axios from 'axios'
import type {
  Member, MemberListItem, MembershipPlan, MemberMembership, AssignMembershipResponse,
  HikvisionDevice, AccessLog,
  Product, ProductCategory, Sale, DashboardStats
} from '../types'

// Configuración de Axios simple y directa
const api = axios.create({ 
  baseURL: '/api'
})

// ── Miembros ──────────────────────────────────────────────────────────────────

export const membersApi = {
  list: (params?: { search?: string; status?: string }) =>
    api.get<MemberListItem[]>('/members', { params }),
  get: (id: number) => api.get<Member>(`/members/${id}`),
  create: (data: Partial<Member>) => api.post<Member>('/members', data),
  update: (id: number, data: Partial<Member>) => api.put<Member>(`/members/${id}`, data),
  delete: (id: number) => api.delete(`/members/${id}`),
  uploadPhoto: (id: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/members/${id}/photo`, form)
  },
  getMemberships: (id: number) => api.get<MemberMembership[]>(`/members/${id}/memberships`),
  setFaceStatus: (id: number, faceEnrolled: boolean) =>
    api.patch(`/members/${id}/face-status`, null, { params: { face_enrolled: faceEnrolled } }),
  assignMembership: (id: number, data: {
    plan_id: number; start_date: string; end_date: string;
    price_paid: number; payment_method: string; member_id?: number
  }) => api.post<AssignMembershipResponse>(`/members/${id}/memberships`, data),
  updateValidity: (id: number, opts?: {
    beginDate?: string; endDate?: string; deviceIds?: string
  }) => api.post(`/members/${id}/update-validity`, null, {
    params: {
      begin_date: opts?.beginDate,
      end_date:   opts?.endDate,
      device_ids: opts?.deviceIds,
    }
  }),
}

// ── Planes de membresía ───────────────────────────────────────────────────────

export const plansApi = {
  list: () => api.get<MembershipPlan[]>('/members/plans'),
  create: (data: Partial<MembershipPlan>) => api.post<MembershipPlan>('/members/plans', data),
  update: (id: number, data: Partial<MembershipPlan>) =>
    api.put<MembershipPlan>(`/members/plans/${id}`, data),
  delete: (id: number) => api.delete(`/members/plans/${id}`),
}

// ── Dispositivos Hikvision ────────────────────────────────────────────────────

export const devicesApi = {
  list: () => api.get<HikvisionDevice[]>('/access/devices'),
  create: (data: Partial<HikvisionDevice> & { password: string }) =>
    api.post<HikvisionDevice>('/access/devices', data),
  update: (id: number, data: Partial<HikvisionDevice>) =>
    api.put<HikvisionDevice>(`/access/devices/${id}`, data),
  delete: (id: number) => api.delete(`/access/devices/${id}`),
  test: (id: number) => api.post(`/access/devices/${id}/test`),
  openDoor: (id: number) => api.post(`/access/devices/${id}/open-door`),
  debugDoor: (id: number) => api.get(`/access/devices/${id}/debug-door`),
  commsLog:  (id: number, memberId?: number) =>
    api.get(`/access/devices/${id}/comms-log`, { params: memberId ? { member_id: memberId } : {} }),
  syncMembers: (id: number) => api.post(`/access/devices/${id}/sync-members`),
  getHttpHosts: (id: number) => api.get(`/devices/${id}/http-hosts`),
  configureEvents: (id: number, serverIp: string, serverPort = 8000, slotId = 1) =>
    api.post(`/devices/${id}/configure-events`, null, {
      params: { server_ip: serverIp, server_port: serverPort, slot_id: slotId }
    }),
  pullEvents: (id: number, hours = 24) =>
    api.post(`/access/devices/${id}/pull-events`, null, { params: { hours } }),
}


// ── Acceso ────────────────────────────────────────────────────────────────────

export const accessApi = {
  getLogs: (params?: {
    member_id?: number; device_id?: number;
    start_date?: string; end_date?: string; limit?: number
  }) => api.get<AccessLog[]>('/access/logs', { params }),
  getRecentFaces: () => api.get<any[]>('/access/recent-faces'),
  createLog: (data: Partial<AccessLog>) => api.post<AccessLog>('/access/logs', data),
  registerAndEnroll: (memberId: number, opts?: {
    beginDate?: string; endDate?: string; deviceIds?: string
  }) => api.post(`/access/register-and-enroll/${memberId}`, null, {
    params: {
      begin_date: opts?.beginDate,
      end_date:   opts?.endDate,
      device_ids: opts?.deviceIds,
    }
  }),
  registerUser: (memberId: number, opts?: {
    beginDate?: string; endDate?: string; deviceIds?: string
  }) => api.post(`/access/register-user/${memberId}`, null, {
    params: {
      begin_date: opts?.beginDate,
      end_date:   opts?.endDate,
      device_ids: opts?.deviceIds,
    }
  }),
  enrollFace: (memberId: number, opts?: {
    beginDate?: string; endDate?: string; deviceIds?: string
  }) => api.post(`/access/enroll-face/${memberId}`, null, {
    params: {
      begin_date: opts?.beginDate,
      end_date:   opts?.endDate,
      device_ids: opts?.deviceIds,
    }
  }),
  unenrollFace: (memberId: number) => api.delete(`/access/unenroll-face/${memberId}`),
  capturePhotoFromDevice: (deviceId: number, memberId: number) =>
    api.post(`/access/devices/${deviceId}/capture-photo/${memberId}`),
}

// ── POS ───────────────────────────────────────────────────────────────────────

export const posApi = {
  getCategories: () => api.get<ProductCategory[]>('/pos/categories'),
  createCategory: (data: Partial<ProductCategory>) =>
    api.post<ProductCategory>('/pos/categories', data),
  getProducts: (params?: { search?: string; category_id?: number; is_service?: boolean }) =>
    api.get<Product[]>('/pos/products', { params }),
  createProduct: (data: Partial<Product>) => api.post<Product>('/pos/products', data),
  updateProduct: (id: number, data: Partial<Product>) =>
    api.put<Product>(`/pos/products/${id}`, data),
  deleteProduct: (id: number) => api.delete(`/pos/products/${id}`),
  updateStock: (id: number, quantity: number) =>
    api.put(`/pos/products/${id}/stock`, null, { params: { quantity } }),
  createSale: (data: {
    member_id?: number; cashier?: string; discount?: number; tax?: number;
    payment_method: string; payment_reference?: string; notes?: string;
    items: { product_id?: number; product_name: string; quantity: number; unit_price: number; discount?: number }[]
  }) => api.post<Sale>('/pos/sales', data),
  getSales: (params?: { member_id?: number; start_date?: string; end_date?: string }) =>
    api.get<Sale[]>('/pos/sales', { params }),
  getSale: (id: number) => api.get<Sale>(`/pos/sales/${id}`),
  getDashboard: () => api.get<DashboardStats>('/pos/dashboard'),
}

// ── Reportes ────────────────────────────────────────────────────────────────────

export const reportsApi = {
  getDashboard: () => api.get('/reports/dashboard'),
  getDailyStats: (days = 7) => api.get('/reports/daily', { params: { days } }),
  getAccessReport: (params?: {
    start_date?: string; end_date?: string; result?: string; member_id?: number; limit?: number
  }) => api.get('/reports/access', { params }),
  getSalesReport: (params?: {
    start_date?: string; end_date?: string; payment_method?: string; member_id?: number; limit?: number
  }) => api.get('/reports/sales', { params }),
  getTopMembers: (days = 30, limit = 10) =>
    api.get('/reports/top-members', { params: { days, limit } }),
  getTopProducts: (days = 30, limit = 10) =>
    api.get('/reports/top-products', { params: { days, limit } }),
  getSummary: (params?: { start_date?: string; end_date?: string }) =>
    api.get('/reports/summary', { params }),
}

export default api
