<script setup lang="ts">
const props = defineProps<{ initial?: string; examples?: boolean; mediaType?: string; dark?: boolean }>()
const emit = defineEmits<{ submit: [query: string, type: string] }>()
const localePath = useLocalePath()
const router = useRouter()
const { t, tm, rt } = useI18n()
const q = ref(props.initial ?? '')
const media = ref(props.mediaType || 'both')

const exampleList = computed(() => (tm('search.examples') as string[]).map((e) => rt(e)))

function go(text = q.value) {
  const value = text.trim()
  if (value.length < 2) return
  emit('submit', value, media.value)
  router.push({ path: localePath('/search'), query: { q: value, type: media.value } })
}
function pick(text: string) {
  q.value = text
  go(text)
}
</script>

<template>
  <form role="search" @submit.prevent="go()">
    <label for="q" class="sr-only">{{ t('search.label') }}</label>
    <div class="flex flex-col gap-2 sm:flex-row">
      <input
        id="q"
        v-model="q"
        type="search"
        maxlength="300"
        autocomplete="off"
        :placeholder="t('search.placeholder')"
        class="search-input min-h-[52px] flex-1 rounded-[6px] border bg-white px-4 text-base"
      />
      <button type="submit" class="btn btn-primary min-h-[52px] px-6">{{ t('search.button') }}</button>
    </div>
    <fieldset class="mt-3 flex flex-wrap items-center gap-2">
      <legend class="sr-only">{{ t('search.type') }}</legend>
      <label
        v-for="opt in ['both', 'movie', 'tv']"
        :key="opt"
        class="chip cursor-pointer"
        :class="[dark ? 'chip-dark' : '', { 'chip-on': media === opt }]"
      >
        <input v-model="media" type="radio" name="media" :value="opt" class="sr-only" />
        {{ t(`search.types.${opt}`) }}
      </label>
    </fieldset>
    <div v-if="examples" class="mt-4 flex flex-wrap gap-2" :aria-label="t('search.tryLabel')">
      <button v-for="e in exampleList" :key="e" type="button" class="chip" :class="{ 'chip-dark': dark }" @click="pick(e)">{{ e }}</button>
    </div>
  </form>
</template>

<style scoped>
.search-input {
  border-color: var(--line-strong);
  outline: none;
  transition: border-color var(--dur);
}
.search-input:focus {
  border-color: var(--ink);
  box-shadow: 0 0 0 3px var(--accent-soft);
}
.chip-on {
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
}
.chip-dark.chip-on {
  background: #fff;
  color: var(--night);
  border-color: #fff;
}
</style>
