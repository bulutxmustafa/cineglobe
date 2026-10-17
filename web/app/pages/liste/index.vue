<script setup lang="ts">
interface Guide {
  slug: string
  media_type: 'movie' | 'tv'
  title: string
  intro: string
  posters?: string[]
}
const { t } = useI18n()
const localePath = useLocalePath()
useSeoMeta({
  title: () => t('guides.metaTitle'),
  description: () => t('guides.metaDescription'),
  ogTitle: () => t('guides.metaTitle'),
  ogDescription: () => t('guides.metaDescription'),
})
useBreadcrumbs(() => [
  { name: t('guides.home'), path: '/' },
  { name: t('guides.title'), path: '/liste' },
])
const { data, pending, error } = await useApiFetch<{ guides: Guide[] }>('/guides/')
</script>

<template>
  <div class="container-page py-10">
    <nav class="crumbs" aria-label="breadcrumb">
      <NuxtLink :to="localePath('/')">{{ t('guides.home') }}</NuxtLink>
      <span aria-hidden="true">›</span>
      <span>{{ t('guides.title') }}</span>
    </nav>
    <h1 class="mt-3 text-3xl sm:text-4xl">{{ t('guides.title') }}</h1>
    <p class="mt-2 max-w-2xl" style="color: var(--ink-soft)">{{ t('guides.lead') }}</p>
    <div class="mt-8">
      <ApiState :pending="pending" :error="error" :empty="!data?.guides?.length">
        <ul class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          <li v-for="(g, i) in data?.guides" :key="g.slug">
            <NuxtLink :to="localePath(`/liste/${g.slug}`)" class="guide group" :class="`tone-${i % 6}`">
              <div class="relative z-10 flex h-full max-w-[58%] flex-col">
                <span class="kind">{{ g.media_type === 'tv' ? t('title.tv') : t('title.movie') }}</span>
                <span class="mt-3 block font-serif text-[1.2rem] font-bold leading-snug text-white">{{ g.title }}</span>
                <span class="mt-2 line-clamp-3 text-[12.5px] leading-relaxed text-white/80">{{ g.intro }}</span>
                <span class="more">{{ t('guides.open') }} →</span>
              </div>
              <div v-if="g.posters?.length" class="fan" aria-hidden="true">
                <img v-for="(src, k) in g.posters" :key="k" :src="src" alt="" width="120" height="180" loading="lazy" :class="`p${k}`" />
              </div>
            </NuxtLink>
          </li>
        </ul>
      </ApiState>
    </div>
  </div>
</template>

<style scoped>
.crumbs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 13px;
  color: var(--ink-soft);
}
.crumbs a:hover {
  color: var(--accent);
  text-decoration: underline;
}
.guide {
  position: relative;
  overflow: hidden;
  display: flex;
  height: 100%;
  min-height: 220px;
  padding: 22px;
  border-radius: 22px;
  border: 1px solid rgb(255 255 255 / 10%);
  box-shadow: 0 2px 4px rgb(13 40 90 / 12%), 0 16px 32px rgb(13 40 90 / 20%);
  transition: transform 280ms var(--spring), border-color 200ms var(--ease);
}
.guide:hover {
  transform: translateY(-5px);
  border-color: rgb(255 194 71 / 70%);
}
.fan {
  position: absolute;
  right: 8px;
  top: 50%;
  width: 46%;
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
.tone-0 { background: linear-gradient(135deg, #1d4ed8, #3b82f6); }
.tone-1 { background: linear-gradient(135deg, #047857, #10b981); }
.tone-2 { background: linear-gradient(135deg, #6d28d9, #a855f7); }
.tone-3 { background: linear-gradient(135deg, #0e7490, #06b6d4); }
.tone-4 { background: linear-gradient(135deg, #be185d, #ec4899); }
.tone-5 { background: linear-gradient(135deg, #c2410c, #f59e0b); }
.kind {
  align-self: flex-start;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #1b1406;
  background: #ffe3a3;
}
.more {
  margin-top: auto;
  padding-top: 14px;
  font-size: 13px;
  font-weight: 700;
  color: #ffe3a3;
}
</style>
