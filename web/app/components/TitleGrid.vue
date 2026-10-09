<script setup lang="ts">
import type { TitleItem } from '~/composables/useApi'

defineProps<{ items: TitleItem[]; showReason?: boolean }>()
</script>

<template>
  <ul class="grid grid-cols-2 gap-x-4 gap-y-7 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
    <li v-for="item in items" :key="`${item.media_type}:${item.tmdb_id}`">
      <TitleCard :item="item" :show-reason="showReason" />
    </li>
  </ul>
</template>
