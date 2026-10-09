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
</script>

<template>
  <NuxtLink
    :to="localePath(`/collections/${collection.slug}`)"
    class="card group relative flex h-full min-h-[190px] overflow-hidden rounded-[18px] p-5"
  >
    <div class="relative z-10 flex max-w-[58%] flex-col justify-between">
      <span class="num">{{ String(index).padStart(2, '0') }}</span>
      <div>
        <span class="block font-serif text-xl font-semibold leading-snug text-[#fbf3e2]">{{ collection.name }}</span>
        <span class="mt-1 block text-[13px] leading-snug text-[#cdbfa8]">{{ collection.description }}</span>
      </div>
    </div>
    <div class="fan" aria-hidden="true">
      <img v-for="(src, i) in posters" :key="i" :src="src" alt="" loading="lazy" width="120" height="180" :class="`p${i}`" />
    </div>
  </NuxtLink>
</template>

<style scoped>
.card {
  background: linear-gradient(160deg, #241d17, #15110e);
  border: 1px solid #3a2f23;
  box-shadow: 0 12px 30px rgb(20 17 15 / 22%);
  transition: transform 220ms var(--ease), border-color 220ms var(--ease), box-shadow 220ms var(--ease);
}
.card:hover {
  transform: translateY(-4px);
  border-color: #e39a2e;
  box-shadow: 0 18px 38px rgb(20 17 15 / 34%);
}
.num {
  font-family: var(--font-serif);
  font-size: 1.6rem;
  font-weight: 600;
  background: var(--grad);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
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
