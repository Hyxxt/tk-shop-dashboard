import { request } from './http'

export interface Overview {
  gmv: number
  orders: number
  visitors: number
  conversion_rate: number
  avg_order_value: number
  refund_rate: number
  gmv_growth: number
  orders_growth: number
}

export interface TrendPoint {
  stat_date: string
  gmv: number
  orders: number
  visitors: number
}

export interface TopProduct {
  product_id: number
  title: string
  sku: string
  category: string
  shop_name: string
  gmv: number
  orders: number
  visitors: number
  conversion_rate: number
}

export interface ShopRow {
  id: number
  platform: string
  name: string
  region: string
  currency: string
  health_score: number
  gmv: number
  orders: number
  visitors: number
  conversion_rate: number
}

export interface SocialRow {
  platform: string
  posts: number
  views: number
  likes: number
  comments: number
  shares: number
  engagement_rate: number
  avg_views: number
}

export interface CollectTask {
  id: number
  source: string
  target: string
  schedule: string
  status: string
  last_run_at: string | null
  last_rows: number
  error_msg: string | null
}

export interface LoginResp {
  token: string
  username: string
  display_name: string
  roles: string[]
  permissions: string[]
}

export interface SystemStats {
  shops: number
  products: number
  daily_metrics: number
  collect_tasks: number
  dialect: string
}

const qs = (params: Record<string, string | number | undefined>) => {
  const p = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== '') p.set(k, String(v))
  })
  const s = p.toString()
  return s ? `?${s}` : ''
}

export const api = {
  login: (username: string, password: string) =>
    request<LoginResp>('/auth/login', { method: 'POST', body: { username, password } }),
  me: () => request<LoginResp>('/auth/me'),

  overview: (shopId?: number, days = 30) =>
    request<Overview>(`/dashboard/overview${qs({ shop_id: shopId, days })}`),
  trend: (shopId?: number, days = 30) =>
    request<TrendPoint[]>(`/dashboard/trend${qs({ shop_id: shopId, days })}`),
  topProducts: (shopId?: number, days = 30, limit = 10, orderBy = 'gmv') =>
    request<TopProduct[]>(
      `/dashboard/top-products${qs({ shop_id: shopId, days, limit, order_by: orderBy })}`,
    ),

  shops: () => request<ShopRow[]>('/shops'),
  social: () => request<SocialRow[]>('/social/summary'),
  collectTasks: () => request<CollectTask[]>('/collect/tasks'),
  runCollect: (id: number) =>
    request<{ task_id: number; status: string; rows: number; message: string }>(
      `/collect/tasks/${id}/run`,
      { method: 'POST', body: {} },
    ),
  systemStats: () => request<SystemStats>('/system/stats'),
}
