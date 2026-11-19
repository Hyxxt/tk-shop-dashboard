<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { api, type Overview, type ShopRow, type TopProduct, type TrendPoint } from '@/api'
import StatCard from '@/components/StatCard.vue'
import LineChart from '@/components/LineChart.vue'
import DonutChart from '@/components/DonutChart.vue'
import { money, moneyFull, num, PLATFORM_LABEL } from '@/utils/format'

const DONUT_PALETTE = ['#165dff', '#1d9e75', '#ff7d00', '#d4537e', '#7f77dd']

const days = ref(30)
const shopId = ref<number | ''>('')
const shops = ref<ShopRow[]>([])
const overview = ref<Overview | null>(null)
const trend = ref<TrendPoint[]>([])
const top = ref<TopProduct[]>([])
const loading = ref(false)
const error = ref('')

const trendData = computed(() => trend.value.map((t) => ({ label: t.stat_date, value: t.gmv })))

const donutItems = computed(() =>
  shops.value.map((s, i) => ({
    label: s.name,
    value: s.gmv,
    // 按店铺序号取色，不用平台色 —— 同平台多家店会撞色，扇区就分不出来了
    color: DONUT_PALETTE[i % DONUT_PALETTE.length],
  })),
)

const topRows = computed(() => top.value.slice(0, 8))

async function load() {
  loading.value = true
  error.value = ''
  try {
    const sid = shopId.value === '' ? undefined : Number(shopId.value)
    const [ov, tr, tp] = await Promise.all([
      api.overview(sid, days.value),
      api.trend(sid, days.value),
      api.topProducts(sid, days.value, 8, 'gmv'),
    ])
    overview.value = ov
    trend.value = tr
    top.value = tp
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  shops.value = await api.shops()
  await load()
})

watch([days, shopId], load)
</script>

<template>
  <div class="page">
    <div class="toolbar">
      <div class="left">
        <h2 class="page-title">经营看板</h2>
        <span class="muted">近 {{ days }} 天 · 全平台汇总</span>
      </div>
      <div class="right">
        <select v-model="shopId" class="select">
          <option value="">全部店铺</option>
          <option v-for="s in shops" :key="s.id" :value="s.id">
            {{ s.name }}（{{ PLATFORM_LABEL[s.platform] || s.platform }}）
          </option>
        </select>
        <div class="seg">
          <button :class="{ on: days === 7 }" @click="days = 7">7 天</button>
          <button :class="{ on: days === 30 }" @click="days = 30">30 天</button>
          <button :class="{ on: days === 90 }" @click="days = 90">90 天</button>
        </div>
      </div>
    </div>

    <div v-if="error" class="alert">{{ error }}</div>

    <div v-if="overview" class="grid cards">
      <StatCard
        title="总 GMV"
        :value="money(overview.gmv)"
        :growth="overview.gmv_growth"
        accent="#165dff"
      />
      <StatCard
        title="订单量"
        :value="num(overview.orders)"
        :growth="overview.orders_growth"
        accent="#1d9e75"
      />
      <StatCard
        title="访客数"
        :value="num(overview.visitors)"
        :sub="`转化率 ${overview.conversion_rate}%`"
        accent="#ff7d00"
      />
      <StatCard
        title="客单价"
        :value="moneyFull(overview.avg_order_value)"
        :sub="`退款率 ${overview.refund_rate}%`"
        accent="#7f77dd"
      />
    </div>

    <div class="grid main-grid">
      <section class="panel">
        <div class="panel-head">
          <h3 class="panel-title">GMV 日趋势</h3>
          <span class="muted">{{ trend.length }} 个数据点</span>
        </div>
        <div class="panel-body">
          <LineChart v-if="trendData.length" :data="trendData" :height="266" />
          <div v-else class="empty">暂无趋势数据</div>
        </div>
      </section>

      <section class="panel">
        <div class="panel-head">
          <h3 class="panel-title">店铺 GMV 占比</h3>
        </div>
        <div class="panel-body">
          <DonutChart :items="donutItems" />
        </div>
      </section>
    </div>

    <section class="panel">
      <div class="panel-head">
        <h3 class="panel-title">Top 单品（按 GMV）</h3>
        <span class="muted">点击「单品排行」看完整榜单</span>
      </div>
      <table>
        <thead>
          <tr>
            <th style="width: 46px">#</th>
            <th>商品</th>
            <th>店铺</th>
            <th>类目</th>
            <th style="text-align: right">GMV</th>
            <th style="text-align: right">订单</th>
            <th style="text-align: right">转化率</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(p, i) in topRows" :key="p.product_id">
            <td class="muted">{{ i + 1 }}</td>
            <td class="strong">{{ p.title }}</td>
            <td class="muted">{{ p.shop_name }}</td>
            <td><span class="tag tag-gray">{{ p.category }}</span></td>
            <td class="num" style="text-align: right">{{ moneyFull(p.gmv) }}</td>
            <td class="num" style="text-align: right">{{ p.orders }}</td>
            <td class="num" style="text-align: right">{{ p.conversion_rate }}%</td>
          </tr>
        </tbody>
      </table>
      <div v-if="!topRows.length" class="empty">暂无数据</div>
    </section>

    <div v-if="loading" class="loading-line" />
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
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.left {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.page-title {
  font-size: 19px;
  margin: 0;
  font-weight: 600;
}

.right {
  display: flex;
  gap: 10px;
  align-items: center;
}

.select {
  padding: 7px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 13px;
  color: var(--text-2);
  background: #fff;
  outline: none;
  min-width: 190px;
}

.cards {
  grid-template-columns: repeat(4, 1fr);
}

.main-grid {
  grid-template-columns: 1.85fr 1fr;
  align-items: start;
}

.strong {
  font-weight: 500;
}

.num {
  font-variant-numeric: tabular-nums;
}

.alert {
  background: #ffece8;
  color: #c02b2b;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
}

.loading-line {
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--brand), transparent);
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.25;
  }
  50% {
    opacity: 1;
  }
}

@media (max-width: 1180px) {
  .cards {
    grid-template-columns: repeat(2, 1fr);
  }
  .main-grid {
    grid-template-columns: 1fr;
  }
}
</style>
