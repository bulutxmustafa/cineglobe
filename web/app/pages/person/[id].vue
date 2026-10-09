<script setup lang="ts">
import type { TitleItem } from '~/composables/useApi'

interface Person {
  name: string
  biography: string
  biography_is_fallback: boolean
  birthday: string | null
  place_of_birth: string | null
  profile_url: string | null
  known_for: TitleItem[]
}

const route = useRoute()
const { t, locale } = useI18n()
const base = useApiBase()
const id = String(route.params.id)
const sort = ref<'newest' | 'oldest' | 'rating'>('newest')

const { data: person, error } = await useFetch<Person>(`${base}/people/${id}/`, {
  query: { lang: locale.value },
  key: `person:${id}:${locale.value}`,
})
if (error.value) {
  throw createError({ statusCode: error.value.statusCode === 404 ? 404 : 503, statusMessage: t('person.notFound'), fatal: true })
}
const { data: films, pending } = await useFetch<{ results: TitleItem[] }>(`${base}/people/${id}/filmography/`, {
  query: computed(() => ({ sort: sort.value, lang: locale.value })),
  key: `film:${id}`,
  watch: [sort],
})

const description = computed(() => (person.value?.biography || '').slice(0, 160))
useSeoMeta({
  title: () => `${person.value?.name} | CINEGLOB`,
  description: () => description.value,
  ogTitle: () => person.value?.name,
  ogDescription: () => description.value,
  ogImage: () => person.value?.profile_url || undefined,
})
useHead({
  script: [
    {
      type: 'application/ld+json',
      innerHTML: computed(() =>
        JSON.stringify({
          '@context': 'https://schema.org',
          '@type': 'Person',
          name: person.value?.name,
          image: person.value?.profile_url || undefined,
          birthDate: person.value?.birthday || undefined,
        }),
      ),
    },
  ],
})
</script>

<template>
  <div v-if="person" class="container-page py-10">
    <div class="grid gap-8 md:grid-cols-[200px_1fr]">
      <div class="mx-auto w-40 md:w-full">
        <div class="aspect-[2/3] overflow-hidden rounded-[6px]" style="background: var(--line)">
          <img v-if="person.profile_url" :src="person.profile_url" :alt="person.name" class="h-full w-full object-cover" width="342" height="513" />
        </div>
      </div>
      <div>
        <h1 class="text-3xl sm:text-4xl">{{ person.name }}</h1>
        <p v-if="person.birthday" class="mt-1 text-sm" style="color: var(--ink-soft)">
          {{ t('person.born') }}: {{ person.birthday }}<span v-if="person.place_of_birth"> · {{ person.place_of_birth }}</span>
        </p>
        <h2 class="mt-5 text-xl">{{ t('person.bio') }}</h2>
        <p v-if="person.biography_is_fallback && person.biography" class="mt-1 text-xs" style="color: var(--ink-faint)">{{ t('person.bioFallback') }}</p>
        <p class="mt-2 max-w-2xl whitespace-pre-line leading-relaxed">{{ person.biography || t('person.noBio') }}</p>
      </div>
    </div>

    <section v-if="person.known_for?.length" class="mt-10">
      <h2 class="section-title">{{ t('person.knownFor') }}</h2>
      <TitleGrid :items="person.known_for" />
    </section>

    <section class="mt-10">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <h2 class="section-title !mb-0">{{ t('person.filmography') }}</h2>
        <div class="flex gap-2" role="group">
          <button
            v-for="opt in (['newest', 'oldest', 'rating'] as const)"
            :key="opt"
            type="button"
            class="chip"
            :class="{ 'chip-on': sort === opt }"
            :aria-pressed="sort === opt"
            @click="sort = opt"
          >{{ t(`person.sort.${opt}`) }}</button>
        </div>
      </div>
      <div class="mt-5">
        <ApiState :pending="pending" :empty="!films?.results?.length">
          <TitleGrid :items="films?.results ?? []" />
        </ApiState>
      </div>
    </section>
  </div>
</template>

<style scoped>
.chip-on {
  border-color: var(--ink);
  color: var(--ink);
  font-weight: 600;
}
</style>
