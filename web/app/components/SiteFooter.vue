<template>
  <footer class="mt-16 border-t" style="border-color: var(--line); background: var(--surface)">
    <div class="container-page grid gap-6 py-10 text-sm sm:grid-cols-[1.4fr_1fr]" style="color: var(--ink-soft)">
      <div>
        <p class="font-serif text-lg font-bold tracking-[0.14em]" style="color: var(--accent)">CINEGLOB</p>
        <p class="mt-1 max-w-md">{{ $t('site.tagline') }}</p>
      </div>
      <p class="text-xs leading-relaxed" style="color: var(--ink-faint)">
        {{ $t('footer.tmdb') }}
      </p>
    </div>
  </footer>
</template>
