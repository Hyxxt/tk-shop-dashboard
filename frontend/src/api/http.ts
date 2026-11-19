/** 统一请求层：注入 token、401 踢回登录、错误统一抛。 */

export interface ApiError extends Error {
  status?: number
}

const TOKEN_KEY = 'tk_token'

/**
 * 开发期走 vite proxy（相对路径 /api）；
 * 生产构建时由 VITE_API_BASE 指定后端域名，例如
 *   VITE_API_BASE=https://tk-shop-api.onrender.com/api
 */
const API_BASE = (import.meta.env.VITE_API_BASE as string | undefined) || '/api'

export function getToken(): string {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

export async function request<T>(
  path: string,
  options: { method?: string; body?: unknown } = {},
): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`${API_BASE}${path}`, {
    method: options.method || 'GET',
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  })

  if (res.status === 401) {
    clearToken()
    if (!location.hash.includes('/login')) location.hash = '#/login'
  }

  const text = await res.text()
  const data = text ? JSON.parse(text) : null

  if (!res.ok) {
    const err: ApiError = new Error(data?.detail || `请求失败 (${res.status})`)
    err.status = res.status
    throw err
  }
  return data as T
}
