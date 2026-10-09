<script setup lang="ts">
import type { Collection, TitleItem } from '~/composables/useApi'

// "Lucky Pick": choose a collection, spin the poster wheel, get a random title.
// `compact` = the small card used next to the hero search; otherwise a full-width section.
defineProps<{ compact?: boolean }>()
const { t, locale } = useI18n()
const localePath = useLocalePath()
const base = useApiBase()

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
  <!-- Compact card (home hero, right side) -->
  <section v-if="compact" id="sans" class="cp scroll-mt-24" :aria-label="t('lucky.title')">
    <ConfettiBurst :fire="confetti" />
    <div class="relative">
      <p class="inline-block rounded-full border px-3 py-1 text-xs font-bold uppercase tracking-[0.14em]" style="border-color: rgb(255 255 255 / 30%); color: #dbe8f8">🎲 {{ t('lucky.title') }}</p>

      <div class="wheel-wrap wheel-compact">
        <ClientOnly>
          <PosterWheel :posters="wheel ?? []" :spinning="spinning" :pick-poster="pick?.poster_url ?? null" @landed="landed" />
        </ClientOnly>
      </div>

      <label for="lcol" class="sr-only">{{ t('lucky.from') }}</label>
      <select id="lcol" v-model="slug" class="sel min-h-[46px] w-full rounded-[12px] border px-3 text-sm" :disabled="spinning">
        <option v-for="c in cols?.collections" :key="c.slug" :value="c.slug">{{ c.icon }} {{ c.name }}</option>
      </select>
      <button class="btn btn-primary mt-3 min-h-[46px] w-full text-sm" :disabled="spinning || !slug" @click="spin">
        <LogoMark :size="24" variant="default" class="spin-logo" :class="{ going: spinning }" />
        {{ spinning ? t('lucky.spinning') : pick ? t('lucky.again') : t('lucky.go') }}
      </button>
      <p v-if="failed" class="mt-3 text-sm" style="color: #ffb4a8" role="alert">{{ t('state.errorBody') }}</p>

      <div v-if="pick && shown" class="mini reveal" aria-live="polite">
        <img v-if="pick.poster_url" :src="pick.poster_url" :alt="titleName(pick)" width="64" height="96" />
        <div class="min-w-0">
          <p class="text-[11px] font-bold uppercase tracking-wide" style="color: var(--gold)">{{ t('lucky.cheer') }}</p>
          <p class="line-clamp-2 font-semibold leading-snug" style="color: var(--text)">{{ titleName(pick) }}</p>
          <NuxtLink :to="localePath(`/title/${pick.media_type}/${pick.tmdb_id}`)" class="mt-1 inline-block text-sm font-semibold underline underline-offset-4" style="color: var(--gold)">{{ t('lucky.details') }} →</NuxtLink>
        </div>
      </div>
    </div>
  </section>

  <!-- Full section (used on /lucky) -->
  <section v-else id="sans" class="container-page scroll-mt-20 py-12" :aria-label="t('lucky.title')">
    <div class="panel relative overflow-hidden rounded-[28px]">
      <ConfettiBurst :fire="confetti" />
      <div class="relative grid items-center gap-6 p-6 sm:p-10 lg:grid-cols-[1fr_1.15fr]">
        <div>
          <p class="inline-block rounded-full border px-3 py-1 text-xs font-bold uppercase tracking-[0.14em]" style="border-color: rgb(255 255 255 / 30%); color: #dbe8f8">🎲 {{ t('lucky.title') }}</p>
          <h2 class="mt-4 text-lg sm:text-[1.4rem]" style="color: var(--text)">{{ t('lucky.headline') }}</h2>
          <p class="mt-3 max-w-md text-sm" style="color: var(--text-2)">{{ t('lucky.lead') }}</p>

          <div class="mt-6 flex flex-wrap items-end gap-3">
            <div class="min-w-0 flex-1 sm:flex-none">
              <label for="lcol" class="mb-1 block text-sm font-medium" style="color: var(--text-2)">{{ t('lucky.from') }}</label>
              <select id="lcol" v-model="slug" class="sel min-h-[52px] w-full rounded-[12px] border px-3" :disabled="spinning">
                <option v-for="c in cols?.collections" :key="c.slug" :value="c.slug">{{ c.icon }} {{ c.name }}</option>
              </select>
            </div>
            <button class="btn btn-primary min-h-[48px] px-6 text-sm" :disabled="spinning || !slug" @click="spin">
              <LogoMark :size="26" variant="default" class="spin-logo" :class="{ going: spinning }" />
              {{ spinning ? t('lucky.spinning') : pick ? t('lucky.again') : t('lucky.go') }}
            </button>
          </div>
          <p v-if="failed" class="mt-4 text-sm" style="color: #ffb4a8" role="alert">{{ t('state.errorBody') }}</p>
        </div>

        <div class="wheel-wrap">
          <ClientOnly>
            <PosterWheel :posters="wheel ?? []" :spinning="spinning" :pick-poster="pick?.poster_url ?? null" @landed="landed" />
          </ClientOnly>
        </div>
      </div>
    </div>

    <div aria-live="polite">
      <div
        v-if="pick && shown"
        class="reveal mx-auto mt-6 grid max-w-3xl gap-6 rounded-[20px] border p-5 sm:grid-cols-[200px_1fr]"
        style="border-color: var(--line-strong); background: #fffdf8; box-shadow: 0 18px 44px rgb(20 32 44 / 16%)"
      >
        <TitleCard :item="pick" />
        <div>
          <p class="text-sm font-bold uppercase tracking-wide" style="color: var(--accent)">{{ t('lucky.cheer') }}</p>
          <h3 class="mt-1 text-2xl">{{ titleName(pick) }}</h3>
          <p v-if="pick.reason" class="mt-2" style="color: var(--ink-soft)">{{ pick.reason }}</p>
          <p v-if="pick.overview" class="mt-3 line-clamp-5 text-sm leading-relaxed">{{ pick.overview }}</p>
          <div class="mt-4 flex flex-wrap gap-2">
            <NuxtLink :to="localePath(`/title/${pick.media_type}/${pick.tmdb_id}`)" class="btn btn-primary">{{ t('lucky.details') }}</NuxtLink>
            <FavoriteButton :item="pick" />
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.panel {
  background: var(--box);
  border: 1px solid rgb(255 255 255 / 16%);
  box-shadow: 0 2px 4px rgb(0 0 0 / 20%), 0 14px 30px rgb(0 0 0 / 30%);
}
.sel {
  background: rgb(0 0 0 / 28%);
  border-color: var(--border);
  color: var(--text);
}
.cp {
  position: relative;
  overflow: hidden;
  padding: 18px;
  border-radius: 22px;
  background: var(--box);
  border: 1px solid rgb(255 255 255 / 16%);
  box-shadow: 0 2px 4px rgb(0 0 0 / 20%), 0 14px 30px rgb(0 0 0 / 30%);
}
.wheel-compact {
  margin: 8px -8px 6px;
}
.wheel-compact :deep(.stage) {
  --w: 84px;
}
.mini {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-top: 14px;
  padding: 10px;
  border-radius: 14px;
  background: rgb(255 255 255 / 6%);
  border: 1px solid var(--border);
}
.mini img {
  width: 48px;
  border-radius: 6px;
  flex: none;
}
.spin-logo.going {
  animation: turn 0.9s linear infinite;
}
@keyframes turn {
  to {
    transform: rotate(360deg);
  }
}
.wheel-wrap :deep(.stage) {
  --w: 128px;
}
@media (min-width: 640px) {
  .wheel-wrap:not(.wheel-compact) :deep(.stage) {
    --w: 140px;
  }
}
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
