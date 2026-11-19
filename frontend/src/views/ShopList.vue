<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { api, type ShopRow } from '@/api'
import { moneyFull, num, PLATFORM_LABEL } from '@/utils/format'

const rows = ref<ShopRow[]>([])
const keyword = ref('')

const filtered = computed(() =>
  rows.value.filter((r) => r.name.toLowerCase().includes(keyword.value.toLowerCase())),
)

const totalGmv = computed(() => rows.value.reduce((s, r) => s + r.gmv, 0))

function healthColor(score: number) {
  if (score >= 80) return '#00b42a'
  if (score >= 65) return '#ff7d00'
  return '#f53f3f'
}

onMounted(async () => {
  rows.value = await api.shops()
})
</script>

<template>
  <div class="page">
    <div class="toolbar">
      <div>
        <h2 class="page-title">店铺管理</h2>
        <span class="muted">
          共 {{ rows.length }} 个店铺 / 账号，近 30 天合计 GMV {{ moneyFull(totalGmv) }}
        </span>
      </div>
      <input v-model="keyword" class="search" placeholder="搜索店铺名" />
    </div>

    <section class="panel">
      <table>
        <thead>
          <tr>
            <th>店铺 / 账号</th>
            <th>平台</th>
            <th>地区</th>
            <th>健康分</th>
            <th style="text-align: right">GMV（30 天）</th>
            <th style="text-align: right">订单</th>
            <th style="text-align: right">访客</th>
            <th style="text-align: right">转化率</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in filtered" :key="r.id">
            <td class="strong">{{ r.name }}</td>
            <td>
              <span class="tag tag-blue">{{ PLATFORM_LABEL[r.platform] || r.platform }}</span>
            </td>
            <td class="muted">{{ r.region }} · {{ r.currency }}</td>
            <td>
              <div class="health">
                <div class="h-track">
                  <div
                    class="h-fill"
                    :style="{ width: `${r.health_score}%`, background: healthColor(r.health_score) }"
                  />
                </div>
                <span class="num h-num">{{ r.health_score }}</span>
              </div>
            </td>
            <td class="num" style="text-align: right">{{ moneyFull(r.gmv) }}</td>
            <td class="num" style="text-align: right">{{ num(r.orders) }}</td>
            <td class="num" style="text-align: right">{{ num(r.visitors) }}</td>
            <td class="num" style="text-align: right">{{ r.conversion_rate }}%</td>
          </tr>
        </tbody>
      </table>
      <div v-if="!filtered.length" class="empty">没有匹配的店铺</div>
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
}

.page-title {
  font-size: 19px;
  margin: 0 0 4px;
  font-weight: 600;
}

.search {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  width: 200px;
}

.search:focus {
  border-color: var(--brand);
}

.strong {
  font-weight: 500;
}

.health {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 110px;
}

.h-track {
  width: 62px;
  height: 5px;
  background: #f2f4f8;
  border-radius: 3px;
  overflow: hidden;
}

.h-fill {
  height: 100%;
  border-radius: 3px;
}

.h-num {
  font-size: 12px;
  color: var(--text-2);
}
</style>
