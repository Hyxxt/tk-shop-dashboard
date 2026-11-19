<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    items: { label: string; value: number; color?: string }[]
    size?: number
    thickness?: number
  }>(),
  { size: 168, thickness: 18 },
)

const total = computed(() => props.items.reduce((s, i) => s + i.value, 0) || 1)
const r = computed(() => (props.size - props.thickness) / 2)
const c = computed(() => 2 * Math.PI * r.value)

const segments = computed(() => {
  let acc = 0
  return props.items.map((it, idx) => {
    const frac = it.value / total.value
    const seg = {
      ...it,
      color: it.color || ['#165dff', '#1d9e75', '#ff7d00', '#d4537e', '#7f77dd'][idx % 5],
      dash: frac * c.value,
      offset: -acc * c.value,
      frac,
    }
    acc += frac
    return seg
  })
})
</script>

<template>
  <div class="donut">
    <svg :width="size" :height="size" :viewBox="`0 0 ${size} ${size}`">
      <g :transform="`rotate(-90 ${size / 2} ${size / 2})`">
        <circle
          :cx="size / 2"
          :cy="size / 2"
          :r="r"
          fill="none"
          stroke="#f2f4f8"
          :stroke-width="thickness"
        />
        <circle
          v-for="s in segments"
          :key="s.label"
          :cx="size / 2"
          :cy="size / 2"
          :r="r"
          fill="none"
          :stroke="s.color"
          :stroke-width="thickness"
          :stroke-dasharray="`${s.dash} ${c - s.dash}`"
          :stroke-dashoffset="s.offset"
          stroke-linecap="butt"
        />
      </g>
      <text
        :x="size / 2"
        :y="size / 2 - 4"
        text-anchor="middle"
        font-size="11"
        fill="#86909c"
      >
        GMV 占比
      </text>
      <text
        :x="size / 2"
        :y="size / 2 + 16"
        text-anchor="middle"
        font-size="15"
        font-weight="600"
        fill="#1d2129"
      >
        {{ items.length }} 个店铺
      </text>
    </svg>

    <div class="legend">
      <div v-for="s in segments" :key="s.label" class="li">
        <span class="dot" :style="{ background: s.color }" />
        <span class="nm">{{ s.label }}</span>
        <span class="pc num">{{ (s.frac * 100).toFixed(1) }}%</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.donut {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.legend {
  display: flex;
  flex-direction: column;
  gap: 9px;
  flex: 1;
  min-width: 130px;
}

.li {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12.5px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  flex: 0 0 8px;
}

.nm {
  flex: 1;
  color: var(--text-2);
}

.pc {
  color: var(--text-3);
  font-variant-numeric: tabular-nums;
}
</style>
