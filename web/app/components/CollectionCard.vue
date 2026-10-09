<script setup lang="ts">
import type { Collection, TitleItem } from '~/composables/useApi'

const props = defineProps<{ collection: Collection; index: number }>()
const localePath = useLocalePath()
const { locale } = useI18n()
const base = useApiBase()

// Three posters from the collection itself (small payload, CDN-cached upstream).
const { data: posters } = useFetch<string[]>(() => `${base}/collections/${props.collection.slug}/`, {
  query: { lang: locale.value },
  key: `colposters:${props.collection.slug}:${locale.value}`,
  transform: (r: unknown) =>
    ((r as { results?: TitleItem[] }).results ?? [])
      .map((i) => i.poster_url || '')
      .filter(Boolean)
      .slice(0, 3),
  default: () => [],
})
const tone = computed(() => `var(--card-${((props.index - 1) % 6) + 1})`)
</script>

<template>
  <NuxtLink
    :to="localePath(`/collections/${collection.slug}`)"
    class="card group relative flex h-full min-h-[200px] overflow-hidden rounded-[18px] p-5"
    :style="{ '--tone': tone }"
  >
    <div class="relative z-10 flex max-w-[56%] flex-col justify-between">
      <span class="num">{{ String(index).padStart(2, '0') }}</span>
      <div>
        <span class="block font-serif text-[1.3rem] font-bold leading-tight text-[var(--text)]">{{ collection.name }}</span>
        <span class="mt-1.5 block text-[13px] leading-snug text-[var(--text-2)]">{{ collection.description }}</span>
        <span class="more mt-3 inline-flex items-center gap-1 text-[13px] font-semibold">{{ $t('collections.explore') }} <span aria-hidden="true" class="arrow">→</span></span>
      </div>
    </div>
    <div class="fan" aria-hidden="true">
      <img v-for="(src, i) in posters" :key="i" :src="src" alt="" loading="lazy" width="120" height="180" :class="`p${i}`" />
    </div>
  </NuxtLink>
</template>

<style scoped>
.card {
  background: linear-gradient(180deg, rgb(255 255 255 / 6%), transparent 55%), var(--tone);
  border: 1px solid rgb(255 255 255 / 10%);
  box-shadow: var(--shadow);
  transition: transform 280ms var(--spring), border-color 200ms var(--ease), box-shadow 200ms var(--ease);
}
.card:hover {
  transform: translateY(-5px);
  border-color: rgb(242 185 80 / 75%);
  box-shadow: 0 2px 4px rgb(0 0 0 / 25%), 0 18px 34px rgb(0 0 0 / 38%);
}
.num {
  font-family: var(--font-serif);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--gold);
}
.more {
  color: var(--gold);
}
.arrow {
  transition: transform 220ms var(--spring);
}
.card:hover .arrow {
  transform: translateX(4px);
}
.fan {
  position: absolute;
  right: 10px;
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
  border: 1px solid rgb(255 255 255 / 14%);
  box-shadow: 0 10px 24px rgb(0 0 0 / 50%);
  transition: transform 320ms var(--spring);
}
.p0 { right: 36%; top: 16%; transform: rotate(-9deg); z-index: 1; }
.p1 { right: 12%; top: 8%; transform: rotate(0deg); z-index: 2; }
.p2 { right: -8%; top: 20%; transform: rotate(10deg); z-index: 1; }
.group:hover .p0 { transform: rotate(-13deg) translateX(-5px) scale(1.04); }
.group:hover .p1 { transform: translateY(-7px) scale(1.06); }
.group:hover .p2 { transform: rotate(14deg) translateX(5px) scale(1.04); }
@media (hover: none) {
  .card:hover { transform: none; }
}
</style>
