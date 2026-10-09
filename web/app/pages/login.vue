<script setup lang="ts">
const { t, locale } = useI18n()
const localePath = useLocalePath()
const router = useRouter()
const { login, register } = useAuth()

useHead({ meta: [{ name: 'robots', content: 'noindex, follow' }] })
useSeoMeta({ title: () => `${t('auth.title')} | CINEGLOB` })

const mode = ref<'login' | 'register'>('login')
const email = ref('')
const password = ref('')
const adult = ref(false)
const busy = ref(false)
const error = ref('')

async function submit() {
  error.value = ''
  if (mode.value === 'register' && !adult.value) {
    error.value = t('auth.needAdult')
    return
  }
  busy.value = true
  try {
    if (mode.value === 'login') await login(email.value, password.value)
    else await register(email.value, password.value, locale.value)
    await router.push(localePath('/account'))
  } catch (e) {
    error.value = apiErrorText(e, t('auth.failed'))
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="container-page py-10">
    <div class="mx-auto max-w-md">
      <h1 class="text-3xl">{{ mode === 'login' ? t('auth.login') : t('auth.register') }}</h1>
      <p class="mt-2 text-sm" style="color: var(--ink-soft)">{{ t('auth.optional') }}</p>

      <form class="mt-6 space-y-4 rounded-[10px] border p-5" style="border-color: var(--line); background: var(--surface)" @submit.prevent="submit">
        <div>
          <label for="email" class="mb-1 block text-sm font-medium">{{ t('auth.email') }}</label>
          <input id="email" v-model="email" type="email" required autocomplete="email" class="field" />
        </div>
        <div>
          <label for="pw" class="mb-1 block text-sm font-medium">{{ t('auth.password') }}</label>
          <input
            id="pw"
            v-model="password"
            type="password"
            required
            minlength="8"
            :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
            class="field"
          />
          <p v-if="mode === 'register'" class="mt-1 text-xs" style="color: var(--ink-faint)">{{ t('auth.passwordHint') }}</p>
        </div>
        <label v-if="mode === 'register'" class="flex items-start gap-2 text-sm">
          <input v-model="adult" type="checkbox" class="mt-1 h-4 w-4" />
          <span>{{ t('auth.adult') }}</span>
        </label>
        <p v-if="error" class="text-sm font-medium" style="color: var(--accent)" role="alert">{{ error }}</p>
        <button type="submit" class="btn btn-primary w-full" :disabled="busy">
          {{ mode === 'login' ? t('auth.login') : t('auth.register') }}
        </button>
      </form>

      <p class="mt-4 text-center text-sm">
        <button type="button" class="underline underline-offset-4" @click="mode = mode === 'login' ? 'register' : 'login'; error = ''">
          {{ mode === 'login' ? t('auth.toRegister') : t('auth.toLogin') }}
        </button>
      </p>
    </div>
  </div>
</template>

<style scoped>
.field {
  width: 100%;
  min-height: 44px;
  border: 1px solid var(--line-strong);
  border-radius: 6px;
  padding: 0 12px;
  background: #0e1620;
  color: var(--text);
  outline: none;
}
.field:focus {
  border-color: var(--ink);
  box-shadow: 0 0 0 3px var(--accent-soft);
}
</style>
