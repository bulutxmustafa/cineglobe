<script setup lang="ts">
import type { TitleItem } from '~/composables/useApi'

interface SearchResponse {
  results: TitleItem[]
  ai_status: 'ok' | 'quota_exceeded' | 'budget_exceeded' | 'fallback'
}

const route = useRoute()
const { t, locale } = useI18n()
const base = useApiBase()

useHead({ meta: [{ name: 'robots', content: 'noindex, follow' }] })
useSeoMeta({ title: () => `${t('search.title')} | FilmPusula` })

const query = computed(() => String(route.query.q ?? '').trim())
const mediaType = computed(() => String(route.query.type ?? 'both'))
const data = ref<SearchResponse | null>(null)
const pending = ref(false)
const failed = ref(false)
let controller: AbortController | null = null

async function run() {
  controller?.abort()
  data.value = null
  failed.value = false
  if (query.value.length < 2) return
  controller = new AbortController()
  pending.value = true
  try {
    data.value = await $fetch<SearchResponse>(`${base}/search/`, {
      method: 'POST',
      body: { query: query.value, media_type: mediaType.value, lang: locale.value },
      signal: controller.signal,
    })
  } catch (e) {
    if ((e as Error).name !== 'AbortError') failed.value = true
  } finally {
    pending.value = false
  }
}
watch(() => [route.query.q, route.query.type, locale.value], run)
onMounted(run)

const notice = computed(() => {
  const s = data.value?.ai_status
  if (s === 'quota_exceeded' || s === 'budget_exceeded') return t('search.aiQuota')
  if (s === 'fallback') return t('search.aiFallback')
  return ''
})
</script>

<template>
  <div class="container-page py-10">
    <h1 class="text-3xl">{{ t('search.title') }}</h1>
    <div class="mt-5 max-w-3xl">
      <SearchBox :key="query" :initial="query" :media-type="mediaType" />
    </div>

    <div class="mt-8" aria-live="polite">
      <p v-if="pending" class="mb-4 text-sm font-medium" style="color: var(--ink-soft)">{{ t('search.searching') }}</p>
      <p v-else-if="query && data" class="mb-4 text-lg font-serif">{{ t('search.resultsFor', { query }) }}</p>
      <p
        v-if="notice"
        class="mb-4 rounded-[6px] border px-4 py-3 text-sm"
        style="border-color: var(--line-strong); background: var(--accent-soft)"
      >{{ notice }}</p>
      <ApiState :pending="pending" :error="failed" :empty="!!data && !data.results.length">
        <TitleGrid v-if="data" :items="data.results" show-reason />
      </ApiState>
    </div>
  </div>
</template>
