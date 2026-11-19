<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { login, authState } from '@/stores/auth'

const router = useRouter()
const route = useRoute()

const username = ref('admin')
const password = ref('admin123')
const error = ref('')

async function submit() {
  error.value = ''
  try {
    await login(username.value.trim(), password.value)
    const redirect = (route.query.redirect as string) || '/dashboard'
    router.push(redirect)
  } catch (e) {
    error.value = (e as Error).message || '登录失败'
  }
}

function fill(u: string, p: string) {
  username.value = u
  password.value = p
}
</script>

<template>
  <div class="page">
    <div class="brand-side">
      <div class="mark">TK</div>
      <h1>TK Shop 智能运营看板</h1>
      <p>
        打通 TikTok Shop 与 Instagram / Facebook / YouTube 矩阵数据，
        从每日采集到指标看板一条链路。
      </p>
      <ul>
        <li>店铺 / 单品双粒度经营快照，采集幂等可重跑</li>
        <li>MySQL 表设计 + 联合索引，看板查询下推到数据库聚合</li>
        <li>权限码三级校验：菜单过滤、路由守卫、接口鉴权</li>
      </ul>
      <div class="note">演示数据为模拟数据，不含任何真实平台经营数据</div>
    </div>

    <div class="form-side">
      <div class="box">
        <h2>登录</h2>
        <p class="muted">使用演示账号进入系统</p>

        <form @submit.prevent="submit">
          <label>账号</label>
          <input v-model="username" placeholder="admin" autocomplete="username" />

          <label>密码</label>
          <input
            v-model="password"
            type="password"
            placeholder="admin123"
            autocomplete="current-password"
          />

          <div v-if="error" class="err">{{ error }}</div>

          <button class="btn btn-primary submit" type="submit" :disabled="authState.loading">
            {{ authState.loading ? '登录中…' : '登 录' }}
          </button>
        </form>

        <div class="quick">
          <span class="muted">演示账号</span>
          <button class="chip" type="button" @click="fill('admin', 'admin123')">
            admin / admin123（可执行采集）
          </button>
          <button class="chip" type="button" @click="fill('viewer', 'viewer123')">
            viewer / viewer123（只读，验证 403）
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  min-height: 100vh;
}

.brand-side {
  flex: 1.05;
  background: linear-gradient(160deg, #0f1c2e 0%, #16294a 55%, #1b3a6b 100%);
  color: #fff;
  padding: 64px 56px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.mark {
  width: 44px;
  height: 44px;
  border-radius: 11px;
  background: var(--brand);
  display: grid;
  place-items: center;
  font-weight: 700;
  margin-bottom: 26px;
}

h1 {
  font-size: 27px;
  margin: 0 0 14px;
  letter-spacing: -0.3px;
}

.brand-side p {
  color: #a9bcd6;
  line-height: 1.75;
  max-width: 440px;
  margin: 0 0 26px;
  font-size: 14px;
}

ul {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 11px;
}

li {
  position: relative;
  padding-left: 18px;
  color: #cfdcee;
  font-size: 13px;
  line-height: 1.6;
}

li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 7px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #4d8dff;
}

.note {
  margin-top: 34px;
  font-size: 11.5px;
  color: #6b7f9b;
}

.form-side {
  flex: 0 0 480px;
  display: grid;
  place-items: center;
  background: #fff;
  padding: 32px;
}

.box {
  width: 100%;
  max-width: 340px;
}

h2 {
  margin: 0 0 4px;
  font-size: 22px;
}

label {
  display: block;
  margin: 18px 0 6px;
  font-size: 12.5px;
  color: var(--text-2);
}

input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 7px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.15s;
}

input:focus {
  border-color: var(--brand);
  box-shadow: 0 0 0 3px rgba(22, 93, 255, 0.1);
}

.submit {
  width: 100%;
  margin-top: 22px;
  padding: 11px;
  font-size: 14px;
}

.err {
  margin-top: 14px;
  color: #f53f3f;
  font-size: 12.5px;
  background: #ffece8;
  padding: 8px 10px;
  border-radius: 6px;
}

.quick {
  margin-top: 26px;
  padding-top: 18px;
  border-top: 1px dashed var(--border);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chip {
  text-align: left;
  border: 1px solid var(--border);
  background: #fafbfc;
  border-radius: 6px;
  padding: 7px 10px;
  font-size: 12px;
  color: var(--text-2);
}

.chip:hover {
  border-color: var(--brand);
  color: var(--brand);
}

@media (max-width: 900px) {
  .brand-side {
    display: none;
  }
  .form-side {
    flex: 1;
  }
}
</style>
