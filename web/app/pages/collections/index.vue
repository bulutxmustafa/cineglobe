<script setup lang="ts">
import type { Collection } from '~/composables/useApi'

const { t } = useI18n()
useSeoMeta({
  title: () => t('collections.metaTitle'),
  description: () => t('collections.metaDescription'),
  ogTitle: () => t('collections.metaTitle'),
  ogDescription: () => t('collections.metaDescription'),
})
const { data, pending, error } = await useApiFetch<{ collections: Collection[] }>('/collections/')
</script>

<template>
  <div class="container-page py-10">
    <h1 class="text-3xl">{{ t('collections.title') }}</h1>
    <p class="mt-2 max-w-2xl" style="color: var(--ink-soft)">{{ t('collections.lead') }}</p>
    <div class="mt-6">
      <ApiState :pending="pending" :error="error" :empty="!data?.collections?.length">
        <ul class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <li v-for="(c, i) in data?.collections" :key="c.slug"><CollectionCard :collection="c" :index="i + 1" /></li>
        </ul>
      </ApiState>
    </div>
  </div>
</template>
