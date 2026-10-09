<script setup lang="ts">
const localePath = useLocalePath()
const { locale } = useI18n()
const switchLocalePath = useSwitchLocalePath()
const { me, ready, refresh } = useAuth()
onMounted(() => {
  if (!ready.value) refresh()
})
const otherCode = computed<'tr' | 'en'>(() => (locale.value === 'tr' ? 'en' : 'tr'))
</script>

<template>
  <header class="sticky top-0 z-40 border-b backdrop-blur-md" style="border-color: var(--border); background: rgb(11 31 58 / 92%)">
    <div class="container-page flex h-16 items-center gap-4">
      <NuxtLink :to="localePath('/')" class="flex items-center gap-2.5" aria-label="FilmPusula">
        <LogoMark :size="34" />
        <span class="logo text-[1.15rem] font-extrabold tracking-[0.14em]">FilmPusula</span>
      </NuxtLink>
      <nav class="hidden items-center gap-1.5 text-sm sm:flex" :aria-label="$t('nav.main')">
        <NuxtLink :to="localePath('/')" class="nav-link">{{ $t('nav.discover') }}</NuxtLink>
        <NuxtLink :to="localePath('/collections')" class="nav-link">{{ $t('nav.collections') }}</NuxtLink>
        <NuxtLink :to="localePath('/upcoming')" class="nav-link">{{ $t('nav.upcoming') }}</NuxtLink>
        <NuxtLink :to="localePath('/favorites')" class="nav-link">{{ $t('nav.favorites') }}</NuxtLink>
      </nav>
      <div class="ml-auto flex items-center gap-2">
        <NuxtLink :to="localePath('/search')" class="btn hbtn">{{ $t('nav.search') }}</NuxtLink>
        <NuxtLink :to="localePath(me ? '/account' : '/login')" class="btn hbtn">
          {{ me ? $t('auth.account') : $t('auth.login') }}
        </NuxtLink>
        <a :href="switchLocalePath(otherCode)" class="btn hbtn !px-3 uppercase" :hreflang="otherCode" :aria-label="$t('nav.language')">{{ otherCode }}</a>
      </div>
    </div>
    <nav class="container-page flex gap-1.5 overflow-x-auto pb-2 text-sm sm:hidden" :aria-label="$t('nav.main')">
      <NuxtLink :to="localePath('/')" class="nav-link py-2">{{ $t('nav.discover') }}</NuxtLink>
      <NuxtLink :to="localePath('/collections')" class="nav-link py-2">{{ $t('nav.collections') }}</NuxtLink>
      <NuxtLink :to="localePath('/upcoming')" class="nav-link py-2">{{ $t('nav.upcoming') }}</NuxtLink>
      <NuxtLink :to="localePath('/favorites')" class="nav-link py-2">{{ $t('nav.favorites') }}</NuxtLink>
    </nav>
  </header>
</template>

<style scoped>
/* One look for every header box: filled dark navy */
.nav-link,
.hbtn {
  background: #163766;
  border: 1px solid #2b5190;
  color: #f6cf6e;
  font-weight: 700;
  white-space: nowrap;
  border-radius: 10px;
  transition: background var(--dur), border-color var(--dur), transform var(--dur) var(--spring);
}
.nav-link {
  padding: 7px 13px;
}
.nav-link:hover,
.hbtn:hover {
  background: #1d4682;
  border-color: #3b6fc0;
  transform: translateY(-1px);
}
.nav-link.router-link-exact-active {
  background: #1d4682;
  border-color: var(--gold);
  color: #ffe08a;
}
.logo {
  background: linear-gradient(95deg, #fff3c9 0%, #f9d57a 45%, #f2b950 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
</style>
