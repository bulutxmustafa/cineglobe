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
  <header class="sticky top-0 z-40 border-b backdrop-blur-xl" style="border-color: rgb(255 255 255 / 7%); background: rgb(5 12 30 / 94%)">
    <div class="container-page flex h-[64px] items-center gap-3 sm:h-[68px] sm:gap-6">
      <NuxtLink :to="localePath('/')" class="flex items-center gap-2.5" aria-label="FilmPusula">
        <LogoMark :size="32" class="shrink-0" />
        <span class="word">Film<span class="gold">Pusula</span></span>
      </NuxtLink>
      <nav class="hidden items-center gap-6 text-[15px] font-medium lg:flex" :aria-label="$t('nav.main')">
        <NuxtLink :to="localePath('/')" class="nav-link">{{ $t('nav.discover') }}</NuxtLink>
        <NuxtLink :to="localePath('/collections')" class="nav-link">{{ $t('nav.collections') }}</NuxtLink>
        <NuxtLink :to="localePath('/liste')" class="nav-link">{{ $t('nav.guides') }}</NuxtLink>
        <NuxtLink :to="localePath('/upcoming')" class="nav-link">{{ $t('nav.upcoming') }}</NuxtLink>
        <NuxtLink :to="localePath('/favorites')" class="nav-link">{{ $t('nav.favorites') }}</NuxtLink>
      </nav>
      <div class="ml-auto flex shrink-0 items-center gap-1.5 sm:gap-2">
        <NuxtLink :to="localePath('/search')" class="icon-btn" :aria-label="$t('nav.search')">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>
        </NuxtLink>
        <a :href="switchLocalePath(otherCode)" class="pill uppercase" :hreflang="otherCode" :aria-label="$t('nav.language')">{{ otherCode }}</a>
        <NuxtLink :to="localePath(me ? '/account' : '/login')" class="cta">
          {{ me ? $t('auth.account') : $t('auth.login') }}
        </NuxtLink>
      </div>
    </div>
    <nav class="container-page flex gap-5 overflow-x-auto pb-3 text-sm font-medium lg:hidden" :aria-label="$t('nav.main')">
      <NuxtLink :to="localePath('/')" class="nav-link">{{ $t('nav.discover') }}</NuxtLink>
      <NuxtLink :to="localePath('/collections')" class="nav-link">{{ $t('nav.collections') }}</NuxtLink>
      <NuxtLink :to="localePath('/liste')" class="nav-link">{{ $t('nav.guides') }}</NuxtLink>
      <NuxtLink :to="localePath('/upcoming')" class="nav-link">{{ $t('nav.upcoming') }}</NuxtLink>
      <NuxtLink :to="localePath('/favorites')" class="nav-link">{{ $t('nav.favorites') }}</NuxtLink>
    </nav>
  </header>
</template>

<style scoped>
.word {
  font-family: var(--font-serif);
  font-size: 1.2rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: #fbf6ec;
}
.gold {
  color: var(--gold);
}
.nav-link {
  position: relative;
  padding: 6px 0;
  white-space: nowrap;
  color: #c3cbd9;
  transition: color var(--dur);
}
.nav-link::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: -2px;
  height: 2px;
  border-radius: 2px;
  background: var(--gold);
  transform: scaleX(0);
  transition: transform 240ms var(--ease);
}
.nav-link:hover {
  color: #fbf6ec;
}
.nav-link.router-link-exact-active {
  color: #fbf6ec;
}
.nav-link.router-link-exact-active::after,
.nav-link:hover::after {
  transform: scaleX(1);
}
.icon-btn,
.pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  min-width: 40px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid rgb(255 255 255 / 16%);
  color: #e8ecf3;
  font-size: 13px;
  font-weight: 600;
  transition: border-color var(--dur), background var(--dur);
}
.icon-btn {
  display: none;
  padding: 0;
}
.icon-btn:hover,
.pill:hover {
  border-color: var(--gold);
  background: rgb(242 192 102 / 8%);
}
.cta {
  display: inline-flex;
  align-items: center;
  min-height: 40px;
  padding: 0 14px;
  border-radius: 999px;
  background: var(--gold);
  color: var(--accent-ink);
  font-size: 14px;
  font-weight: 700;
  white-space: nowrap;
  transition: transform var(--dur) var(--spring), filter var(--dur);
}
@media (min-width: 640px) {
  .icon-btn {
    display: inline-flex;
  }
  .word {
    font-size: 1.45rem;
  }
  .cta {
    padding: 0 20px;
  }
}
.cta:hover {
  transform: translateY(-1px);
  filter: brightness(1.06);
}
</style>
