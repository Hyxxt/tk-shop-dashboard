<script setup lang="ts">
import { computed, ref } from 'vue'
import { money, shortDate } from '@/utils/format'

const props = withDefaults(
  defineProps<{
    data: { label: string; value: number }[]
    height?: number
    color?: string
  }>(),
  { height: 260, color: '#165dff' },
)

const W = 760
const PAD = { l: 52, r: 14, t: 16, b: 26 }
const H = computed(() => props.height)
const active = ref<number | null>(null)

const maxV = computed(() => {
  const m = Math.max(...props.data.map((d) => d.value), 1)
  const step = Math.pow(10, Math.floor(Math.log10(m)))
  return Math.ceil(m / step) * step
})

const innerW = computed(() => W - PAD.l - PAD.r)
const innerH = computed(() => H.value - PAD.t - PAD.b)

const points = computed(() =>
  props.data.map((d, i) => {
    const x = PAD.l + (props.data.length <= 1 ? 0 : (i / (props.data.length - 1)) * innerW.value)
    const y = PAD.t + innerH.value - (d.value / maxV.value) * innerH.value
    return { x, y, ...d }
  }),
)

const linePath = computed(() =>
  points.value.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' '),
)

const areaPath = computed(() => {
  if (!points.value.length) return ''
  const base = PAD.t + innerH.value
  const first = points.value[0]
  const last = points.value[points.value.length - 1]
  return `${linePath.value} L${last.x.toFixed(1)} ${base} L${first.x.toFixed(1)} ${base} Z`
})

const yTicks = computed(() => {
  const n = 4
  return Array.from({ length: n + 1 }, (_, i) => {
    const v = (maxV.value / n) * i
    return { v, y: PAD.t + innerH.value - (i / n) * innerH.value }
  })
})

const xTicks = computed(() => {
  const len = props.data.length
  if (!len) return []
  const count = Math.min(6, len)
  const step = Math.max(1, Math.floor((len - 1) / (count - 1 || 1)))
  const idxs: number[] = []
  for (let i = 0; i < len; i += step) idxs.push(i)
  if (idxs[idxs.length - 1] !== len - 1) idxs.push(len - 1)
  return idxs.map((i) => ({ x: points.value[i].x, label: shortDate(props.data[i].label) }))
})

function onMove(e: MouseEvent) {
  const svg = e.currentTarget as SVGSVGElement
  const rect = svg.getBoundingClientRect()
  const xInSvg = ((e.clientX - rect.left) / rect.width) * W
  let best = 0
  let bestDist = Infinity
  points.value.forEach((p, i) => {
    const d = Math.abs(p.x - xInSvg)
    if (d < bestDist) {
      bestDist = d
      best = i
    }
  })
  active.value = best
}

const activePoint = computed(() => (active.value === null ? null : points.value[active.value]))
</script>

<template>
  <div class="wrap">
    <svg
      :viewBox="`0 0 ${W} ${H}`"
      width="100%"
      :style="{ height: `${H}px`, display: 'block' }"
      @mousemove="onMove"
      @mouseleave="active = null"
    >
      <defs>
        <linearGradient :id="`grad-${color.replace('#', '')}`" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" :stop-color="color" stop-opacity="0.22" />
          <stop offset="100%" :stop-color="color" stop-opacity="0.01" />
        </linearGradient>
      </defs>

      <g v-for="t in yTicks" :key="`y${t.v}`">
        <line
          :x1="PAD.l"
          :x2="W - PAD.r"
          :y1="t.y"
          :y2="t.y"
          stroke="#eef1f5"
          stroke-width="1"
        />
        <text :x="PAD.l - 10" :y="t.y + 4" text-anchor="end" font-size="11" fill="#86909c">
          {{ money(t.v, 0) }}
        </text>
      </g>

      <path :d="areaPath" :fill="`url(#grad-${color.replace('#', '')})`" />
      <path :d="linePath" fill="none" :stroke="color" stroke-width="2" stroke-linejoin="round" />

      <g v-if="activePoint">
        <line
          :x1="activePoint.x"
          :x2="activePoint.x"
          :y1="PAD.t"
          :y2="PAD.t + innerH"
          stroke="#c9d2e0"
          stroke-width="1"
          stroke-dasharray="3 3"
        />
        <circle :cx="activePoint.x" :cy="activePoint.y" r="4.5" :fill="color" stroke="#fff" stroke-width="2" />
      </g>

      <text
        v-for="t in xTicks"
        :key="`x${t.x}`"
        :x="t.x"
        :y="H - 8"
        text-anchor="middle"
        font-size="11"
        fill="#86909c"
      >
        {{ t.label }}
      </text>
    </svg>

    <div
      v-if="activePoint"
      class="tip"
      :style="{ left: `calc(${(activePoint.x / W) * 100}% )`, top: '6px' }"
    >
      <div class="tip-d">{{ activePoint.label }}</div>
      <div class="tip-v">{{ money(activePoint.value) }}</div>
    </div>
  </div>
</template>

<style scoped>
.wrap {
  position: relative;
  width: 100%;
}

.tip {
  position: absolute;
  transform: translateX(-50%);
  background: #0f1c2e;
  color: #fff;
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 12px;
  pointer-events: none;
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(15, 28, 46, 0.18);
}

.tip-d {
  color: #9fb0c6;
  font-size: 11px;
  margin-bottom: 2px;
}

.tip-v {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
</style>
