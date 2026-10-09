<script setup lang="ts">
import type { Collection } from '~/composables/useApi'

defineProps<{ collection: Collection; index: number }>()
const localePath = useLocalePath()
</script>

<template>
  <NuxtLink
    :to="localePath(`/collections/${collection.slug}`)"
    class="card flex h-full gap-4 rounded-[10px] border p-5"
  >
    <span class="font-serif text-2xl font-semibold leading-none" style="color: var(--accent)">{{ String(index).padStart(2, '0') }}</span>
    <span>
      <span class="block font-serif text-lg font-semibold leading-snug">{{ collection.name }}</span>
      <span class="mt-1 block text-sm" style="color: var(--ink-soft)">{{ collection.description }}</span>
    </span>
  </NuxtLink>
</template>

<style scoped>
.card {
  border-color: var(--line);
  background: var(--surface);
  transition: border-color var(--dur), box-shadow var(--dur);
}
.card:hover {
  border-color: var(--ink);
  box-shadow: var(--shadow);
}
</style>
