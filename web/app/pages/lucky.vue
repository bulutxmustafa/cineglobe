<script setup lang="ts">
const { t } = useI18n()
useSeoMeta({
  title: () => t('lucky.metaTitle'),
  description: () => t('lucky.metaDescription'),
})
</script>

<template>
  <div class="pt-4">
    <LuckyPicker />
  </div>
</template>
