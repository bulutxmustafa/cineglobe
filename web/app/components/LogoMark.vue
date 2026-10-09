<script setup lang="ts">
// FilmPusula mark: a globe (meridians) with a play triangle, in sky blue and emerald.
withDefaults(defineProps<{ size?: number; variant?: string }>(), { size: 34, variant: 'default' })
</script>

<template>
  <svg :width="size" :height="size" viewBox="0 0 48 48" aria-hidden="true">
    <defs><linearGradient id="cgG" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#a6f7da"/><stop offset=".5" stop-color="#34c7c0"/><stop offset="1" stop-color="#1b8fd8"/></linearGradient></defs>
<circle cx="24" cy="24" r="22" fill="url(#cgG)"/>
<g fill="none" stroke="#06283c" stroke-opacity="0.3" stroke-width="1.4"><ellipse cx="24" cy="24" rx="9" ry="22"/><path d="M2.5 24h43M5 14.5h38M5 33.5h38"/></g>
<circle cx="24" cy="24" r="22" fill="none" stroke="#06283c" stroke-opacity="0.4" stroke-width="1.6"/>
<path d="M19.5 15.5v17l14-8.5z" fill="#06283c"/>
  </svg>
</template>
