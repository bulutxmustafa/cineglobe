<script setup lang="ts">
import type { Collection, TitleItem } from '~/composables/useApi'

const { t, locale } = useI18n()
const localePath = useLocalePath()
const base = useApiBase()
useSeoMeta({
  title: () => t('lucky.metaTitle'),
  description: () => t('lucky.metaDescription'),
})

const { data: cols } = await useApiFetch<{ collections: Collection[] }>('/collections/')
const slug = ref('')
const pick = ref<TitleItem | null>(null)
const spinning = ref(false)
const failed = ref(false)
const recent = ref<string[]>([])

watchEffect(() => {
  if (!slug.value && cols.value?.collections?.length) slug.value = cols.value.collections[0]!.slug
})

async function spin() {
  if (!slug.value || spinning.value) return
  spinning.value = true
  failed.value = false
  try {
    const [res] = await Promise.all([
      $fetch<{ pick: TitleItem | null }>(`${base}/collections/${slug.value}/random/`, {
        query: { lang: locale.value, exclude: recent.value.slice(-8).join(',') },
      }),
      new Promise((r) => setTimeout(r, 2600)), // short suspense; also respects reduced motion below
    ])
    pick.value = res.pick
    if (res.pick) recent.value.push(`${res.pick.media_type}:${res.pick.tmdb_id}`)
  } catch {
    failed.value = true
  } finally {
    spinning.value = false
  }
}
</script>

<template>
  <div>
    <section class="relative overflow-hidden" style="background: radial-gradient(ellipse at 50% 15%, #2e2418, var(--night) 72%)">
      <div class="container-page relative py-12 text-center text-white">
        <h1 class="text-3xl sm:text-4xl">{{ t('lucky.title') }}</h1>
        <p class="mx-auto mt-2 max-w-xl text-white/80">{{ t('lucky.lead') }}</p>

        <ClientOnly><LuckyGlobe :spinning="spinning" class="mt-4" /></ClientOnly>

        <div class="mx-auto mt-4 flex max-w-xl flex-wrap items-end justify-center gap-3 text-left">
          <div>
            <label for="lcol" class="mb-1 block text-sm font-medium text-white/80">{{ t('lucky.from') }}</label>
            <select id="lcol" v-model="slug" class="min-h-[48px] rounded-[10px] border-0 bg-white px-3 text-[var(--ink)]">
              <option v-for="c in cols?.collections" :key="c.slug" :value="c.slug">{{ c.name }}</option>
            </select>
          </div>
          <button class="btn btn-primary min-h-[48px] px-6 text-base" :disabled="spinning || !slug" @click="spin">
            {{ spinning ? t('lucky.spinning') : pick ? t('lucky.again') : t('lucky.go') }}
          </button>
        </div>
      </div>
    </section>

    <div class="container-page py-10" aria-live="polite">
      <p v-if="failed" class="text-sm" role="alert">{{ t('state.errorBody') }}</p>
      <div
        v-else-if="pick && !spinning"
        class="reveal mx-auto grid max-w-3xl gap-6 rounded-[16px] border p-5 sm:grid-cols-[220px_1fr]"
        style="border-color: var(--line); background: var(--surface); box-shadow: var(--shadow)"
      >
        <TitleCard :item="pick" />
        <div>
          <p class="text-sm font-semibold uppercase tracking-wide" style="color: var(--accent)">{{ t('lucky.tonight') }}</p>
          <h2 class="mt-1 text-2xl">{{ titleName(pick) }}</h2>
          <p v-if="pick.reason" class="mt-2" style="color: var(--ink-soft)">{{ pick.reason }}</p>
          <p v-if="pick.overview" class="mt-3 line-clamp-5 text-sm leading-relaxed">{{ pick.overview }}</p>
          <div class="mt-4 flex flex-wrap gap-2">
            <NuxtLink :to="localePath(`/title/${pick.media_type}/${pick.tmdb_id}`)" class="btn btn-quiet">{{ t('lucky.details') }}</NuxtLink>
            <FavoriteButton :item="pick" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.reveal {
  animation: pop 450ms var(--ease);
}
@keyframes pop {
  from {
    opacity: 0;
    transform: translateY(14px) scale(0.97);
  }
}
button:disabled {
  opacity: 0.6;
}
</style>
