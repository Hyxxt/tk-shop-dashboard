import { createRouter, createWebHashHistory, type RouteRecordRaw } from 'vue-router'
import { authState, hasPerm } from '@/stores/auth'
import { getToken } from '@/api/http'

/**
 * 菜单即路由。
 *
 * 这是中后台框架（Vben / Ant Design Pro 一类）的核心机制，拆开就三层：
 *   1. 路由表带 meta.perm 权限码；
 *   2. 侧边栏菜单由路由表过滤生成 —— 没权限的菜单根本不渲染；
 *   3. 路由守卫再拦一次 —— 手动敲 URL 也进不去。
 * 第 2 步只是体验，第 3 步才是安全；后端接口上的 require_perm 是第三道锁。
 * 三处缺一不可，只做菜单隐藏等于没做。
 */
declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    icon?: string
    perm?: string
    hidden?: boolean
  }
}

export const layoutRoutes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '经营看板', icon: 'chart', perm: 'dashboard:view' },
  },
  {
    path: '/shops',
    name: 'shops',
    component: () => import('@/views/ShopList.vue'),
    meta: { title: '店铺管理', icon: 'shop', perm: 'shop:view' },
  },
  {
    path: '/products',
    name: 'products',
    component: () => import('@/views/TopProducts.vue'),
    meta: { title: '单品排行', icon: 'box', perm: 'product:view' },
  },
  {
    path: '/social',
    name: 'social',
    component: () => import('@/views/Social.vue'),
    meta: { title: '社媒矩阵', icon: 'share', perm: 'social:view' },
  },
  {
    path: '/collect',
    name: 'collect',
    component: () => import('@/views/Collect.vue'),
    meta: { title: '采集任务', icon: 'sync', perm: 'collect:view' },
  },
  {
    path: '/system',
    name: 'system',
    component: () => import('@/views/System.vue'),
    meta: { title: '数据规模', icon: 'db', perm: 'system:admin' },
  },
]

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', hidden: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/BasicLayout.vue'),
    children: layoutRoutes,
  },
  {
    path: '/:pathMatch(.*)*',
    name: '404',
    component: () => import('@/views/NotFound.vue'),
    meta: { hidden: true },
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach((to) => {
  const authed = Boolean(getToken() && authState.user)

  if (to.path === '/login') {
    return authed ? { path: '/dashboard' } : true
  }
  if (!authed) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.meta.perm && !hasPerm(to.meta.perm as string)) {
    // 没权限就退回有权限的第一个页面，而不是白屏
    return { path: '/dashboard' }
  }
  return true
})

router.afterEach((to) => {
  const base = 'TK Shop 智能运营看板'
  document.title = to.meta.title ? `${to.meta.title} · ${base}` : base
})

export default router
