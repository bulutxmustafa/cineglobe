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
      new Promise((r) => setTimeout(r, 900)), // short suspense; also respects reduced motion below
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
  <div class="container-page py-10">
    <h1 class="text-3xl">{{ t('lucky.title') }}</h1>
    <p class="mt-2 max-w-2xl" style="color: var(--ink-soft)">{{ t('lucky.lead') }}</p>

    <div class="mt-6 flex flex-wrap items-end gap-3">
      <div>
        <label for="lcol" class="mb-1 block text-sm font-medium">{{ t('lucky.from') }}</label>
        <select id="lcol" v-model="slug" class="min-h-[44px] rounded-[6px] border bg-white px-3" style="border-color: var(--line-strong)">
          <option v-for="c in cols?.collections" :key="c.slug" :value="c.slug">{{ c.name }}</option>
        </select>
      </div>
      <button class="btn btn-primary min-h-[44px]" :disabled="spinning || !slug" @click="spin">
        {{ spinning ? t('lucky.spinning') : pick ? t('lucky.again') : t('lucky.go') }}
      </button>
    </div>

    <div class="mt-8" aria-live="polite">
      <div v-if="spinning" class="spin mx-auto h-16 w-16 rounded-full border-4" aria-hidden="true" />
      <p v-else-if="failed" class="text-sm" role="alert">{{ t('state.errorBody') }}</p>
      <div v-else-if="pick" class="grid max-w-3xl gap-6 sm:grid-cols-[220px_1fr]">
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
.spin {
  border-color: var(--line);
  border-top-color: var(--accent);
  animation: spin 700ms linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
button:disabled {
  opacity: 0.6;
}
</style>
