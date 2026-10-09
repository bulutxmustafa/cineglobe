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
const { data: wall } = await useApiFetch<{ results: TitleItem[] }>('/collections/never-boring/')
const posters = computed(() => (wall.value?.results ?? []).map((r) => r.poster_url || '').filter(Boolean))
const upcoming = computed(() => (up.value?.results ?? []).filter((i) => i.poster_url).slice(0, 5))
</script>

<template>
  <div>
    <section class="relative overflow-hidden" style="background: var(--night)">
      <ClientOnly><PosterWall :posters="posters" /></ClientOnly>
      <div
        class="absolute inset-0"
        style="background: radial-gradient(ellipse at 20% 30%, rgb(109 40 217 / 55%), transparent 60%), linear-gradient(180deg, rgb(13 11 31 / 55%), rgb(13 11 31 / 92%))"
      />
      <div class="container-page relative py-16 sm:py-24">
        <p class="inline-block rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-white" style="background: var(--grad)">
          {{ t('hero.eyebrow') }}
        </p>
        <h1 class="mt-4 max-w-3xl text-[2.2rem] leading-[1.1] text-white sm:text-[3.4rem]">
          {{ t('hero.title') }}
        </h1>
        <p class="mt-5 max-w-2xl text-base text-white/80 sm:text-lg">{{ t('hero.lead') }}</p>
        <div class="mt-8 max-w-3xl">
          <SearchBox examples dark />
        </div>
        <NuxtLink :to="localePath('/lucky')" class="btn btn-glass mt-6">🌍 {{ t('nav.lucky') }}</NuxtLink>
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
          class="rounded-[16px] p-6 text-white"
          :style="{ background: ['linear-gradient(135deg,#e11d48,#f97316)', 'linear-gradient(135deg,#6d28d9,#06b6d4)', 'linear-gradient(135deg,#0ea5e9,#6366f1)'][i], boxShadow: '0 10px 28px rgb(13 11 31 / 16%)' }"
        >
          <span class="font-serif text-4xl font-semibold opacity-90">{{ i + 1 }}</span>
          <h3 class="mt-2 font-sans text-lg font-semibold">{{ $rt(step.t as any) }}</h3>
          <p class="mt-1 text-sm text-white/90">{{ $rt(step.d as any) }}</p>
        </li>
      </ol>
    </section>
  </div>
</template>
