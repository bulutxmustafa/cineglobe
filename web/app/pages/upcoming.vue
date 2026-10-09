<script setup lang="ts">
import type { TitleItem } from '~/composables/useApi'

const { t } = useI18n()
useSeoMeta({
  title: () => t('upcoming.metaTitle'),
  description: () => t('upcoming.metaDescription'),
  ogTitle: () => t('upcoming.metaTitle'),
  ogDescription: () => t('upcoming.metaDescription'),
})
const media = ref<'both' | 'movie' | 'tv'>('both')
const { locale } = useI18n()
const base = useApiBase()
const { data, pending, error } = await useFetch<{
  groups: { key: string; items: TitleItem[] }[]
}>(() => `${base}/upcoming/`, {
  query: computed(() => ({ media_type: media.value, lang: locale.value })),
  key: 'upcoming',
  watch: [media],
})
const groups = computed(() => (data.value?.groups ?? []).filter((g) => g.items.length))
</script>

<template>
  <div class="container-page py-10">
    <h1 class="text-3xl">{{ t('upcoming.title') }}</h1>
    <p class="mt-2 max-w-2xl" style="color: var(--ink-soft)">{{ t('upcoming.lead') }}</p>
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
    <div class="mt-8">
      <ApiState :pending="pending" :error="error" :empty="!groups.length">
        <section v-for="g in groups" :key="g.key" class="mb-10" :aria-labelledby="`g-${g.key}`">
          <h2 :id="`g-${g.key}`" class="section-title">{{ t(`upcoming.groups.${g.key}`) }}</h2>
          <TitleGrid :items="g.items" />
        </section>
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
</style>
