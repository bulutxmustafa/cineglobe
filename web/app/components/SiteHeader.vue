<script setup lang="ts">
const localePath = useLocalePath()
const { locale } = useI18n()
const switchLocalePath = useSwitchLocalePath()
const { me, ready, refresh } = useAuth()
onMounted(() => { if (!ready.value) refresh() })
const otherCode = computed<'tr' | 'en'>(() => (locale.value === 'tr' ? 'en' : 'tr'))
</script>

<template>
  <header class="sticky top-0 z-40 border-b backdrop-blur-md" style="border-color: rgb(255 255 255 / 10%); background: rgb(11 29 58 / 92%)">
    <div class="container-page flex h-16 items-center gap-6">
      <NuxtLink :to="localePath('/')" class="flex items-center gap-2.5" aria-label="CINEGLOB">
        <LogoMark :size="34" />
        <span class="logo font-serif text-[1.35rem] font-bold tracking-[0.14em]">CINEGLOB</span>
      </NuxtLink>
      <nav class="hidden items-center gap-5 text-sm sm:flex" :aria-label="$t('nav.main')">
        <NuxtLink :to="localePath('/')" class="nav-link">{{ $t('nav.discover') }}</NuxtLink>
        <NuxtLink :to="localePath('/collections')" class="nav-link">{{ $t('nav.collections') }}</NuxtLink>
        <NuxtLink :to="localePath('/upcoming')" class="nav-link">{{ $t('nav.upcoming') }}</NuxtLink>
        <NuxtLink :to="localePath('/lucky')" class="nav-link">{{ $t('nav.lucky') }}</NuxtLink>
        <NuxtLink :to="localePath('/favorites')" class="nav-link">{{ $t('nav.favorites') }}</NuxtLink>
      </nav>
      <div class="ml-auto flex items-center gap-2">
        <NuxtLink :to="localePath('/search')" class="btn btn-glass">{{ $t('nav.search') }}</NuxtLink>
        <NuxtLink :to="localePath(me ? '/account' : '/login')" class="btn btn-glass">
          {{ me ? $t('auth.account') : $t('auth.login') }}
        </NuxtLink>
        <a
          :href="switchLocalePath(otherCode)"
          class="btn btn-glass !px-3 uppercase"
          :hreflang="otherCode"
          :aria-label="$t('nav.language')"
        >{{ otherCode }}</a>
      </div>
    </div>
    <nav class="container-page flex gap-5 overflow-x-auto pb-2 text-sm sm:hidden" :aria-label="$t('nav.main')">
      <NuxtLink :to="localePath('/')" class="nav-link py-2">{{ $t('nav.discover') }}</NuxtLink>
      <NuxtLink :to="localePath('/collections')" class="nav-link py-2">{{ $t('nav.collections') }}</NuxtLink>
      <NuxtLink :to="localePath('/upcoming')" class="nav-link py-2">{{ $t('nav.upcoming') }}</NuxtLink>
      <NuxtLink :to="localePath('/lucky')" class="nav-link py-2">{{ $t('nav.lucky') }}</NuxtLink>
      <NuxtLink :to="localePath('/favorites')" class="nav-link py-2">{{ $t('nav.favorites') }}</NuxtLink>
    </nav>
  </header>
</template>

<style scoped>
.nav-link {
  color: rgb(255 255 255 / 70%);
  white-space: nowrap;
  transition: color var(--dur);
}
.nav-link:hover,
.nav-link.router-link-exact-active {
  color: #fff;
}
.logo {
  background: linear-gradient(135deg, #f1fffb, #5eead4);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.nav-link.router-link-exact-active {
  text-decoration: underline;
  text-decoration-color: var(--accent);
  text-underline-offset: 6px;
  text-decoration-thickness: 2px;
}
</style>
