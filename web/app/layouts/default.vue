<template>
  <div class="flex min-h-screen flex-col">
    <a
      href="#main"
      class="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:bg-white focus:p-2"
    >
      {{ $t('nav.skip') }}
    </a>
    <SiteHeader />
    <main id="main" class="flex-1"><slot /></main>
    <SiteFooter />
  </div>
</template>
