<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    items: { label: string; value: number; hint?: string }[]
    unit?: string
    color?: string
  }>(),
  { color: '#165dff', unit: '' },
)

const max = computed(() => Math.max(...props.items.map((i) => i.value), 1))
const fmt = (v: number) => (props.unit === '$' ? `$${v.toLocaleString('en-US', { maximumFractionDigits: 0 })}` : v.toLocaleString('en-US'))
</script>

<template>
  <div class="list">
    <div v-for="(it, i) in items" :key="it.label" class="row">
      <div class="rank">{{ i + 1 }}</div>
      <div class="mid">
        <div class="lab">
          <span class="name" :title="it.label">{{ it.label }}</span>
          <span class="val num">{{ fmt(it.value) }}</span>
        </div>
        <div class="track">
          <div
            class="fill"
            :style="{
              width: `${Math.max(2, (it.value / max) * 100)}%`,
              background: color,
              opacity: 1 - i * 0.07,
            }"
          />
        </div>
        <div v-if="it.hint" class="hint">{{ it.hint }}</div>
      </div>
    </div>
    <div v-if="!items.length" class="empty">暂无数据</div>
  </div>
</template>

<style scoped>
.list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.rank {
  width: 18px;
  height: 18px;
  flex: 0 0 18px;
  border-radius: 4px;
  background: #f2f4f8;
  color: var(--text-3);
  font-size: 11px;
  display: grid;
  place-items: center;
  margin-top: 2px;
  font-variant-numeric: tabular-nums;
}

.mid {
  flex: 1;
  min-width: 0;
}

.lab {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 5px;
  font-size: 12.5px;
}

.name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-2);
}

.val {
  font-weight: 600;
  flex: 0 0 auto;
}

.track {
  height: 6px;
  background: #f2f4f8;
  border-radius: 3px;
  overflow: hidden;
}

.fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.4s ease;
}

.hint {
  margin-top: 4px;
  font-size: 11px;
  color: var(--text-3);
}
</style>
