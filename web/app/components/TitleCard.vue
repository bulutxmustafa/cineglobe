<script setup lang="ts">
import type { TitleItem } from '~/composables/useApi'

const props = defineProps<{ item: TitleItem; showReason?: boolean }>()
const localePath = useLocalePath()
const { t, locale } = useI18n()
const name = computed(() => titleName(props.item))
const year = computed(() => yearOf(props.item.release_date))
const rating = computed(() => (props.item.vote_average ? props.item.vote_average.toFixed(1) : ''))
const dateText = computed(() =>
  props.item.group && props.item.release_date
    ? new Intl.DateTimeFormat(locale.value, { day: 'numeric', month: 'long' }).format(new Date(props.item.release_date))
    : '',
)
</script>

<template>
  <article class="group relative flex flex-col">
    <FavoriteButton :item="item" compact class="absolute right-2 top-2 z-10 !bg-[#0b0f19]/70" />
    <NuxtLink :to="localePath(`/title/${item.media_type}/${item.tmdb_id}`)" class="block">
      <div class="relative aspect-[2/3] overflow-hidden rounded-[6px]" style="background: var(--line); box-shadow: var(--shadow)">
        <img
          v-if="item.poster_url"
          :src="item.poster_url"
          :alt="t('title.posterAlt', { name })"
          width="342"
          height="513"
          loading="lazy"
          class="poster h-full w-full object-cover"
        />
        <div v-else class="flex h-full items-center justify-center p-3 text-center text-sm" style="color: var(--ink-faint)">
          {{ name }}
        </div>
        <span
          class="badge absolute left-2 top-2"
          :style="item.media_type === 'tv' ? 'background: #8b5cf6; color: #fff' : 'background: rgb(255 255 255 / 92%); color: #0b0f19'"
        >{{ item.media_type === 'tv' ? t('title.tv') : t('title.movie') }}</span>
      </div>
      <h3 class="mt-2 line-clamp-2 font-sans text-[0.95rem] font-semibold leading-snug">{{ name }}</h3>
    </NuxtLink>
    <p class="mt-0.5 flex items-center gap-2 text-xs" style="color: var(--ink-soft)">
      <span v-if="dateText">{{ dateText }}</span>
      <span v-else-if="year">{{ year }}</span>
      <span v-if="rating" class="font-medium" style="color: var(--star)">★ {{ rating }}</span>
    </p>
    <p v-if="showReason && item.reason" class="mt-1.5 text-[13px] leading-snug" style="color: var(--ink-soft)">
      {{ item.reason }}
    </p>
  </article>
</template>

<style scoped>
.poster {
  transition: transform 300ms var(--ease);
}
.group:hover .poster {
  transform: scale(1.03);
}
</style>
