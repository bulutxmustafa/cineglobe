<script setup lang="ts">
// Slowly scrolling poster columns behind the hero (a "video" made from real posters).
// Order is shuffled on every visit and one poster at a time is swapped for another
// from the pool, so the wall keeps changing.
const props = defineProps<{ posters: string[] }>()
const N = 9
const PER_COL = 6
const slots = ref<string[]>([])

function shuffle<T>(list: T[]): T[] {
  const a = [...list]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j]!, a[i]!]
  }
  return a
}
function fill() {
  const pool = shuffle(props.posters.filter(Boolean))
  if (!pool.length) return (slots.value = [])
  slots.value = Array.from({ length: N * PER_COL }, (_, i) => pool[i % pool.length]!)
}
watch(() => props.posters, fill, { immediate: true })

let timer: ReturnType<typeof setInterval> | undefined
onMounted(() => {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  timer = setInterval(() => {
    const pool = props.posters.filter((p) => p && !slots.value.includes(p))
    if (!pool.length || !slots.value.length) return
    const next = [...slots.value]
    next[Math.floor(Math.random() * next.length)] = pool[Math.floor(Math.random() * pool.length)]!
    slots.value = next
  }, 2500)
})
onBeforeUnmount(() => clearInterval(timer))

// Each column repeats its posters three times so the scroll loops seamlessly.
const columns = computed(() =>
  Array.from({ length: N }, (_, c) => {
    const col = slots.value.slice(c * PER_COL, (c + 1) * PER_COL)
    return [...col, ...col, ...col]
  }).filter((col) => col.length),
)
</script>

<template>
  <div class="wall" aria-hidden="true">
    <div v-for="(col, c) in columns" :key="c" class="col" :class="c % 2 ? 'down' : 'up'" :style="{ animationDuration: `${70 + c * 9}s` }">
      <img v-for="(src, i) in col" :key="`${i}-${src}`" :src="src" alt="" decoding="async" width="200" height="300" class="swap" />
    </div>
    <div class="veil" />
  </div>
</template>

<style scoped>
.wall {
  position: absolute;
  inset: 0;
  display: grid;
  grid-template-columns: repeat(9, 1fr);
  gap: 10px;
  padding: 0 12px;
  overflow: hidden;
  transform: rotate(-6deg) scale(1.25);
  opacity: 1;
}
.col {
  display: flex;
  flex-direction: column;
  gap: 10px;
  will-change: transform;
}
.swap {
  animation: swap-in 900ms ease both;
}
@keyframes swap-in {
  from {
    opacity: 0;
  }
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
    grid-template-columns: repeat(4, 1fr);
  }
  .col:nth-child(n + 5) {
    display: none;
  }
}
@media (prefers-reduced-motion: reduce) {
  .col {
    animation: none;
  }
}
</style>
