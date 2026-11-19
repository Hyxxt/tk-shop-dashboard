<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { api, type TopProduct } from '@/api'
import BarList from '@/components/BarList.vue'
import { moneyFull, num } from '@/utils/format'

const days = ref(30)
const orderBy = ref<'gmv' | 'orders' | 'visitors'>('gmv')
const rows = ref<TopProduct[]>([])
const loading = ref(false)

const barItems = ref<{ label: string; value: number; hint?: string }[]>([])

async function load() {
  loading.value = true
  try {
    rows.value = await api.topProducts(undefined, days.value, 15, orderBy.value)
    barItems.value = rows.value.slice(0, 10).map((p) => ({
      label: p.title,
      value: orderBy.value === 'gmv' ? p.gmv : orderBy.value === 'orders' ? p.orders : p.visitors,
      hint: `${p.sku} · 转化率 ${p.conversion_rate}%`,
    }))
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch([days, orderBy], load)
</script>

<template>
  <div class="page">
    <div class="toolbar">
      <div>
        <h2 class="page-title">单品排行</h2>
        <span class="muted">
          跨店铺聚合 · 排序维度：{{ orderBy === 'gmv' ? 'GMV' : orderBy === 'orders' ? '订单量' : '访客数' }}
        </span>
      </div>
      <div class="right">
        <div class="seg">
          <button :class="{ on: orderBy === 'gmv' }" @click="orderBy = 'gmv'">按 GMV</button>
          <button :class="{ on: orderBy === 'orders' }" @click="orderBy = 'orders'">按订单</button>
          <button :class="{ on: orderBy === 'visitors' }" @click="orderBy = 'visitors'">按访客</button>
        </div>
        <div class="seg">
          <button :class="{ on: days === 7 }" @click="days = 7">7 天</button>
          <button :class="{ on: days === 30 }" @click="days = 30">30 天</button>
          <button :class="{ on: days === 90 }" @click="days = 90">90 天</button>
        </div>
      </div>
    </div>

    <div class="grid two">
      <section class="panel">
        <div class="panel-head">
          <h3 class="panel-title">Top 10</h3>
          <span class="muted">{{ loading ? '加载中…' : '按 ' + orderBy }}</span>
        </div>
        <div class="panel-body">
          <BarList
            :items="barItems"
            :unit="orderBy === 'gmv' ? '$' : ''"
            :color="orderBy === 'gmv' ? '#165dff' : '#1d9e75'"
          />
        </div>
      </section>

      <section class="panel">
        <div class="panel-head">
          <h3 class="panel-title">明细</h3>
          <span class="muted">Top {{ rows.length }}</span>
        </div>
        <div class="scroll">
          <table>
            <thead>
              <tr>
                <th style="width: 40px">#</th>
                <th>商品</th>
                <th style="text-align: right">GMV</th>
                <th style="text-align: right">订单</th>
                <th style="text-align: right">转化</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(p, i) in rows" :key="p.product_id">
                <td class="muted">{{ i + 1 }}</td>
                <td>
                  <div class="t">{{ p.title }}</div>
                  <div class="muted">{{ p.shop_name }} · {{ p.category }}</div>
                </td>
                <td class="num" style="text-align: right">{{ moneyFull(p.gmv) }}</td>
                <td class="num" style="text-align: right">{{ num(p.orders) }}</td>
                <td class="num" style="text-align: right">{{ p.conversion_rate }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
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

.right {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.two {
  grid-template-columns: 1fr 1fr;
  align-items: start;
}

.scroll {
  max-height: 520px;
  overflow-y: auto;
}

.t {
  font-weight: 500;
  margin-bottom: 2px;
}

.num {
  font-variant-numeric: tabular-nums;
}

@media (max-width: 1100px) {
  .two {
    grid-template-columns: 1fr;
  }
}
</style>
