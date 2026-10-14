<script setup lang="ts">
import type { Collection, TitleItem } from '~/composables/useApi'

const props = defineProps<{ collection: Collection; index: number }>()
const localePath = useLocalePath()
const { locale } = useI18n()
const base = useApiBase()

// Three posters from the collection itself (small payload, CDN-cached upstream).
const { data: posters } = await useFetch<string[]>(() => `${base}/collections/${props.collection.slug}/`, {
  query: { lang: locale.value },
  key: `colposters:${props.collection.slug}:${locale.value}`,
  transform: (r: unknown) =>
    ((r as { results?: TitleItem[] }).results ?? [])
      .map((i) => i.poster_url || '')
      .filter(Boolean)
      .slice(0, 3),
  default: () => [],
})
// Vivid tones: royal blue, emerald, violet, cyan, magenta, sunset orange.
const pairs = [
  ['#1d4ed8', '#3b82f6'],
  ['#047857', '#10b981'],
  ['#6d28d9', '#a855f7'],
  ['#0e7490', '#06b6d4'],
  ['#be185d', '#ec4899'],
  ['#c2410c', '#f59e0b'],
]
const bg = computed(() => {
  const [a, b] = pairs[(props.index - 1) % pairs.length]!
  return `radial-gradient(120% 90% at 85% 15%, rgb(255 255 255 / 18%), transparent 55%), linear-gradient(135deg, ${a}, ${b})`
})
</script>

<template>
  <NuxtLink
    :to="localePath(`/collections/${collection.slug}`)"
    class="card group relative flex h-full min-h-[210px] overflow-hidden rounded-[22px] p-5"
    :style="{ background: bg }"
  >
    <div class="relative z-10 flex max-w-[56%] flex-col justify-between">
      <span class="num">{{ String(index).padStart(2, '0') }}</span>
      <div>
        <span class="block font-serif text-[1.2rem] font-bold leading-tight text-white">{{ collection.name }}</span>
        <span class="mt-1.5 block text-[13px] leading-snug text-white/80">{{ collection.description }}</span>
        <span class="more mt-2.5 inline-flex items-center gap-1 text-[12px] font-semibold">{{ $t('collections.explore') }} <span aria-hidden="true" class="arrow">→</span></span>
      </div>
    </div>
    <div class="fan" aria-hidden="true">
      <img v-for="(src, i) in posters" :key="i" :src="src" alt="" width="120" height="180" :class="`p${i}`" />
    </div>
  </NuxtLink>
</template>

<style scoped>
.card {
  border: 1px solid rgb(255 255 255 / 10%);
  box-shadow: 0 2px 4px rgb(13 40 90 / 12%), 0 16px 32px rgb(13 40 90 / 20%);
  transition: transform 280ms var(--spring), border-color 200ms var(--ease), box-shadow 200ms var(--ease);
}
.card:hover {
  transform: translateY(-5px);
  border-color: rgb(242 192 102 / 70%);
  box-shadow: 0 2px 4px rgb(0 0 0 / 25%), 0 18px 34px rgb(0 0 0 / 36%);
}
.num {
  font-family: var(--font-serif);
  font-size: 1.4rem;
  font-weight: 700;
  color: #ffe3a3;
}
.more {
  color: #ffe3a3;
}
.arrow {
  transition: transform 220ms var(--spring);
}
.card:hover .arrow {
  transform: translateX(4px);
}
.fan {
  position: absolute;
  right: 8px;
  top: 50%;
  width: 48%;
  height: 100%;
  transform: translateY(-50%);
}
.fan img {
  position: absolute;
  width: 58%;
  aspect-ratio: 2 / 3;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid rgb(255 255 255 / 16%);
  box-shadow: 0 10px 24px rgb(0 0 0 / 45%);
  transition: transform 320ms var(--spring);
}
.p0 { right: 36%; top: 18%; transform: rotate(-9deg); z-index: 1; }
.p1 { right: 12%; top: 10%; transform: rotate(0deg); z-index: 2; }
.p2 { right: -8%; top: 22%; transform: rotate(10deg); z-index: 1; }
.group:hover .p0 { transform: rotate(-13deg) translateX(-5px) scale(1.04); }
.group:hover .p1 { transform: translateY(-7px) scale(1.06); }
.group:hover .p2 { transform: rotate(14deg) translateX(5px) scale(1.04); }
@media (hover: none) {
  .card:hover { transform: none; }
}
</style>
