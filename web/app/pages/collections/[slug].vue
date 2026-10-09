<script setup lang="ts">
import type { Collection, TitleItem } from '~/composables/useApi'

const route = useRoute()
const { t, locale } = useI18n()
const base = useApiBase()
const localePath = useLocalePath()
const slug = String(route.params.slug)
const media = ref<'both' | 'movie' | 'tv'>('both')
const page = ref(1)

const { data, pending, error } = await useFetch<{
  collection: Collection
  total_pages: number
  results: TitleItem[]
}>(() => `${base}/collections/${slug}/`, {
  query: computed(() => ({ media_type: media.value, page: page.value, lang: locale.value })),
  key: `col:${slug}`,
  watch: [media, page],
})

if (error.value?.statusCode === 404) {
  throw createError({ statusCode: 404, statusMessage: t('collections.notFound'), fatal: true })
}

const name = computed(() => data.value?.collection.name ?? '')
useSeoMeta({
  title: () => (name.value ? `${name.value} | CINEGLOB` : 'CINEGLOB'),
  description: () => data.value?.collection.description ?? '',
  ogTitle: () => name.value,
  ogDescription: () => data.value?.collection.description ?? '',
})
watch(media, () => (page.value = 1))
</script>

<template>
  <div class="container-page py-10">
    <nav class="text-sm" style="color: var(--ink-soft)" aria-label="breadcrumb">
      <NuxtLink :to="localePath('/collections')" class="underline underline-offset-4">{{ t('collections.title') }}</NuxtLink>
    </nav>
    <h1 class="mt-2 text-3xl">{{ name }}</h1>
    <p class="mt-2 max-w-2xl" style="color: var(--ink-soft)">{{ data?.collection.description }}</p>

    <div class="mt-5 flex flex-wrap gap-2" role="group" :aria-label="t('search.type')">
      <button
        v-for="opt in (['both', 'movie', 'tv'] as const)"
        :key="opt"
        type="button"
        class="chip"
        :class="{ 'chip-on': media === opt }"
        :aria-pressed="media === opt"
        @click="media = opt"
      >{{ t(`search.types.${opt}`) }}</button>
    </div>

    <div class="mt-6">
      <ApiState :pending="pending" :error="error" :empty="!data?.results?.length">
        <TitleGrid :items="data?.results ?? []" show-reason />
        <div v-if="(data?.total_pages ?? 1) > 1" class="mt-8 flex items-center justify-center gap-3 text-sm">
          <button class="btn btn-quiet" :disabled="page <= 1" @click="page--">{{ t('collections.prev') }}</button>
          <span>{{ t('collections.pageOf', { page, total: data?.total_pages }) }}</span>
          <button class="btn btn-quiet" :disabled="page >= (data?.total_pages ?? 1)" @click="page++">{{ t('collections.next') }}</button>
        </div>
      </ApiState>
    </div>
  </div>
</template>

<style scoped>
.chip-on {
  border-color: var(--ink);
  color: var(--ink);
  font-weight: 600;
}
button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
