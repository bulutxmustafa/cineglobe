<script setup lang="ts">
// Canonical + hreflang (TR/EN) for every page.
const head = useLocaleHead({ dir: true, seo: true })
useHead(() => ({
  htmlAttrs: head.value.htmlAttrs,
  link: head.value.link,
  meta: head.value.meta,
}))
</script>

<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
