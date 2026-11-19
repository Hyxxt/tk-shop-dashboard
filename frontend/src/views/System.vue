<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api, type SystemStats } from '@/api'

const stats = ref<SystemStats | null>(null)
const error = ref('')

const tables = [
  { name: 'shop', desc: '店铺 / 社媒账号载体', rows: '5' },
  { name: 'product', desc: '商品主数据，uk(shop_id, sku) 去重', rows: '40' },
  { name: 'daily_metric', desc: '每日经营快照，商品级 + 店铺级同表', rows: '' },
  { name: 'social_post', desc: '社媒矩阵内容表现', rows: '140' },
  { name: 'collect_task', desc: '采集任务与运行状态', rows: '5' },
]

onMounted(async () => {
  try {
    stats.value = await api.systemStats()
  } catch (e) {
    error.value = (e as Error).message
  }
})
</script>

<template>
  <div class="page">
    <div class="toolbar">
      <div>
        <h2 class="page-title">数据规模</h2>
        <span class="muted">仅 admin 可见，验证 system:admin 权限码</span>
      </div>
    </div>

    <div v-if="error" class="alert">{{ error }}</div>

    <div v-if="stats" class="grid cards">
      <div class="panel mini">
        <div class="muted">店铺 / 账号</div>
        <div class="v num">{{ stats.shops }}</div>
      </div>
      <div class="panel mini">
        <div class="muted">商品</div>
        <div class="v num">{{ stats.products }}</div>
      </div>
      <div class="panel mini">
        <div class="muted">指标快照行数</div>
        <div class="v num">{{ stats.daily_metrics.toLocaleString('en-US') }}</div>
      </div>
      <div class="panel mini">
        <div class="muted">采集任务</div>
        <div class="v num">{{ stats.collect_tasks }}</div>
      </div>
      <div class="panel mini">
        <div class="muted">当前数据库方言</div>
        <div class="v" style="font-size: 18px">{{ stats.dialect }}</div>
      </div>
    </div>

    <section class="panel">
      <div class="panel-head">
        <h3 class="panel-title">表结构</h3>
        <span class="muted">完整 DDL 见 backend/sql/schema.sql</span>
      </div>
      <table>
        <thead>
          <tr>
            <th>表名</th>
            <th>说明</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in tables" :key="t.name">
            <td class="mono">{{ t.name }}</td>
            <td class="muted">{{ t.desc }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="panel">
      <div class="panel-body">
        <strong style="font-size: 13.5px">索引为什么这么建</strong>
        <ul class="points">
          <li>
            <code>uk_shop_product_date</code> —— 采集幂等的根。重跑采集时靠唯一键冲突走
            UPSERT，不会插重复行，也不会把 GMV 翻倍。
          </li>
          <li>
            <code>idx_shop_date_gmv</code> —— 最左列 shop_id 等值、stat_date 范围、gmv
            可参与排序，一条索引同时服务看板主查询和单品排行。
          </li>
          <li>
            <code>idx_shop_category_price</code> —— 商品列表页固定「店铺 → 类目 → 价格」，
            顺序必须和查询条件顺序一致，否则只能用到最左前缀。
          </li>
          <li>
            千万级以后索引救不了聚合 —— 要上预聚合表
            <code>daily_metric_rollup</code>，看板只查汇总，明细留 90 天。
          </li>
        </ul>
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

.page-title {
  font-size: 19px;
  margin: 0 0 4px;
  font-weight: 600;
}

.cards {
  grid-template-columns: repeat(5, 1fr);
}

.mini {
  padding: 14px 16px;
}

.v {
  font-size: 22px;
  font-weight: 600;
  margin-top: 6px;
  letter-spacing: -0.3px;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12.5px;
  color: var(--text);
}

.points {
  margin: 10px 0 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 9px;
  font-size: 12.8px;
  color: var(--text-2);
  line-height: 1.75;
}

code {
  background: #f2f4f8;
  padding: 1px 5px;
  border-radius: 3px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
  color: #0e4bd6;
}

.alert {
  background: #ffece8;
  color: #c02b2b;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 13px;
}

@media (max-width: 1100px) {
  .cards {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
