<script setup lang="ts">
// A short celebratory burst of confetti; re-fires whenever `fire` changes.
const props = defineProps<{ fire: number }>()
const pieces = ref<{ id: number; x: number; dx: number; rot: number; delay: number; color: string; size: number }[]>([])
const colors = ['#f2b950', '#19a99c', '#f1ede5', '#f7d58b', '#5ed1c6', '#ffffff']

watch(
  () => props.fire,
  (n) => {
    if (!n || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    pieces.value = Array.from({ length: 46 }, (_, i) => ({
      id: n * 100 + i,
      x: 30 + Math.random() * 40,
      dx: (Math.random() - 0.5) * 360,
      rot: Math.random() * 720,
      delay: Math.random() * 180,
      color: colors[i % colors.length]!,
      size: 6 + Math.random() * 8,
    }))
    setTimeout(() => (pieces.value = []), 2600)
  },
)
</script>

<template>
  <div class="confetti" aria-hidden="true">
    <span
      v-for="p in pieces"
      :key="p.id"
      :style="{
        left: `${p.x}%`,
        width: `${p.size}px`,
        height: `${p.size * 0.5}px`,
        background: p.color,
        animationDelay: `${p.delay}ms`,
        '--dx': `${p.dx}px`,
        '--rot': `${p.rot}deg`,
      }"
    />
  </div>
</template>

<style scoped>
.confetti {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}
.confetti span {
  position: absolute;
  top: 38%;
  border-radius: 2px;
  animation: burst 2.2s cubic-bezier(0.2, 0.7, 0.3, 1) forwards;
}
@keyframes burst {
  0% {
    transform: translate(0, 0) rotate(0);
    opacity: 1;
  }
  30% {
    transform: translate(calc(var(--dx) * 0.6), -160px) rotate(calc(var(--rot) * 0.4));
    opacity: 1;
  }
  100% {
    transform: translate(var(--dx), 420px) rotate(var(--rot));
    opacity: 0;
  }
}
</style>
