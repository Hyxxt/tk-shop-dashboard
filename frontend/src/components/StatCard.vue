<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    title: string
    value: string
    sub?: string
    growth?: number
    growthLabel?: string
    accent?: string
  }>(),
  { accent: '#165dff', growthLabel: '环比上期' },
)

const up = computed(() => (props.growth ?? 0) >= 0)
</script>

<template>
  <div class="card">
    <div class="bar" :style="{ background: accent }" />
    <div class="body">
      <div class="title">{{ title }}</div>
      <div class="value num">{{ value }}</div>
      <div class="foot">
        <span v-if="growth !== undefined" class="growth" :class="up ? 'up' : 'down'">
          {{ up ? '▲' : '▼' }} {{ Math.abs(growth).toFixed(2) }}%
        </span>
        <span class="sub">{{ growth !== undefined ? growthLabel : sub }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.card {
  position: relative;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  overflow: hidden;
  display: flex;
}

.bar {
  width: 3px;
  flex: 0 0 3px;
  opacity: 0.85;
}

.body {
  padding: 15px 18px 14px;
  flex: 1;
  min-width: 0;
}

.title {
  font-size: 12.5px;
  color: var(--text-3);
  margin-bottom: 8px;
}

.value {
  font-size: 24px;
  font-weight: 600;
  letter-spacing: -0.4px;
  line-height: 1.1;
  color: var(--text);
}

.foot {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11.5px;
}

.growth {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.up {
  color: #f53f3f;
}

.down {
  color: #00a02a;
}

.sub {
  color: var(--text-3);
}
</style>
