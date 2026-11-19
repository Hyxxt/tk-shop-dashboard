<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <div class="box">
    <div class="code">404</div>
    <p class="muted">页面不存在，或当前账号没有访问权限。</p>
    <button class="btn btn-primary" @click="router.push('/dashboard')">回到看板</button>
  </div>
</template>

<style scoped>
.box {
  min-height: 60vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.code {
  font-size: 44px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -1px;
}

.btn {
  margin-top: 8px;
}
</style>
