<script setup lang="ts">
defineProps<{ pending?: boolean; error?: unknown; empty?: boolean }>()
</script>

<template>
  <div v-if="pending" class="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-5" aria-busy="true">
    <div v-for="n in 10" :key="n" class="aspect-[2/3] animate-pulse rounded-[6px]" style="background: var(--line)" />
  </div>
  <div
    v-else-if="error"
    class="rounded-[6px] border p-6 text-center"
    style="border-color: var(--line-strong); background: var(--surface)"
    role="alert"
  >
    <p class="font-semibold">{{ $t('state.errorTitle') }}</p>
    <p class="mt-1 text-sm" style="color: var(--ink-soft)">{{ $t('state.errorBody') }}</p>
  </div>
  <div
    v-else-if="empty"
    class="rounded-[6px] border p-6 text-center"
    style="border-color: var(--line); background: var(--surface)"
  >
    <p class="font-semibold">{{ $t('state.emptyTitle') }}</p>
    <p class="mt-1 text-sm" style="color: var(--ink-soft)">{{ $t('state.emptyBody') }}</p>
  </div>
  <slot v-else />
</template>
