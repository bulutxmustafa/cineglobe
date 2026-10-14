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
  title: () => `${name.value}${year.value ? ` (${year.value})` : ''} | FilmPusula`,
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
          genre: data.value?.genres?.map((g) => g.name),
          aggregateRating:
            data.value?.vote_average && data.value?.vote_count
              ? { '@type': 'AggregateRating', ratingValue: Number(data.value.vote_average.toFixed(1)), ratingCount: data.value.vote_count, bestRating: 10, worstRating: 0 }
              : undefined,
        }),
      ),
    },
  ],
})
</script>

<template>
  <article v-if="data" class="detail">
    <!-- Cinematic hero: the backdrop slowly drifts (Ken Burns), poster and facts sit on top -->
    <section class="hero relative overflow-hidden">
      <img v-if="data.backdrop_url" :src="data.backdrop_url" alt="" class="bg" width="1280" height="720" />
      <img v-else-if="data.poster_url" :src="data.poster_url" alt="" class="bg bg-blur" width="342" height="513" />
      <div class="shine" aria-hidden="true" />
      <div class="veil absolute inset-0" aria-hidden="true" />
      <div class="container-page relative py-12 sm:py-16 lg:py-20">
        <div class="grid items-end gap-8 md:grid-cols-[300px_minmax(0,1fr)] lg:gap-12">
          <div class="mx-auto w-56 md:w-full">
            <div class="poster aspect-[2/3] overflow-hidden rounded-[16px]">
              <img v-if="data.poster_url" :src="data.poster_url" :alt="t('title.posterAlt', { name })" class="h-full w-full object-cover" width="342" height="513" />
            </div>
          </div>
          <div class="text-center md:text-left">
            <p class="eyebrow">{{ type === 'tv' ? t('title.tv') : t('title.movie') }}</p>
            <h1 class="mt-4 text-[2.2rem] leading-[1.05] sm:text-[3rem] lg:text-[3.6rem]" style="color: #fff">
              {{ name }} <span v-if="year" class="font-normal" style="color: #c9d3e4">({{ year }})</span>
            </h1>
            <p v-if="data.original_title && data.original_title !== name" class="mt-2 text-sm" style="color: #c9d3e4">
              {{ t('title.originalTitle') }}: {{ data.original_title }}
            </p>
            <ul class="mt-4 flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-sm md:justify-start" style="color: #dbe3ef">
              <li v-if="data.vote_average" class="font-bold" style="color: var(--gold)">★ {{ data.vote_average.toFixed(1) }} <span class="font-normal" style="color: #c9d3e4">· {{ t('title.votes', { n: data.vote_count }) }}</span></li>
              <li v-if="data.tv_details">{{ t('title.seasons', { n: data.tv_details.number_of_seasons }) }} · {{ t('title.episodes', { n: data.tv_details.number_of_episodes }) }}</li>
              <li v-if="data.tv_details?.episode_runtime">{{ t('title.runtime', { n: data.tv_details.episode_runtime }) }}</li>
            </ul>
            <ul v-if="data.genres?.length" class="mt-4 flex flex-wrap justify-center gap-2 md:justify-start">
              <li v-for="g in data.genres" :key="g.id" class="chip chip-dark !min-h-[30px] text-xs">{{ g.name }}</li>
            </ul>
            <p class="mx-auto mt-5 max-w-2xl text-[15px] leading-relaxed sm:text-base md:mx-0" style="color: #e3e9f2">
              {{ data.display_overview || t('title.noOverview') }}
            </p>
            <div class="mt-7 flex flex-wrap justify-center gap-2.5 md:justify-start">
              <ClientOnly><TrailerButton :media-type="data.media_type" :tmdb-id="data.tmdb_id" :title="name" /></ClientOnly>
              <FavoriteButton :item="{ media_type: data.media_type, tmdb_id: data.tmdb_id, title: data.title, display_title: data.display_title, poster_url: data.poster_url, release_date: data.release_date ?? undefined, vote_average: data.vote_average ?? undefined }" />
              <NuxtLink :to="localePath({ path: '/search', query: { q: name } })" class="btn btn-glass">
                {{ t('title.more') }}
              </NuxtLink>
            </div>
          </div>
        </div>
      </div>
    </section>
  </article>
</template>

<style scoped>
.hero {
  background: var(--bg);
  min-height: calc(100svh - 68px);
  display: flex;
  align-items: center;
}
.hero > .container-page {
  width: 100%;
}
.bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center 30%;
  transform-origin: 60% 40%;
  animation: drift 32s ease-in-out infinite alternate;
}
.bg-blur {
  filter: blur(28px) saturate(1.2);
  transform: scale(1.2);
  animation: none;
}
@keyframes drift {
  from {
    transform: scale(1.05) translate3d(0, 0, 0);
  }
  to {
    transform: scale(1.16) translate3d(-2.5%, -1.5%, 0);
  }
}
.shine {
  position: absolute;
  inset: -20%;
  background: linear-gradient(115deg, transparent 40%, rgb(255 214 140 / 10%) 50%, transparent 60%);
  animation: sweep 14s ease-in-out infinite;
  pointer-events: none;
}
@keyframes sweep {
  0%,
  15% {
    transform: translateX(-60%);
  }
  85%,
  100% {
    transform: translateX(60%);
  }
}
.veil {
  background:
    linear-gradient(90deg, rgb(10 24 56 / 92%) 0%, rgb(10 24 56 / 70%) 40%, rgb(10 24 56 / 25%) 75%, rgb(10 24 56 / 35%) 100%),
    linear-gradient(180deg, rgb(10 24 56 / 35%) 0%, transparent 30%, rgb(10 24 56 / 55%) 70%, rgb(10 24 56 / 88%) 88%, #0a1838 100%);
}
.poster {
  border: 1px solid rgb(255 255 255 / 18%);
  box-shadow: 0 30px 60px rgb(0 0 0 / 55%), 0 0 0 6px rgb(255 255 255 / 4%);
  background: #13244a;
}
/* The hero runs straight into the footer (same navy), no light strip in between. */
.detail {
  margin-bottom: -4rem;
}
@media (prefers-reduced-motion: reduce) {
  .bg,
  .shine {
    animation: none;
  }
}
</style>
