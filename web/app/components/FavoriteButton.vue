<script setup lang="ts">
import type { TitleItem } from '~/composables/useApi'

const props = defineProps<{ item: TitleItem; compact?: boolean }>()
const { t } = useI18n()
const { has, toggle } = useFavorites()
const on = computed(() => has(props.item.media_type, props.item.tmdb_id))

function click() {
  toggle({
    media_type: props.item.media_type,
    tmdb_id: props.item.tmdb_id,
    title: titleName(props.item),
    poster_url: props.item.poster_url,
    release_date: props.item.release_date,
    vote_average: props.item.vote_average,
  })
}
</script>

<template>
  <button
    type="button"
    class="fav btn btn-quiet"
    :class="{ on, '!min-h-[36px] !px-2': compact }"
    :aria-pressed="on"
    :aria-label="on ? t('fav.remove') : t('fav.add')"
    @click.prevent.stop="click"
  >
    <span aria-hidden="true">{{ on ? '♥' : '♡' }}</span>
    <span v-if="!compact">{{ on ? t('fav.saved') : t('fav.add') }}</span>
  </button>
</template>

<style scoped>
.fav.on {
  color: var(--accent);
  border-color: var(--accent);
}
</style>
