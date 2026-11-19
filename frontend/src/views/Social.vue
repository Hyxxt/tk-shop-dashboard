<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api, type SocialRow } from '@/api'
import { num, PLATFORM_LABEL, PLATFORM_COLOR } from '@/utils/format'

const rows = ref<SocialRow[]>([])
const totalViews = computed(() => rows.value.reduce((s, r) => s + r.views, 0))
const totalPosts = computed(() => rows.value.reduce((s, r) => s + r.posts, 0))

onMounted(async () => {
  rows.value = await api.social()
})
</script>

<template>
  <div class="page">
    <div class="toolbar">
      <div>
        <h2 class="page-title">社媒矩阵</h2>
        <span class="muted">
          {{ rows.length }} 个平台 · {{ totalPosts }} 条内容 · 总曝光 {{ num(totalViews) }}
        </span>
      </div>
    </div>

    <div class="grid plats">
      <div v-for="r in rows" :key="r.platform" class="plat panel">
        <div class="p-head">
          <span class="dot" :style="{ background: PLATFORM_COLOR[r.platform] }" />
          <strong>{{ PLATFORM_LABEL[r.platform] || r.platform }}</strong>
          <span class="muted">{{ r.posts }} 条</span>
        </div>
        <div class="p-val num">{{ num(r.views) }}</div>
        <div class="muted">总曝光 · 条均 {{ num(r.avg_views) }}</div>
        <div class="p-foot">
          <span class="tag" :class="r.engagement_rate >= 8 ? 'tag-green' : 'tag-amber'">
            互动率 {{ r.engagement_rate }}%
          </span>
        </div>
      </div>
    </div>

    <section class="panel">
      <div class="panel-head">
        <h3 class="panel-title">平台表现拆分</h3>
        <span class="muted">互动率 =（赞 + 评 + 转）/ 曝光</span>
      </div>
      <table>
        <thead>
          <tr>
            <th>平台</th>
            <th style="text-align: right">内容数</th>
            <th style="text-align: right">曝光</th>
            <th style="text-align: right">点赞</th>
            <th style="text-align: right">评论</th>
            <th style="text-align: right">转发</th>
            <th style="text-align: right">条均曝光</th>
            <th style="text-align: right">互动率</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rows" :key="r.platform">
            <td>
              <span class="tag tag-blue">{{ PLATFORM_LABEL[r.platform] || r.platform }}</span>
            </td>
            <td class="num" style="text-align: right">{{ r.posts }}</td>
            <td class="num" style="text-align: right">{{ num(r.views) }}</td>
            <td class="num" style="text-align: right">{{ num(r.likes) }}</td>
            <td class="num" style="text-align: right">{{ num(r.comments) }}</td>
            <td class="num" style="text-align: right">{{ num(r.shares) }}</td>
            <td class="num" style="text-align: right">{{ num(r.avg_views) }}</td>
            <td class="num" style="text-align: right">{{ r.engagement_rate }}%</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="panel note">
      <div class="panel-body">
        <strong>矩阵口径说明</strong>
        <p class="muted" style="line-height: 1.8; margin: 8px 0 0">
          四个平台的内容统一落到 `social_post` 一张表，靠 `platform + post_id` 唯一键去重。
          口径上把「曝光 / 互动 / 条均产出」拉齐，才能横向比矩阵效率 ——
          否则 TikTok 的视频播放和 Facebook 的帖子触达根本没法放进同一张表里比。
          数据为模拟数据，用于演示采集与看板链路。
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

.page-title {
  font-size: 19px;
  margin: 0 0 4px;
  font-weight: 600;
}

.plats {
  grid-template-columns: repeat(4, 1fr);
}

.plat {
  padding: 16px 18px;
}

.p-head {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  margin-bottom: 12px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.p-val {
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.3px;
  margin-bottom: 4px;
}

.p-foot {
  margin-top: 12px;
}

.num {
  font-variant-numeric: tabular-nums;
}

.note {
  background: #fbfcfe;
}

@media (max-width: 1100px) {
  .plats {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
