<template>
  <footer class="border-t" style="border-color: var(--border); background: rgb(11 31 58 / 96%)">
    <div class="container-page grid gap-6 py-10 text-sm sm:grid-cols-[1.4fr_1fr]" style="color: var(--text-2)">
      <div>
        <p class="flex items-center gap-2.5 text-lg font-extrabold tracking-[0.14em]"><LogoMark :size="30" /><span class="word">CINEGLOB</span></p>
        <p class="mt-2 max-w-md">{{ $t('site.tagline') }}</p>
      </div>
      <p class="text-xs leading-relaxed" style="color: var(--ink-faint)">{{ $t('footer.tmdb') }}</p>
    </div>
  </footer>
</template>

<style scoped>
.word {
  background: linear-gradient(95deg, #fff3c9 0%, #f9d57a 45%, #f2b950 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
</style>
