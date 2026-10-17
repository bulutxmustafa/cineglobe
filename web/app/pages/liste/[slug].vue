<script setup lang="ts">
import type { TitleItem } from '~/composables/useApi'

interface Guide {
  slug: string
  media_type: 'movie' | 'tv'
  title: string
  intro: string
}
const route = useRoute()
const { t } = useI18n()
const localePath = useLocalePath()
const config = useRuntimeConfig()
const slug = String(route.params.slug)

const { data, error } = await useApiFetch<{ guide: Guide; results: TitleItem[] }>(`/guides/${slug}/`)
if (error.value?.statusCode === 404) {
  throw createError({ statusCode: 404, statusMessage: t('guides.notFound'), fatal: true })
}
const { data: all } = await useApiFetch<{ guides: Guide[] }>('/guides/')
const others = computed(() => (all.value?.guides ?? []).filter((g) => g.slug !== slug))

const title = computed(() => data.value?.guide.title ?? '')
const intro = computed(() => data.value?.guide.intro ?? '')
useSeoMeta({
  title: () => (title.value ? `${title.value} | FilmPusula` : 'FilmPusula'),
  description: () => intro.value,
  ogTitle: () => title.value,
  ogDescription: () => intro.value,
  ogImage: () => data.value?.results?.[0]?.backdrop_url || data.value?.results?.[0]?.poster_url || undefined,
})
useBreadcrumbs(() => [
  { name: t('guides.home'), path: '/' },
  { name: t('guides.title'), path: '/liste' },
  { name: title.value, path: `/liste/${slug}` },
])
// The list itself, so Google can show it as a list of films.
const site = String(config.public.siteUrl).replace(/\/$/, '')
useHead({
  script: [
    {
      type: 'application/ld+json',
      key: 'itemlist',
      innerHTML: computed(() =>
        JSON.stringify({
          '@context': 'https://schema.org',
          '@type': 'ItemList',
          name: title.value,
          itemListElement: (data.value?.results ?? []).slice(0, 20).map((item, i) => ({
            '@type': 'ListItem',
            position: i + 1,
            url: `${site}${localePath(`/title/${item.media_type}/${item.tmdb_id}`)}`,
            name: titleName(item),
          })),
        }),
      ),
    },
  ],
})
</script>

<template>
  <div v-if="data" class="container-page py-10">
    <nav class="crumbs" aria-label="breadcrumb">
      <NuxtLink :to="localePath('/')">{{ t('guides.home') }}</NuxtLink>
      <span aria-hidden="true">›</span>
      <NuxtLink :to="localePath('/liste')">{{ t('guides.title') }}</NuxtLink>
      <span aria-hidden="true">›</span>
      <span>{{ title }}</span>
    </nav>
    <h1 class="mt-3 text-3xl sm:text-4xl">{{ title }}</h1>
    <p class="mt-3 max-w-3xl text-[15px] leading-relaxed sm:text-base" style="color: var(--ink-soft)">{{ intro }}</p>

    <div class="mt-8">
      <ApiState :pending="false" :error="error" :empty="!data.results.length">
        <TitleGrid :items="data.results" />
      </ApiState>
    </div>

    <section v-if="others.length" class="mt-16" aria-labelledby="others-h">
      <div class="sec-head"><h2 id="others-h">{{ t('guides.others') }}</h2></div>
      <ul class="mt-5 flex flex-wrap gap-2.5">
        <li v-for="g in others" :key="g.slug">
          <NuxtLink :to="localePath(`/liste/${g.slug}`)" class="chip">{{ g.title }}</NuxtLink>
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.crumbs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 13px;
  color: var(--ink-soft);
}
.crumbs a:hover {
  color: var(--accent);
  text-decoration: underline;
}
</style>
