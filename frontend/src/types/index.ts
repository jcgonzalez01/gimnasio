export interface Member {
  id: number
  member_number: string
  first_name: string
  last_name: string
  email?: string
  phone?: string
  birth_date?: string
  gender?: string
  address?: string
  emergency_contact?: string
  emergency_phone?: string
  photo_path?: string
  face_enrolled: boolean
  hikvision_card_no?: string
  status: 'active' | 'inactive' | 'suspended' | 'expired'
  notes?: string
  created_at: string
  updated_at: string
  memberships: MemberMembership[]
  has_active_membership?: boolean
  membership_expires?: string
}

export interface MemberListItem {
  id: number
  member_number: string
  first_name: string
  last_name: string
  email?: string
  phone?: string
  status: string
  face_enrolled: boolean
  photo_path?: string
  created_at: string
  has_active_membership: boolean
  membership_expires?: string
}

export interface MembershipPlan {
  id: number
  name: string
  description?: string
  duration_days: number
  price: number
  max_entries_per_day?: number
  allows_guest: boolean
  is_active: boolean
  color: string
  created_at: string
}

export interface MemberMembership {
  id: number
  member_id: number
  plan_id: number
  start_date: string
  end_date: string
  price_paid: number
  payment_method: string
  is_active: boolean
  notes?: string
  created_at: string
  plan?: MembershipPlan
  sale_id?: number
}

export interface AccessEnrollResult {
  device: string
  user_added: boolean
  face_enrolled: boolean
  error?: string
}

export interface AssignMembershipResponse {
  membership: MemberMembership
  sale_id: number
  sale_number: string
  sale_total: number
  payment_method: string
  access_enrolled: boolean
  access_results: AccessEnrollResult[]
  access_skipped: boolean
}

export interface HikvisionDevice {
  id: number
  name: string
  ip_address: string
  port: number
  username: string
  device_type: string
  location?: string
  direction: string
  is_active: boolean
  last_heartbeat?: string
  serial_number?: string
  model?: string
  firmware?: string
  face_lib_id: string
  created_at: string
}

export interface AccessLog {
  id: number
  member_id?: number
  device_id?: number
  direction: 'in' | 'out'
  access_type: string
  result: 'granted' | 'denied' | 'unknown'
  temperature?: number
  notes?: string
  timestamp: string
  member_name?: string
  device_name?: string
}

export interface AccessEvent {
  event_type: string
  log_id: number
  member_id?: number
  member_name?: string
  member_number?: string
  photo_path?: string
  device_name?: string
  device_location?: string
  direction: string
  result: string
  access_type: string
  temperature?: number
  timestamp: string
}

export interface ProductCategory {
  id: number
  name: string
  description?: string
  icon?: string
  is_active: boolean
}

export interface Product {
  id: number
  name: string
  description?: string
  sku?: string
  barcode?: string
  price: number
  cost?: number
  stock: number
  min_stock: number
  category_id?: number
  is_service: boolean
  is_active: boolean
  image_path?: string
  created_at: string
  category?: ProductCategory
}

export interface SaleItem {
  id: number
  product_id?: number
  product_name: string
  quantity: number
  unit_price: number
  discount: number
  total: number
}

export interface Sale {
  id: number
  sale_number: string
  member_id?: number
  cashier?: string
  subtotal: number
  discount: number
  tax: number
  total: number
  payment_method: string
  payment_reference?: string
  status: string
  notes?: string
  created_at: string
  items: SaleItem[]
  member_name?: string
}

export interface DashboardStats {
  total_members: number
  active_members: number
  expired_members: number
  entries_today: number
  entries_this_month: number
  sales_today: number
  sales_this_month: number
  low_stock_products: number
  memberships_expiring_soon: number
  manual_openings: number
}

export interface ReportsDashboardStats {
  today_access: number
  today_granted: number
  today_denied: number
  today_sales: number
  total_members: number
  active_members: number
  low_stock_products: number
}

export interface DailyStats {
  date: string
  access_count: number
  access_granted: number
  access_denied: number
  sales_count: number
  sales_total: number
  new_members: number
}

export interface TopMember {
  member_id: number
  member_name: string
  member_number: string
  visits: number
}

export interface TopProduct {
  product_id: number
  product_name: string
  quantity_sold: number
  total_sales: number
}

export interface AccessReport {
  id: number
  member_name?: string
  member_number?: string
  direction: string
  access_type: string
  result: string
  timestamp: string
}

export interface SalesReport {
  id: number
  sale_number: string
  member_name?: string
  total: number
  items_count: number
  payment_method: string
  created_at: string
}

export interface ReportsSummary {
  period: { start: string; end: string }
  access: { total: number; granted: number; denied: number }
  sales: { total: number; amount: number; average: number }
}

// ── Auth ────────────────────────────────────────────────────────────────────

export type UserRole = 'admin' | 'manager' | 'cashier' | 'reception'

export interface AuthUser {
  id: number
  username: string
  email?: string
  full_name?: string
  role: UserRole
  is_active: boolean
  last_login?: string
  created_at: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: AuthUser
}

export interface AuditLogEntry {
  id: number
  user_id?: number
  username?: string
  action: string
  entity_type?: string
  entity_id?: string
  summary?: string
  details?: string
  ip_address?: string
  timestamp: string
}
