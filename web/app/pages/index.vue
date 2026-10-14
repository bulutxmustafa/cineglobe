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
const { data: up, pending: upPending, error: upError } = await useApiFetch<{ results: TitleItem[] }>('/upcoming/', { media_type: 'both' })
const upcoming = computed(() => (up.value?.results ?? []).filter((i) => i.poster_url).slice(0, 5))
</script>

<template>
  <div>
    <!-- Hero: posters roll behind; search on the left, the lucky wheel on the right -->
    <section class="hero relative flex min-h-[calc(100svh-68px)] items-center overflow-hidden">
      <ClientOnly><PosterWall :posters="posters" /></ClientOnly>
      <div class="veil absolute inset-0" />
      <div class="container-page relative w-full pb-20 pt-10 sm:pb-24 sm:pt-14">
        <div class="grid grid-cols-[minmax(0,1fr)] items-center gap-8 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,0.7fr)]">
          <div class="text-center lg:text-left">
            <p class="eyebrow">{{ t('hero.eyebrow') }}</p>
            <h1 class="mt-5 max-w-2xl text-[1.25rem] leading-[1.25] sm:text-[1.6rem]" style="color: #fff; text-shadow: 0 2px 14px rgb(0 0 0 / 60%)">{{ t('hero.title') }}</h1>
            <div class="mt-6 max-w-2xl text-left"><SearchBox examples dark /></div>
          </div>
          <LuckyPicker compact />
        </div>
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
    radial-gradient(ellipse at 30% 45%, rgb(5 10 20 / 55%) 0%, transparent 65%),
    linear-gradient(135deg, rgb(7 13 26 / 35%) 0%, rgb(13 23 41 / 22%) 100%),
    linear-gradient(180deg, transparent 75%, #070d1a 100%);
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
