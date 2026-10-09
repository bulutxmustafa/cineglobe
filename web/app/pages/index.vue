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
    <!-- Hero: search on the left, the lucky wheel on the right; posters roll behind the whole site -->
    <section class="relative flex min-h-[calc(100svh-64px)] items-center overflow-hidden" style="background: linear-gradient(135deg, #0b1f3a 0%, #12305c 100%)">
      <ClientOnly><PosterWall :posters="posters" /></ClientOnly>
      <div
        class="absolute inset-0"
        style="background: radial-gradient(ellipse at 24% 42%, rgb(6 16 34 / 66%) 0%, transparent 66%), linear-gradient(135deg, rgb(11 31 58 / 52%) 0%, rgb(16 41 77 / 40%) 100%), linear-gradient(180deg, transparent 72%, rgb(11 31 58 / 50%) 100%)"
      />
      <div class="container-page relative w-full pb-24 pt-12 sm:pb-32 sm:pt-16">
      <div class="grid items-center gap-8 lg:grid-cols-[1.3fr_0.7fr]">
        <div class="text-center lg:text-left">
          <p class="inline-block rounded-full border px-4 py-1.5 text-[13px] font-bold uppercase tracking-[0.15em] sm:text-sm" style="border-color: rgb(255 255 255 / 30%); color: #dbe8f8; background: rgb(11 31 58 / 60%)">
            {{ t('hero.eyebrow') }}
          </p>
          <h1 class="mt-5 max-w-2xl text-[1.2rem] font-semibold leading-[1.25] sm:text-[1.55rem] lg:mx-0" style="color: #eaf4ff; text-shadow: 0 2px 14px rgb(0 0 0 / 50%)">
            {{ t('hero.title') }}
          </h1>
          <div class="mt-7 max-w-2xl text-left">
            <SearchBox examples dark />
          </div>
        </div>
        <LuckyPicker compact />
      </div>
      </div>
    </section>

    <section class="container-page" aria-labelledby="cols-h">
      <div class="panel-light">
        <div class="flex items-end justify-between gap-4">
          <div>
            <h2 id="cols-h" class="text-lg sm:text-[1.3rem]">{{ t('home.collections') }}</h2>
            <p class="mt-1 text-sm" style="color: var(--ink-soft)">{{ t('home.collectionsLead') }}</p>
          </div>
          <NuxtLink :to="localePath('/collections')" class="text-sm font-semibold underline underline-offset-4" style="color: var(--accent)">{{ t('home.allCollections') }}</NuxtLink>
        </div>
        <div class="mt-6">
          <ApiState :pending="colsPending && !cols?.collections?.length" :error="colsError" :empty="!cols?.collections?.length">
            <ul class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <li v-for="(c, i) in cols?.collections" :key="c.slug" class="rise" :style="{ animationDelay: `${i * 60}ms` }">
                <CollectionCard :collection="c" :index="i + 1" />
              </li>
            </ul>
          </ApiState>
        </div>
      </div>
    </section>

    <section class="container-page mt-6" aria-labelledby="up-h">
      <div class="panel-light">
        <div class="flex items-end justify-between gap-4">
          <div>
            <h2 id="up-h" class="text-lg sm:text-[1.3rem]">{{ t('home.upcoming') }}</h2>
            <p class="mt-1 text-sm" style="color: var(--ink-soft)">{{ t('home.upcomingLead') }}</p>
          </div>
          <NuxtLink :to="localePath('/upcoming')" class="text-sm font-semibold underline underline-offset-4" style="color: var(--accent)">{{ t('home.allUpcoming') }}</NuxtLink>
        </div>
        <div class="mt-6">
          <ApiState :pending="upPending && !upcoming.length" :error="upError" :empty="!upcoming.length">
            <TitleGrid :items="upcoming" />
          </ApiState>
        </div>
      </div>
    </section>

    <section class="container-page mb-12 mt-6" aria-labelledby="how-h">
      <div class="panel-light">
        <h2 id="how-h" class="text-lg sm:text-[1.3rem]">{{ t('home.howTitle') }}</h2>
        <ol class="mt-6 grid gap-4 sm:grid-cols-3">
          <li
            v-for="(step, i) in ($tm('home.how') as { t: string; d: string }[])"
            :key="i"
            class="rounded-[18px] border p-6"
            style="border-color: var(--line); background: var(--surface); box-shadow: var(--shadow)"
          >
            <span class="inline-flex h-10 w-10 items-center justify-center rounded-full font-serif text-xl font-bold" :style="{ background: i === 1 ? 'var(--teal)' : 'var(--gold)', color: i === 1 ? '#fff' : '#1a1305' }">{{ i + 1 }}</span>
            <h3 class="mt-3 font-sans text-lg font-semibold">{{ $rt(step.t as any) }}</h3>
            <p class="mt-1 text-sm" style="color: var(--ink-soft)">{{ $rt(step.d as any) }}</p>
          </li>
        </ol>
      </div>
    </section>
  </div>
</template>
