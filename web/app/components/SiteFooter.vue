<script setup lang="ts">
// The contact address is assembled in the browser only, so it never appears as plain
// text in the server HTML that spam bots scrape.
const contact = ref('')
onMounted(() => {
  contact.value = ['iletisim', 'filmpusula.com'].join('@')
})
</script>

<template>
  <footer class="mt-16 border-t" style="border-color: rgb(255 255 255 / 7%); background: #0a1838">
    <div class="container-page grid gap-6 py-10 text-sm sm:grid-cols-[1.4fr_1fr]" style="color: var(--text-2)">
      <div>
        <p class="flex items-center gap-2.5"><LogoMark :size="30" /><span class="word">Film<span style="color: var(--gold)">Pusula</span></span></p>
        <p class="mt-3 max-w-md">{{ $t('site.tagline') }}</p>
        <p class="mt-4 flex items-center gap-2">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="m3 7 9 6 9-6" /></svg>
          <span>{{ $t('footer.contact') }}:</span>
          <a v-if="contact" :href="`mailto:${contact}`" class="mail">{{ contact }}</a>
        </p>
      </div>
      <p class="text-xs leading-relaxed" style="color: var(--ink-faint)">{{ $t('footer.tmdb') }}</p>
    </div>
  </footer>
</template>

<style scoped>
.mail {
  color: var(--gold);
  font-weight: 600;
}
.mail:hover {
  text-decoration: underline;
  text-underline-offset: 3px;
}
.word {
  font-family: var(--font-serif);
  font-size: 1.25rem;
  font-weight: 700;
  color: #fbf6ec;
}
</style>
