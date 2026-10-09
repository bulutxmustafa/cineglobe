<script setup lang="ts">
const { t } = useI18n()
const localePath = useLocalePath()
const router = useRouter()
const { me, ready, refresh, logout } = useAuth()

useHead({ meta: [{ name: 'robots', content: 'noindex, nofollow' }] })
useSeoMeta({ title: () => `${t('auth.account')} | CINEGLOB` })

onMounted(async () => {
  if (!ready.value) await refresh()
  if (!me.value) router.replace(localePath('/login'))
})

async function out() {
  await logout()
  router.push(localePath('/'))
}
</script>

<template>
  <div class="container-page py-10">
    <h1 class="text-3xl">{{ t('auth.account') }}</h1>
    <div v-if="me" class="mt-6 max-w-md rounded-[10px] border p-5" style="border-color: var(--line); background: var(--surface)">
      <p class="text-sm" style="color: var(--ink-soft)">{{ t('auth.signedInAs') }}</p>
      <p class="font-semibold">{{ me.email }}</p>
      <div class="mt-5 flex flex-wrap gap-2">
        <NuxtLink :to="localePath('/favorites')" class="btn btn-quiet">{{ t('nav.favorites') }}</NuxtLink>
        <button class="btn btn-quiet" @click="out">{{ t('auth.logout') }}</button>
      </div>
    </div>
  </div>
</template>
