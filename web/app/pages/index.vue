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
const upcoming = computed(() => (up.value?.results ?? []).filter((i) => i.poster_url).slice(0, 5))
</script>

<template>
  <div>
    <section class="border-b" style="border-color: var(--line); background: var(--surface)">
      <div class="container-page py-12 sm:py-16">
        <p class="text-sm font-semibold uppercase tracking-[0.12em]" style="color: var(--accent)">{{ t('hero.eyebrow') }}</p>
        <h1 class="mt-3 max-w-3xl text-[2rem] leading-[1.15] sm:text-[2.75rem]">
          {{ t('hero.title') }}
        </h1>
        <p class="mt-4 max-w-2xl text-base sm:text-lg" style="color: var(--ink-soft)">{{ t('hero.lead') }}</p>
        <div class="mt-8 max-w-3xl">
          <SearchBox examples />
        </div>
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
          class="rounded-[10px] border p-5"
          style="border-color: var(--line); background: var(--surface)"
        >
          <span class="font-serif text-3xl font-semibold" style="color: var(--accent)">{{ i + 1 }}</span>
          <h3 class="mt-2 font-sans text-base font-semibold">{{ $rt(step.t as any) }}</h3>
          <p class="mt-1 text-sm" style="color: var(--ink-soft)">{{ $rt(step.d as any) }}</p>
        </li>
      </ol>
    </section>
  </div>
</template>
