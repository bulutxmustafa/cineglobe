<script setup lang="ts">
interface Detail {
  media_type: 'movie' | 'tv'
  tmdb_id: number
  display_title: string
  title: string
  original_title: string
  display_overview: string
  poster_url: string | null
  backdrop_url: string | null
  vote_average: number | null
  vote_count: number | null
  release_date: string | null
  genres?: { id: number; name: string }[]
  tv_details?: { number_of_seasons: number; number_of_episodes: number; episode_runtime: number | null } | null
}

const route = useRoute()
const { t, locale } = useI18n()
const localePath = useLocalePath()
const base = useApiBase()
const config = useRuntimeConfig()
const type = String(route.params.type)
const id = String(route.params.id)

if (type !== 'movie' && type !== 'tv') {
  throw createError({ statusCode: 404, fatal: true })
}

const { data, error } = await useFetch<Detail>(`${base}/titles/${type}/${id}/`, {
  query: { lang: locale.value },
  key: `title:${type}:${id}:${locale.value}`,
})
if (error.value) {
  throw createError({ statusCode: error.value.statusCode === 404 ? 404 : 503, statusMessage: t('title.notFound'), fatal: true })
}

const name = computed(() => data.value?.display_title || data.value?.title || '')
const year = computed(() => yearOf(data.value?.release_date))
const description = computed(() => (data.value?.display_overview || t('title.noOverview')).slice(0, 160))
useSeoMeta({
  title: () => `${name.value}${year.value ? ` (${year.value})` : ''} | CINEGLOB`,
  description: () => description.value,
  ogTitle: () => name.value,
  ogDescription: () => description.value,
  ogImage: () => data.value?.backdrop_url || data.value?.poster_url || undefined,
  ogType: () => (type === 'tv' ? 'video.tv_show' : 'video.movie'),
})
useHead({
  script: [
    {
      type: 'application/ld+json',
      innerHTML: computed(() =>
        JSON.stringify({
          '@context': 'https://schema.org',
          '@type': type === 'tv' ? 'TVSeries' : 'Movie',
          name: name.value,
          image: data.value?.poster_url || undefined,
          description: data.value?.display_overview || undefined,
          datePublished: data.value?.release_date || undefined,
          url: `${config.public.siteUrl}${route.path}`,
        }),
      ),
    },
  ],
})
</script>

<template>
  <article v-if="data">
    <div v-if="data.backdrop_url" class="relative h-48 overflow-hidden sm:h-72" style="background: var(--ink)">
      <img :src="data.backdrop_url" alt="" class="h-full w-full object-cover opacity-80" width="1280" height="720" />
    </div>
    <div class="container-page py-8">
      <div class="grid gap-8 md:grid-cols-[240px_1fr]" :class="{ 'md:-mt-24': data.backdrop_url }">
        <div class="relative z-10 mx-auto w-48 md:w-full">
          <div class="aspect-[2/3] overflow-hidden rounded-[6px]" style="background: var(--line); box-shadow: var(--shadow)">
            <img v-if="data.poster_url" :src="data.poster_url" :alt="t('title.posterAlt', { name })" class="h-full w-full object-cover" width="342" height="513" />
          </div>
        </div>
        <div class="md:pt-28" :class="{ 'md:pt-28': data.backdrop_url, 'md:pt-0': !data.backdrop_url }">
          <p class="text-sm font-semibold uppercase tracking-wide" style="color: var(--accent)">
            {{ type === 'tv' ? t('title.tv') : t('title.movie') }}
          </p>
          <h1 class="mt-1 text-3xl sm:text-4xl">
            {{ name }} <span v-if="year" class="font-normal" style="color: var(--ink-faint)">({{ year }})</span>
          </h1>
          <p
            v-if="data.original_title && data.original_title !== name"
            class="mt-1 text-sm"
            style="color: var(--ink-soft)"
          >{{ t('title.originalTitle') }}: {{ data.original_title }}</p>

          <ul class="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm" style="color: var(--ink-soft)">
            <li v-if="data.vote_average" class="font-semibold" style="color: var(--star)">★ {{ data.vote_average.toFixed(1) }} <span class="font-normal" style="color: var(--ink-soft)">· {{ t('title.votes', { n: data.vote_count }) }}</span></li>
            <li v-if="data.tv_details">{{ t('title.seasons', { n: data.tv_details.number_of_seasons }) }} · {{ t('title.episodes', { n: data.tv_details.number_of_episodes }) }}</li>
            <li v-if="data.tv_details?.episode_runtime">{{ t('title.runtime', { n: data.tv_details.episode_runtime }) }}</li>
          </ul>
          <ul v-if="data.genres?.length" class="mt-3 flex flex-wrap gap-2">
            <li v-for="g in data.genres" :key="g.id" class="chip !min-h-[30px] text-xs">{{ g.name }}</li>
          </ul>

          <h2 class="mt-6 text-xl">{{ t('title.overview') }}</h2>
          <p class="mt-2 max-w-2xl leading-relaxed">{{ data.display_overview || t('title.noOverview') }}</p>

          <div class="mt-6 flex flex-wrap gap-2">
            <FavoriteButton :item="{ media_type: data.media_type, tmdb_id: data.tmdb_id, title: data.title, display_title: data.display_title, poster_url: data.poster_url, release_date: data.release_date ?? undefined, vote_average: data.vote_average ?? undefined }" />
            <NuxtLink :to="localePath({ path: '/search', query: { q: name } })" class="btn btn-quiet">
              {{ t('title.more') }}
            </NuxtLink>
          </div>
        </div>
      </div>
    </div>
  </article>
</template>
