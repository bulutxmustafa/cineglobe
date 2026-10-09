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
const shown = ref(false)
const confetti = ref(0)
const recent = ref<string[]>([])

watchEffect(() => {
  if (!slug.value && cols.value?.collections?.length) slug.value = cols.value.collections[0]!.slug
})

// Posters of the chosen collection fill the wheel.
const { data: wheel } = await useFetch<string[]>(() => `${base}/collections/${slug.value || 'never-boring'}/`, {
  query: computed(() => ({ lang: locale.value })),
  key: 'wheel',
  watch: [slug],
  transform: (r: unknown) =>
    ((r as { results?: TitleItem[] }).results ?? [])
      .map((i) => i.poster_url || '')
      .filter(Boolean)
      .slice(0, 12),
  default: () => [],
})

async function spin() {
  if (!slug.value || spinning.value) return
  spinning.value = true
  shown.value = false
  failed.value = false
  pick.value = null
  try {
    const [res] = await Promise.all([
      $fetch<{ pick: TitleItem | null }>(`${base}/collections/${slug.value}/random/`, {
        query: { lang: locale.value, exclude: recent.value.slice(-8).join(',') },
      }),
      new Promise((r) => setTimeout(r, 2200)), // let the wheel whirl for a moment
    ])
    pick.value = res.pick
    if (res.pick) recent.value.push(`${res.pick.media_type}:${res.pick.tmdb_id}`)
  } catch {
    failed.value = true
  } finally {
    spinning.value = false
    // Safety net: show the result even if the wheel animation cannot run (hidden tab).
    setTimeout(() => {
      if (pick.value && !shown.value) landed()
    }, 3600)
  }
}

function landed() {
  if (!pick.value) return
  shown.value = true
  confetti.value++
}
</script>

<template>
  <div>
    <section class="relative overflow-hidden" style="background: var(--night)">
      <ConfettiBurst :fire="confetti" />
      <div class="container-page relative py-10 text-center text-white">
        <h1 class="text-2xl sm:text-3xl">🎡 {{ t('lucky.title') }}</h1>
        <p class="mx-auto mt-2 max-w-xl text-sm text-white/80 sm:text-base">{{ t('lucky.lead') }}</p>

        <div class="mt-8">
          <ClientOnly>
            <PosterWheel :posters="wheel ?? []" :spinning="spinning" :pick-poster="pick?.poster_url ?? null" @landed="landed" />
          </ClientOnly>
        </div>

        <div class="mx-auto mt-6 flex max-w-xl flex-wrap items-end justify-center gap-3 text-left">
          <div>
            <label for="lcol" class="mb-1 block text-sm font-medium text-white/80">{{ t('lucky.from') }}</label>
            <select id="lcol" v-model="slug" class="min-h-[52px] rounded-[14px] border border-white/20 bg-[#161f33] px-3 text-white" :disabled="spinning">
              <option v-for="c in cols?.collections" :key="c.slug" :value="c.slug">{{ c.icon }} {{ c.name }}</option>
            </select>
          </div>
          <button class="btn btn-primary min-h-[52px] rounded-[14px] px-7 text-base" :disabled="spinning || !slug" @click="spin">
            {{ spinning ? t('lucky.spinning') : pick ? t('lucky.again') : t('lucky.go') }}
          </button>
        </div>
      </div>
    </section>

    <div class="container-page py-10" aria-live="polite">
      <p v-if="failed" class="text-center text-sm" role="alert">{{ t('state.errorBody') }}</p>
      <div
        v-else-if="pick && shown"
        class="reveal mx-auto grid max-w-3xl gap-6 rounded-[20px] border p-5 sm:grid-cols-[220px_1fr]"
        style="border-color: var(--line-strong); background: #161f33; box-shadow: 0 18px 44px rgb(60 40 10 / 14%)"
      >
        <TitleCard :item="pick" />
        <div>
          <p class="text-sm font-semibold uppercase tracking-wide" style="color: var(--accent)">{{ t('lucky.cheer') }}</p>
          <h2 class="mt-1 text-2xl">{{ titleName(pick) }}</h2>
          <p v-if="pick.reason" class="mt-2" style="color: var(--ink-soft)">{{ pick.reason }}</p>
          <p v-if="pick.overview" class="mt-3 line-clamp-5 text-sm leading-relaxed">{{ pick.overview }}</p>
          <div class="mt-4 flex flex-wrap gap-2">
            <NuxtLink :to="localePath(`/title/${pick.media_type}/${pick.tmdb_id}`)" class="btn btn-primary">{{ t('lucky.details') }}</NuxtLink>
            <FavoriteButton :item="pick" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.reveal {
  animation: pop 520ms cubic-bezier(0.2, 1.3, 0.4, 1);
}
@keyframes pop {
  from {
    opacity: 0;
    transform: translateY(18px) scale(0.94);
  }
}
button:disabled {
  opacity: 0.6;
}
</style>
