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
    <FavoriteButton :item="item" compact class="fav absolute right-2 top-2 z-10" />
    <NuxtLink :to="localePath(`/title/${item.media_type}/${item.tmdb_id}`)" class="block">
      <div class="frame relative aspect-[2/3] overflow-hidden rounded-[12px]">
        <img
          v-if="item.poster_url"
          :src="item.poster_url"
          :alt="t('title.posterAlt', { name })"
          width="342"
          height="513"
          loading="lazy"
          class="poster h-full w-full object-cover"
        />
        <div v-else class="flex h-full items-center justify-center p-3 text-center text-sm" style="color: var(--ink-faint)">{{ name }}</div>
        <span class="badge absolute left-2 top-2" :style="item.media_type === 'tv' ? 'background: var(--teal); color: #fff' : 'background: var(--gold); color: #1a1305'">
          {{ item.media_type === 'tv' ? t('title.tv') : t('title.movie') }}
        </span>
        <span v-if="rating" class="rating absolute bottom-2 left-2">★ {{ rating }}</span>
      </div>
      <h3 class="mt-2.5 line-clamp-2 font-sans text-[0.85rem] font-semibold leading-snug">{{ name }}</h3>
    </NuxtLink>
    <p class="mt-0.5 text-[13px]" style="color: var(--ink-soft)">
      <span v-if="dateText">{{ dateText }}</span>
      <span v-else-if="year">{{ year }}</span>
    </p>
    <p v-if="showReason && item.reason" class="mt-1.5 text-[13px] leading-snug" style="color: var(--ink-soft)">{{ item.reason }}</p>
  </article>
</template>

<style scoped>
.frame {
  background: var(--line);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
  transition: border-color 200ms var(--ease), box-shadow 200ms var(--ease);
}
.group:hover .frame {
  border-color: var(--gold);
}
.poster {
  transition: transform 360ms var(--ease);
}
.group:hover .poster {
  transform: scale(1.05);
}
.rating {
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  color: var(--gold);
  background: rgb(16 25 35 / 82%);
}
.fav {
  background: rgb(16 25 35 / 72%) !important;
  color: #fff;
  border-color: rgb(255 255 255 / 25%);
}
</style>
