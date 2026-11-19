<script setup lang="ts">
withDefaults(defineProps<{ name: string; size?: number }>(), { size: 18 })

const paths: Record<string, string> = {
  chart: 'M4 19V5m0 14h16M8 15l3-4 3 2 4-6',
  shop: 'M3 9l1.5-5h15L21 9M3 9h18M5 9v10h14V9M9 19v-6h6v6',
  box: 'M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3zM4 7.5l8 4.5 8-4.5M12 12v9',
  share: 'M8 12a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0zm13-6a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0zm0 12a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0zM7.7 10.8l7-3.6M7.7 13.2l7 3.6',
  sync: 'M20 12a8 8 0 0 1-13.6 5.7M4 12a8 8 0 0 1 13.6-5.7M4 18v-5h5m6-5h5v5',
  db: 'M12 3c4.4 0 8 1.3 8 3s-3.6 3-8 3-8-1.3-8-3 3.6-3 8-3zM4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3',
}
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.6"
    stroke-linecap="round"
    stroke-linejoin="round"
  >
    <path :d="paths[name] || paths.chart" />
  </svg>
</template>
