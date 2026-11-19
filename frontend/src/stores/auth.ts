/**
 * 轻量全局状态：不引 Pinia，够用就行。
 * 权限判断是这一层的核心 —— 前端按权限码过滤菜单/hidden 按钮。
 */
import { computed, reactive } from 'vue'
import { api, type LoginResp } from '@/api'
import { clearToken, getToken, setToken } from '@/api/http'

const USER_KEY = 'tk_user'

interface State {
  user: LoginResp | null
  loading: boolean
}

function readCache(): LoginResp | null {
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? (JSON.parse(raw) as LoginResp) : null
  } catch {
    return null
  }
}

export const authState = reactive<State>({
  user: readCache(),
  loading: false,
})

export const isLoggedIn = computed(() => Boolean(getToken() && authState.user))

export function hasPerm(perm?: string): boolean {
  if (!perm) return true
  return Boolean(authState.user?.permissions.includes(perm))
}

export async function login(username: string, password: string): Promise<void> {
  authState.loading = true
  try {
    const res = await api.login(username, password)
    setToken(res.token)
    localStorage.setItem(USER_KEY, JSON.stringify(res))
    authState.user = res
  } finally {
    authState.loading = false
  }
}

export async function refreshUser(): Promise<void> {
  if (!getToken()) return
  try {
    const res = await api.me()
    localStorage.setItem(USER_KEY, JSON.stringify(res))
    authState.user = res
  } catch {
    logout()
  }
}

export function logout(): void {
  clearToken()
  localStorage.removeItem(USER_KEY)
  authState.user = null
}
