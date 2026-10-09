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
    <!-- Hero: posters under a navy veil that melts into the next section -->
    <section class="relative overflow-hidden" style="background: var(--bg)">
      <ClientOnly><PosterWall :posters="posters" /></ClientOnly>
      <div
        class="absolute inset-0"
        style="background: radial-gradient(ellipse at 50% 42%, rgb(16 25 35 / 80%) 0%, rgb(16 25 35 / 55%) 62%, rgb(16 25 35 / 35%) 100%), linear-gradient(180deg, rgb(16 25 35 / 25%) 0%, rgb(16 25 35 / 0%) 35%, rgb(23 37 54 / 100%) 100%)"
      />
      <div class="container-page relative pb-16 pt-12 text-center sm:pb-24 sm:pt-20">
        <p class="inline-block rounded-full border px-3.5 py-1 text-xs font-bold uppercase tracking-[0.16em]" style="border-color: rgb(242 185 80 / 55%); color: var(--gold); background: rgb(16 25 35 / 55%)">
          {{ t('hero.eyebrow') }}
        </p>
        <h1 class="mx-auto mt-5 max-w-2xl text-[1.9rem] leading-[1.12] sm:text-[2.7rem]" style="text-shadow: 0 2px 18px rgb(0 0 0 / 55%)">
          {{ t('hero.title') }}
        </h1>
        <p class="mx-auto mt-4 max-w-xl text-[15px] sm:text-base" style="color: #d5dde6; text-shadow: 0 1px 10px rgb(0 0 0 / 60%)">{{ t('hero.lead') }}</p>
        <div class="mx-auto mt-8 max-w-2xl text-left">
          <SearchBox examples dark />
        </div>
        <NuxtLink :to="localePath('/lucky')" class="btn btn-quiet mt-6" style="background: rgb(16 25 35 / 70%)">{{ t('hero.surprise') }}</NuxtLink>
      </div>
    </section>

    <section class="pb-14 pt-2" style="background: var(--bg-2)" aria-labelledby="cols-h">
      <div class="container-page">
        <div class="flex items-end justify-between gap-4">
          <div>
            <h2 id="cols-h" class="text-2xl sm:text-[1.7rem]">{{ t('home.collections') }}</h2>
            <p class="mt-1 text-sm" style="color: var(--ink-soft)">{{ t('home.collectionsLead') }}</p>
          </div>
          <NuxtLink :to="localePath('/collections')" class="text-sm font-semibold underline underline-offset-4" style="color: var(--gold)">{{ t('home.allCollections') }}</NuxtLink>
        </div>
        <div class="mt-6">
          <ApiState :pending="colsPending" :error="colsError" :empty="!cols?.collections?.length">
            <ul class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <li v-for="(c, i) in cols?.collections" :key="c.slug" class="rise" :style="{ animationDelay: `${i * 60}ms` }">
                <CollectionCard :collection="c" :index="i + 1" />
              </li>
            </ul>
          </ApiState>
        </div>
      </div>
    </section>

    <section class="surface-light -mt-6 rounded-t-[28px] pb-14 pt-12" aria-labelledby="up-h">
      <div class="container-page">
        <div class="flex items-end justify-between gap-4">
          <div>
            <h2 id="up-h" class="text-2xl sm:text-[1.7rem]">{{ t('home.upcoming') }}</h2>
            <p class="mt-1 text-sm" style="color: var(--ink-soft)">{{ t('home.upcomingLead') }}</p>
          </div>
          <NuxtLink :to="localePath('/upcoming')" class="text-sm font-semibold underline underline-offset-4" style="color: var(--accent)">{{ t('home.allUpcoming') }}</NuxtLink>
        </div>
        <div class="mt-6">
          <ApiState :pending="upPending" :error="upError" :empty="!upcoming.length">
            <TitleGrid :items="upcoming" />
          </ApiState>
        </div>
      </div>
    </section>

    <section class="container-page py-14" aria-labelledby="how-h">
      <h2 id="how-h" class="text-2xl sm:text-[1.7rem]">{{ t('home.howTitle') }}</h2>
      <ol class="mt-6 grid gap-4 sm:grid-cols-3">
        <li
          v-for="(step, i) in ($tm('home.how') as { t: string; d: string }[])"
          :key="i"
          class="rounded-[18px] border p-6"
          style="border-color: var(--border); background: var(--elevated); box-shadow: var(--shadow)"
        >
          <span class="inline-flex h-10 w-10 items-center justify-center rounded-full font-serif text-xl font-bold" :style="{ background: i === 1 ? 'var(--teal)' : 'var(--gold)', color: i === 1 ? '#fff' : '#1a1305' }">{{ i + 1 }}</span>
          <h3 class="mt-3 font-sans text-lg font-semibold">{{ $rt(step.t as any) }}</h3>
          <p class="mt-1 text-sm" style="color: var(--ink-soft)">{{ $rt(step.d as any) }}</p>
        </li>
      </ol>
    </section>
  </div>
</template>
