<script setup lang="ts">
import type { Collection, TitleItem } from '~/composables/useApi'

const { t } = useI18n()
const localePath = useLocalePath()
const config = useRuntimeConfig()

useSeoMeta({
  title: () => t('site.homeTitle'),
  description: () => t('site.homeDescription'),
  ogTitle: () => t('site.homeTitle'),
  ogDescription: () => t('site.homeDescription'),
  ogType: 'website',
  ogSiteName: 'FilmPusula',
})
useHead({
  script: [
    {
      type: 'application/ld+json',
      innerHTML: JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'WebSite',
        name: 'FilmPusula',
        alternateName: 'FilmPusula Film Önerileri ve Keşif Platformu',
        url: config.public.siteUrl,
      }),
    },
  ],
})

const { data: cols, pending: colsPending, error: colsError } = await useApiFetch<{ collections: Collection[] }>('/collections/')
const { data: wall } = await useApiFetch<{ results: TitleItem[] }>('/popular/')
const posters = computed(() => (wall.value?.results ?? []).map((r) => r.poster_url || '').filter(Boolean))
const trending = computed(() => (wall.value?.results ?? []).filter((r) => r.poster_url).slice(0, 6))
const { data: up, pending: upPending, error: upError } = await useApiFetch<{ results: TitleItem[] }>('/upcoming/', { media_type: 'both' })
const upcoming = computed(() => (up.value?.results ?? []).filter((i) => i.poster_url).slice(0, 5))
</script>

<template>
  <div>
    <!-- Hero: real posters keep rolling behind a cinematic veil -->
    <section class="hero relative overflow-hidden">
      <ClientOnly><PosterWall :posters="posters" /></ClientOnly>
      <div class="veil absolute inset-0" />
      <div class="container-page relative pb-40 pt-16 sm:pb-48 sm:pt-24">
        <div class="max-w-2xl">
          <p class="eyebrow">{{ t('hero.eyebrow') }}</p>
          <h1 class="mt-6 text-[2.3rem] leading-[1.06] sm:text-[3.4rem] lg:text-[4rem]" style="color: #fff">{{ t('hero.title') }}</h1>
          <p class="mt-5 max-w-xl text-base leading-relaxed sm:text-lg" style="color: #d3dae6">{{ t('hero.lead') }}</p>
          <div class="mt-8 flex flex-wrap gap-3">
            <a href="#sans" class="btn btn-primary min-h-[52px] px-7 text-[15px]">{{ t('hero.surprise') }}</a>
            <NuxtLink :to="localePath('/collections')" class="btn btn-glass min-h-[52px] px-7 text-[15px]">{{ t('home.allCollections') }}</NuxtLink>
          </div>
        </div>
      </div>
    </section>

    <!-- Search and lucky wheel side by side, overlapping the hero -->
    <section class="container-page relative z-10 -mt-28 sm:-mt-36">
      <div class="grid grid-cols-[minmax(0,1fr)] items-stretch gap-5 lg:grid-cols-[minmax(0,1.45fr)_minmax(0,1fr)]">
        <div class="flex flex-col gap-5">
          <SearchBox examples dark />
          <div v-if="trending.length" class="trend flex-1">
            <div class="flex items-center justify-between">
              <p class="font-serif text-[1.15rem] font-bold" style="color: #fbf6ec">{{ t('home.popular') }}</p>
              <span class="text-xs font-semibold" style="color: var(--ink-faint)">TMDB</span>
            </div>
            <ul class="mt-4 grid grid-cols-3 gap-3 sm:grid-cols-6">
              <li v-for="item in trending" :key="`${item.media_type}-${item.tmdb_id}`">
                <NuxtLink :to="localePath(`/title/${item.media_type}/${item.tmdb_id}`)" class="mini-poster block" :title="titleName(item)">
                  <img :src="item.poster_url!" :alt="titleName(item)" width="120" height="180" loading="lazy" />
                  <span v-if="item.vote_average" class="rate">★ {{ item.vote_average.toFixed(1) }}</span>
                </NuxtLink>
              </li>
            </ul>
          </div>
        </div>
        <LuckyPicker compact />
      </div>
    </section>

    <section class="container-page mt-16" aria-labelledby="cols-h">
      <div class="sec-head flex items-end justify-between gap-4">
        <div>
          <h2 id="cols-h">{{ t('home.collections') }}</h2>
          <p class="mt-1.5 text-sm" style="color: var(--ink-soft)">{{ t('home.collectionsLead') }}</p>
        </div>
        <NuxtLink :to="localePath('/collections')" class="sec-link whitespace-nowrap">{{ t('home.allCollections') }} →</NuxtLink>
      </div>
      <div class="mt-6">
        <ApiState :pending="colsPending && !cols?.collections?.length" :error="colsError" :empty="!cols?.collections?.length">
          <ul class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            <li v-for="(c, i) in cols?.collections" :key="c.slug" class="rise" :style="{ animationDelay: `${i * 60}ms` }">
              <CollectionCard :collection="c" :index="i + 1" />
            </li>
          </ul>
        </ApiState>
      </div>
    </section>

    <section class="container-page mt-16" aria-labelledby="up-h">
      <div class="sec-head flex items-end justify-between gap-4">
        <div>
          <h2 id="up-h">{{ t('home.upcoming') }}</h2>
          <p class="mt-1.5 text-sm" style="color: var(--ink-soft)">{{ t('home.upcomingLead') }}</p>
        </div>
        <NuxtLink :to="localePath('/upcoming')" class="sec-link whitespace-nowrap">{{ t('home.allUpcoming') }} →</NuxtLink>
      </div>
      <div class="mt-6">
        <ApiState :pending="upPending && !upcoming.length" :error="upError" :empty="!upcoming.length">
          <TitleGrid :items="upcoming" />
        </ApiState>
      </div>
    </section>

    <section class="container-page mb-4 mt-16" aria-labelledby="how-h">
      <div class="sec-head"><h2 id="how-h">{{ t('home.howTitle') }}</h2></div>
      <ol class="mt-6 grid gap-5 sm:grid-cols-3">
        <li v-for="(step, i) in ($tm('home.how') as { t: string; d: string }[])" :key="i" class="step">
          <span class="num">{{ i + 1 }}</span>
          <h3 class="mt-4 font-sans text-lg font-semibold" style="color: #fbf6ec">{{ $rt(step.t as any) }}</h3>
          <p class="mt-1.5 text-sm leading-relaxed" style="color: var(--ink-soft)">{{ $rt(step.d as any) }}</p>
        </li>
      </ol>
    </section>
  </div>
</template>

<style scoped>
.hero {
  background: #070d1a;
}
.veil {
  background:
    radial-gradient(ellipse 55% 60% at 85% 20%, rgb(242 160 80 / 22%) 0%, transparent 65%),
    linear-gradient(90deg, rgb(7 13 26 / 96%) 0%, rgb(7 13 26 / 86%) 38%, rgb(7 13 26 / 50%) 72%, rgb(7 13 26 / 62%) 100%),
    linear-gradient(180deg, rgb(7 13 26 / 35%) 0%, transparent 30%, rgb(7 13 26 / 70%) 78%, #070d1a 100%);
}
.trend {
  padding: 22px 26px 24px;
  border-radius: 24px;
  background: var(--box);
  border: 1px solid rgb(255 255 255 / 9%);
}
.mini-poster {
  position: relative;
  overflow: hidden;
  border-radius: 10px;
  border: 1px solid rgb(255 255 255 / 10%);
  transition: transform 260ms var(--spring), border-color 200ms var(--ease);
}
.mini-poster img {
  width: 100%;
  aspect-ratio: 2 / 3;
  object-fit: cover;
  display: block;
}
.mini-poster:hover {
  transform: translateY(-4px);
  border-color: var(--gold);
}
.rate {
  position: absolute;
  left: 6px;
  top: 6px;
  padding: 1px 6px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: var(--gold);
  background: rgb(7 13 26 / 80%);
}
.step {
  padding: 24px;
  border-radius: 20px;
  background: var(--box);
  border: 1px solid rgb(255 255 255 / 8%);
}
.num {
  display: inline-flex;
  width: 44px;
  height: 44px;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  font-family: var(--font-serif);
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--gold);
  border: 1.5px solid rgb(242 192 102 / 55%);
  background: rgb(242 192 102 / 8%);
}
</style>
