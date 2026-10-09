<script setup lang="ts">
import type { Collection, TitleItem } from '~/composables/useApi'

const props = defineProps<{ collection: Collection; index: number }>()
const localePath = useLocalePath()
const { locale } = useI18n()
const neon = ['#8b5cf6', '#ec4899', '#f59e0b', '#22d3ee', '#34d399', '#fb923c']
const accent = computed(() => neon[(props.index - 1) % neon.length]!)
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
</script>

<template>
  <NuxtLink
    :to="localePath(`/collections/${collection.slug}`)"
    class="card group relative flex h-full min-h-[190px] overflow-hidden rounded-[18px] p-5"
    :style="{ '--neon': accent }"
  >
    <div class="relative z-10 flex max-w-[58%] flex-col justify-between">
      <span class="num">{{ String(index).padStart(2, '0') }}</span>
      <div>
        <span class="block font-serif text-xl font-semibold leading-snug text-white">{{ collection.name }}</span>
        <span class="mt-1 block text-[13px] leading-snug text-[#a9b4c8]">{{ collection.description }}</span>
      </div>
    </div>
    <div class="fan" aria-hidden="true">
      <img v-for="(src, i) in posters" :key="i" :src="src" alt="" loading="lazy" width="120" height="180" :class="`p${i}`" />
    </div>
  </NuxtLink>
</template>

<style scoped>
.card {
  background: #161f33;
  border: 1px solid #243049;
  box-shadow: 0 10px 28px rgb(0 0 0 / 40%);
  transition: transform 320ms cubic-bezier(0.34, 1.56, 0.64, 1), border-color 220ms var(--ease), box-shadow 220ms var(--ease);
}
.card:hover {
  transform: translateY(-8px);
  border-color: var(--neon);
  box-shadow: 0 0 0 1px var(--neon), 0 0 30px color-mix(in srgb, var(--neon) 55%, transparent), 0 18px 40px rgb(0 0 0 / 50%);
}
.num {
  font-family: var(--font-serif);
  font-size: 1.6rem;
  font-weight: 600;
  color: var(--neon);
  text-shadow: 0 0 14px color-mix(in srgb, var(--neon) 70%, transparent);
}
.fan {
  position: absolute;
  right: 10px;
  top: 50%;
  width: 46%;
  height: 100%;
  transform: translateY(-50%);
}
.fan img {
  position: absolute;
  width: 56%;
  aspect-ratio: 2 / 3;
  object-fit: cover;
  border-radius: 6px;
  box-shadow: 0 8px 20px rgb(0 0 0 / 45%);
  transition: transform 260ms var(--ease);
}
.p0 { right: 34%; top: 16%; transform: rotate(-9deg); z-index: 1; }
.p1 { right: 12%; top: 8%; transform: rotate(0deg); z-index: 2; }
.p2 { right: -8%; top: 20%; transform: rotate(10deg); z-index: 1; }
.group:hover .p0 { transform: rotate(-13deg) translateX(-4px); }
.group:hover .p1 { transform: translateY(-6px); }
.group:hover .p2 { transform: rotate(14deg) translateX(4px); }
</style>
