<script setup lang="ts">
import type { NuxtError } from '#app'

defineProps<{ error: NuxtError }>()
const localePath = useLocalePath()
useHead({ meta: [{ name: 'robots', content: 'noindex' }] })
</script>

<template>
  <NuxtLayout>
    <div class="container-page py-24 text-center">
      <p class="font-serif text-6xl font-semibold" style="color: var(--accent)">{{ error.statusCode }}</p>
      <h1 class="mt-3 text-2xl">{{ $t('error.title') }}</h1>
      <p class="mt-2" style="color: var(--ink-soft)">{{ $t('error.body') }}</p>
      <NuxtLink :to="localePath('/')" class="btn btn-primary mt-6" @click="clearError()">{{ $t('error.home') }}</NuxtLink>
    </div>
  </NuxtLayout>
</template>
