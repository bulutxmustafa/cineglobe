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
  <!-- Compact card (home, next to the search box) -->
  <section v-if="compact" id="sans" class="cp scroll-mt-24" :aria-label="t('lucky.title')">
    <ConfettiBurst :fire="confetti" />
    <div class="bulbs" aria-hidden="true"><span v-for="n in 14" :key="n" :class="{ on: spinning }" :style="{ animationDelay: `${(n % 2) * 0.45}s` }" /></div>
    <div class="relative">
      <div class="flex items-center justify-between gap-2">
        <p class="eyebrow !py-1">🎲 {{ t('lucky.title') }}</p>
      </div>

      <div class="wheel-wrap wheel-compact">
        <div class="rays" :class="{ fast: spinning }" aria-hidden="true" />
        <div class="pointer" aria-hidden="true" />
        <ClientOnly>
          <PosterWheel :posters="wheel ?? []" :spinning="spinning" :pick-poster="pick?.poster_url ?? null" @landed="landed" />
        </ClientOnly>
      </div>

      <label for="lcol" class="sr-only">{{ t('lucky.from') }}</label>
      <select id="lcol" v-model="slug" class="sel min-h-[46px] w-full rounded-[12px] border px-3 text-sm" :disabled="spinning">
        <option v-for="c in cols?.collections" :key="c.slug" :value="c.slug">{{ c.icon }} {{ c.name }}</option>
      </select>
      <button class="btn btn-primary spin-btn mt-3 min-h-[50px] w-full text-[15px]" :disabled="spinning || !slug" @click="spin">
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
          <p class="eyebrow">🎲 {{ t('lucky.title') }}</p>
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
        style="border-color: rgb(242 192 102 / 35%); background: var(--box); box-shadow: 0 18px 44px rgb(0 0 0 / 40%)"
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
  background: rgb(0 0 0 / 30%);
  border-color: rgb(242 192 102 / 25%);
  color: var(--text);
}
.cp {
  position: relative;
  overflow: hidden;
  padding: 24px 18px 18px;
  border-radius: 22px;
  background: linear-gradient(160deg, rgb(43 31 13 / 92%) 0%, rgb(24 17 8 / 94%) 100%);
  border: 1px solid rgb(242 192 102 / 32%);
  box-shadow: 0 30px 60px rgb(0 0 0 / 45%);
}
.bulbs {
  position: absolute;
  top: 9px;
  left: 18px;
  right: 18px;
  display: flex;
  justify-content: space-between;
  pointer-events: none;
}
.bulbs span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #f2c066;
  box-shadow: 0 0 8px 2px rgb(242 192 102 / 60%);
  animation: twinkle 0.9s ease-in-out infinite alternate;
}
.bulbs span.on {
  animation-duration: 0.22s;
}
@keyframes twinkle {
  from {
    opacity: 0.25;
    box-shadow: none;
  }
}
.rays {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 260px;
  height: 260px;
  margin: -150px 0 0 -130px;
  border-radius: 50%;
  background: repeating-conic-gradient(rgb(242 192 102 / 13%) 0deg 10deg, transparent 10deg 30deg);
  mask-image: radial-gradient(circle, #000 30%, transparent 70%);
  -webkit-mask-image: radial-gradient(circle, #000 30%, transparent 70%);
  animation: rays 24s linear infinite;
  pointer-events: none;
}
.rays.fast {
  animation-duration: 2.5s;
}
@keyframes rays {
  to {
    transform: rotate(360deg);
  }
}
.pointer {
  position: absolute;
  left: 50%;
  top: 4px;
  z-index: 5;
  width: 0;
  height: 0;
  margin-left: -9px;
  border-left: 9px solid transparent;
  border-right: 9px solid transparent;
  border-top: 14px solid var(--gold);
  filter: drop-shadow(0 2px 3px rgb(0 0 0 / 50%));
}
.spin-btn {
  border-radius: 14px;
}
.wheel-compact {
  position: relative;
  margin: 10px -8px 8px;
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
  background: rgb(0 0 0 / 25%);
  border: 1px solid rgb(242 192 102 / 25%);
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
