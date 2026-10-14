<template>
  <footer class="mt-16 border-t" style="border-color: rgb(255 255 255 / 7%); background: #050a14">
    <div class="container-page grid gap-6 py-10 text-sm sm:grid-cols-[1.4fr_1fr]" style="color: var(--text-2)">
      <div>
        <p class="flex items-center gap-2.5"><LogoMark :size="30" /><span class="word">Film<span style="color: var(--gold)">Pusula</span></span></p>
        <p class="mt-3 max-w-md">{{ $t('site.tagline') }}</p>
      </div>
      <p class="text-xs leading-relaxed" style="color: var(--ink-faint)">{{ $t('footer.tmdb') }}</p>
    </div>
  </footer>
</template>

<style scoped>
.word {
  font-family: var(--font-serif);
  font-size: 1.25rem;
  font-weight: 700;
  color: #fbf6ec;
}
</style>
