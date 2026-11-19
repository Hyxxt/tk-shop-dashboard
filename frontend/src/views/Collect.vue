<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api, type CollectTask } from '@/api'
import { dt } from '@/utils/format'
import { hasPerm } from '@/stores/auth'

const rows = ref<CollectTask[]>([])
const running = ref<number | null>(null)
const msg = ref('')
const canRun = hasPerm('collect:run')

async function load() {
  rows.value = await api.collectTasks()
}

async function run(t: CollectTask) {
  running.value = t.id
  msg.value = ''
  try {
    const res = await api.runCollect(t.id)
    msg.value = `任务 #${res.task_id} ${res.status === 'OK' ? '成功' : '失败'}：${res.message}`
  } catch (e) {
    msg.value = `执行被拦截：${(e as Error).message}`
  } finally {
    running.value = null
    await load()
  }
}

function statusTag(s: string) {
  return s === 'OK' ? 'tag-green' : s === 'FAILED' ? 'tag-red' : s === 'RUNNING' ? 'tag-blue' : 'tag-gray'
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="toolbar">
      <div>
        <h2 class="page-title">采集任务</h2>
        <span class="muted">
          cron 表达式驱动 · 按唯一键 UPSERT，重跑不会重复累加
        </span>
      </div>
      <span v-if="!canRun" class="tag tag-amber">当前账号无 collect:run 权限</span>
    </div>

    <div v-if="msg" class="notice">{{ msg }}</div>

    <section class="panel">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>采集源</th>
            <th>目标</th>
            <th>调度</th>
            <th>状态</th>
            <th>上次运行</th>
            <th style="text-align: right">写入行数</th>
            <th style="text-align: right">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in rows" :key="t.id">
            <td class="muted">{{ t.id }}</td>
            <td><span class="tag tag-gray">{{ t.source }}</span></td>
            <td class="strong">{{ t.target }}</td>
            <td class="mono">{{ t.schedule }}</td>
            <td><span class="tag" :class="statusTag(t.status)">{{ t.status }}</span></td>
            <td class="muted">{{ dt(t.last_run_at) }}</td>
            <td class="num" style="text-align: right">{{ t.last_rows }}</td>
            <td style="text-align: right">
              <button
                class="btn"
                :disabled="!canRun || running === t.id"
                :title="canRun ? '' : '缺少 collect:run 权限'"
                @click="run(t)"
              >
                {{ running === t.id ? '执行中…' : '立即执行' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="panel">
      <div class="panel-body">
        <strong style="font-size: 13.5px">为什么「立即执行」按钮要按权限码控制</strong>
        <p class="muted" style="line-height: 1.85; margin: 8px 0 0">
          采集会写库、会消耗平台接口配额，属于有副作用的操作。
          前端按权限码隐藏按钮只是体验，真正的拦截在后端：
          接口挂 <code>require_perm("collect:run")</code>，viewer 账号直接收到 403。
          用 viewer 登录点一次就能验证这条链路。
        </p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.toolbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.page-title {
  font-size: 19px;
  margin: 0 0 4px;
  font-weight: 600;
}

.strong {
  font-weight: 500;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
  color: var(--text-2);
}

.num {
  font-variant-numeric: tabular-nums;
}

.notice {
  background: var(--brand-soft);
  color: #0e4bd6;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
}

code {
  background: #f2f4f8;
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 12px;
}
</style>
