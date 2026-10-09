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
  ogSiteName: 'CINEGLOB',
})
useHead({
  script: [
    {
      type: 'application/ld+json',
      innerHTML: JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'WebSite',
        name: 'CINEGLOB',
        alternateName: 'CINEGLOB Film Önerileri ve Keşif Platformu',
        url: config.public.siteUrl,
      }),
    },
  ],
})

const { data: cols, pending: colsPending, error: colsError } = await useApiFetch<{ collections: Collection[] }>('/collections/')
const { data: up, pending: upPending, error: upError } = await useApiFetch<{ results: TitleItem[] }>('/upcoming/', { media_type: 'both' })
const { data: wall } = await useApiFetch<{ results: TitleItem[] }>('/popular/')
const posters = computed(() => (wall.value?.results ?? []).map((r) => r.poster_url || '').filter(Boolean))
const upcoming = computed(() => (up.value?.results ?? []).filter((i) => i.poster_url).slice(0, 5))
</script>

<template>
  <div>
    <section class="relative overflow-hidden" style="background: var(--night)">
      <ClientOnly><PosterWall :posters="posters" /></ClientOnly>
      <div
        class="absolute inset-0"
        style="background: radial-gradient(ellipse at 50% 45%, rgb(42 17 33 / 82%) 0%, rgb(42 17 33 / 45%) 70%, rgb(42 17 33 / 15%) 100%), linear-gradient(180deg, rgb(42 17 33 / 0%) 60%, rgb(42 17 33 / 90%) 100%)"
      />
      <div class="container-page relative py-12 text-center sm:py-20">
        <p class="inline-block rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em]" style="background: var(--grad); color: #1c1306">
          {{ t('hero.eyebrow') }}
        </p>
        <h1 class="mx-auto mt-4 max-w-2xl text-[1.6rem] leading-[1.2] text-white sm:text-[2.2rem]">
          {{ t('hero.title') }}
        </h1>
        <p class="mx-auto mt-3 max-w-xl text-sm text-white/75 sm:text-base">{{ t('hero.lead') }}</p>
        <div class="mx-auto mt-8 max-w-2xl text-left">
          <SearchBox examples dark />
        </div>
        <NuxtLink :to="localePath('/lucky')" class="btn btn-glass mt-6">🎡 {{ t('nav.lucky') }}</NuxtLink>
      </div>
    </section>

    <section class="container-page mt-12" aria-labelledby="cols-h">
      <div class="flex items-end justify-between gap-4">
        <div>
          <h2 id="cols-h" class="text-2xl">{{ t('home.collections') }}</h2>
          <p class="mt-1 text-sm" style="color: var(--ink-soft)">{{ t('home.collectionsLead') }}</p>
        </div>
        <NuxtLink :to="localePath('/collections')" class="text-sm font-medium underline underline-offset-4">{{ t('home.allCollections') }}</NuxtLink>
      </div>
      <div class="mt-5">
        <ApiState :pending="colsPending" :error="colsError" :empty="!cols?.collections?.length">
          <ul class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <li v-for="(c, i) in cols?.collections" :key="c.slug">
              <CollectionCard :collection="c" :index="i + 1" />
            </li>
          </ul>
        </ApiState>
      </div>
    </section>

    <section class="container-page mt-14" aria-labelledby="up-h">
      <div class="flex items-end justify-between gap-4">
        <div>
          <h2 id="up-h" class="text-2xl">{{ t('home.upcoming') }}</h2>
          <p class="mt-1 text-sm" style="color: var(--ink-soft)">{{ t('home.upcomingLead') }}</p>
        </div>
        <NuxtLink :to="localePath('/upcoming')" class="text-sm font-medium underline underline-offset-4">{{ t('home.allUpcoming') }}</NuxtLink>
      </div>
      <div class="mt-5">
        <ApiState :pending="upPending" :error="upError" :empty="!upcoming.length">
          <TitleGrid :items="upcoming" />
        </ApiState>
      </div>
    </section>

    <section class="container-page mt-14" aria-labelledby="how-h">
      <h2 id="how-h" class="text-2xl">{{ t('home.howTitle') }}</h2>
      <ol class="mt-5 grid gap-4 sm:grid-cols-3">
        <li
          v-for="(step, i) in ($tm('home.how') as { t: string; d: string }[])"
          :key="i"
          class="rounded-[18px] border p-6"
          :style="{ borderColor: 'transparent', background: ['linear-gradient(160deg,#fff1d6,#ffd9a8)', 'linear-gradient(160deg,#ffe1dc,#ffb8ab)', 'linear-gradient(160deg,#d8f3ee,#a6e3d8)'][i], boxShadow: '0 10px 26px rgb(120 60 20 / 14%)' }"
        >
          <span class="inline-flex h-10 w-10 items-center justify-center rounded-full font-serif text-xl font-semibold" style="background: var(--grad); color: #1c1306">{{ i + 1 }}</span>
          <h3 class="mt-3 font-sans text-lg font-semibold">{{ $rt(step.t as any) }}</h3>
          <p class="mt-1 text-sm" style="color: var(--ink-soft)">{{ $rt(step.d as any) }}</p>
        </li>
      </ol>
    </section>
  </div>
</template>
