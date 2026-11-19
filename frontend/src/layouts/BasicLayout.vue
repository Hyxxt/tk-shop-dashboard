<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { layoutRoutes } from '@/router'
import { authState, hasPerm, logout } from '@/stores/auth'
import Icon from '@/components/Icon.vue'

const route = useRoute()
const router = useRouter()

const menus = computed(() =>
  layoutRoutes.filter((r) => r.meta?.title && hasPerm(r.meta?.perm as string)),
)

const currentTitle = computed(() => (route.meta.title as string) || '经营看板')

function doLogout() {
  logout()
  router.push('/login')
}
</script>

<template>
  <div class="shell">
    <aside class="side">
      <div class="brand">
        <div class="logo">TK</div>
        <div class="brand-txt">
          <strong>TK Shop</strong>
          <span>智能运营看板</span>
        </div>
      </div>

      <nav class="menu">
        <router-link
          v-for="m in menus"
          :key="m.path"
          :to="m.path"
          class="item"
          :class="{ active: route.path === m.path }"
        >
          <Icon :name="m.meta?.icon || 'chart'" />
          <span>{{ m.meta?.title }}</span>
        </router-link>
      </nav>

      <div class="side-foot">
        <div class="env">DEMO 环境</div>
        <div class="muted-light">数据为模拟数据</div>
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <div class="loc">
          <span class="muted">TK Shop</span>
          <span class="sep">/</span>
          <strong>{{ currentTitle }}</strong>
        </div>
        <div class="user">
          <span class="tag tag-blue">{{ authState.user?.roles[0] || 'guest' }}</span>
          <span class="uname">{{ authState.user?.display_name }}</span>
          <button class="btn" @click="doLogout">退出</button>
        </div>
      </header>

      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.shell {
  display: flex;
  height: 100%;
  min-height: 100vh;
}

.side {
  width: 224px;
  flex: 0 0 224px;
  background: var(--sidebar);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: 100vh;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 18px 20px;
}

.logo {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  background: var(--brand);
  color: #fff;
  font-weight: 700;
  font-size: 14px;
  display: grid;
  place-items: center;
  letter-spacing: 0.5px;
}

.brand-txt {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
  color: #fff;
}

.brand-txt strong {
  font-size: 14px;
  font-weight: 600;
}

.brand-txt span {
  font-size: 11px;
  color: #7b8aa0;
}

.menu {
  flex: 1;
  padding: 4px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
}

.item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border-radius: 7px;
  color: #a9b6c8;
  font-size: 13.5px;
  transition: all 0.15s;
}

.item:hover {
  background: var(--sidebar-hover);
  color: #fff;
}

.item.active {
  background: var(--brand);
  color: #fff;
  font-weight: 500;
}

.side-foot {
  padding: 14px 18px 18px;
  border-top: 1px solid #1c2b40;
}

.env {
  display: inline-block;
  font-size: 10.5px;
  color: #6ee7b7;
  background: rgba(110, 231, 183, 0.12);
  border-radius: 4px;
  padding: 1px 6px;
  margin-bottom: 6px;
}

.muted-light {
  font-size: 11px;
  color: #62718a;
}

.main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.topbar {
  height: 56px;
  flex: 0 0 56px;
  background: #fff;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 22px;
  position: sticky;
  top: 0;
  z-index: 5;
}

.loc {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.sep {
  color: var(--text-3);
}

.user {
  display: flex;
  align-items: center;
  gap: 10px;
}

.uname {
  font-size: 13px;
  color: var(--text-2);
}

.content {
  padding: 20px 22px 40px;
  flex: 1;
  min-width: 0;
}
</style>
