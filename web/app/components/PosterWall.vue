<script setup lang="ts">
// Slowly scrolling poster columns behind the hero (a "video" made from real posters).
const props = defineProps<{ posters: string[] }>()
const columns = computed(() => {
  const list = props.posters.filter(Boolean)
  if (!list.length) return []
  const n = 6
  return Array.from({ length: n }, (_, c) => {
    const col = list.filter((_, i) => i % n === c)
    const base = col.length ? col : list
    return [...base, ...base, ...base]
  })
})
</script>

<template>
  <div class="wall" aria-hidden="true">
    <div v-for="(col, c) in columns" :key="c" class="col" :class="c % 2 ? 'down' : 'up'" :style="{ animationDuration: `${70 + c * 9}s` }">
      <img v-for="(src, i) in col" :key="i" :src="src" alt="" decoding="async" fetchpriority="low" width="200" height="300" />
    </div>
    <div class="veil" />
  </div>
</template>

<style scoped>
.wall {
  position: absolute;
  inset: 0;
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
  padding: 0 12px;
  overflow: hidden;
  transform: rotate(-6deg) scale(1.25);
  opacity: 0.85;
}
.col {
  display: flex;
  flex-direction: column;
  gap: 12px;
  will-change: transform;
}
.col img {
  width: 100%;
  aspect-ratio: 2 / 3;
  object-fit: cover;
  border-radius: 8px;
}
.up {
  animation: up linear infinite;
}
.down {
  animation: down linear infinite;
}
@keyframes up {
  to {
    transform: translateY(-33.333%);
  }
}
@keyframes down {
  from {
    transform: translateY(-33.333%);
  }
  to {
    transform: translateY(0);
  }
}
@media (max-width: 640px) {
  .wall {
    grid-template-columns: repeat(3, 1fr);
  }
  .col:nth-child(n + 4) {
    display: none;
  }
}
@media (prefers-reduced-motion: reduce) {
  .col {
    animation: none;
  }
}
</style>
