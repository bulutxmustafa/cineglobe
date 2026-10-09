<script setup lang="ts">
import type { TitleItem } from '~/composables/useApi'

const { t } = useI18n()
const { items } = useFavorites()
useHead({ meta: [{ name: 'robots', content: 'noindex, follow' }] })
useSeoMeta({ title: () => `${t('fav.title')} | CINEGLOB` })

const list = computed(() => items.value.map((f) => ({ ...f, display_title: f.title }) as TitleItem))
</script>

<template>
  <div class="container-page py-10">
    <h1 class="text-3xl">{{ t('fav.title') }}</h1>
    <p class="mt-2 max-w-2xl" style="color: var(--ink-soft)">{{ t('fav.lead') }}</p>
    <div class="mt-6">
      <ApiState :empty="!list.length">
        <TitleGrid :items="list" />
      </ApiState>
    </div>
  </div>
</template>
