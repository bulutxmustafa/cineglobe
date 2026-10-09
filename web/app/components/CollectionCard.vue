<script setup lang="ts">
import type { Collection } from '~/composables/useApi'

const props = defineProps<{ collection: Collection; index: number }>()
const localePath = useLocalePath()
const palettes = [
  ['#e11d48', '#f97316'],
  ['#6d28d9', '#06b6d4'],
  ['#0ea5e9', '#6366f1'],
  ['#10b981', '#84cc16'],
  ['#d946ef', '#f43f5e'],
  ['#f59e0b', '#ef4444'],
]
const bg = computed(() => {
  const [a, b] = palettes[(props.index - 1) % palettes.length]!
  return `linear-gradient(135deg, ${a}, ${b})`
})
</script>

<template>
  <NuxtLink
    :to="localePath(`/collections/${collection.slug}`)"
    class="card relative flex h-full min-h-[150px] flex-col justify-end overflow-hidden rounded-[16px] p-5 text-white"
    :style="{ background: bg }"
  >
    <span class="icon" aria-hidden="true">{{ collection.icon }}</span>
    <span class="relative block pr-12 font-serif text-xl font-semibold leading-snug">{{ collection.name }}</span>
    <span class="relative mt-1 block text-sm text-white/85">{{ collection.description }}</span>
  </NuxtLink>
</template>

<style scoped>
.card {
  box-shadow: 0 10px 28px rgb(13 11 31 / 18%);
  transition: transform 200ms var(--ease), box-shadow 200ms var(--ease);
}
.card:hover {
  transform: translateY(-4px) rotate(-0.4deg);
  box-shadow: 0 16px 36px rgb(13 11 31 / 28%);
}
.icon {
  position: absolute;
  right: 14px;
  top: 12px;
  font-size: 3.4rem;
  opacity: 0.9;
  filter: drop-shadow(0 4px 8px rgb(0 0 0 / 25%));
}
</style>
