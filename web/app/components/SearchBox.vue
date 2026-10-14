<script setup lang="ts">
const props = defineProps<{ initial?: string; examples?: boolean; mediaType?: string; dark?: boolean }>()
const emit = defineEmits<{ submit: [query: string, type: string] }>()
const localePath = useLocalePath()
const router = useRouter()
const { t, tm, rt } = useI18n()
const q = ref(props.initial ?? '')
const media = ref(props.mediaType || 'both')
const focused = ref(false)

const exampleList = computed(() => (tm('search.examples') as string[]).map((e) => rt(e)))
const icons: Record<string, string> = { both: '✨', movie: '🎬', tv: '📺' }

// The placeholder "types" example sentences so the box shows what it can do.
const typed = ref('')
let timer: ReturnType<typeof setTimeout> | undefined
function startTyping() {
  if (!props.dark || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
  let ex = 0
  let ch = 0
  let erasing = false
  const step = () => {
    const full = exampleList.value[ex % exampleList.value.length] ?? ''
    if (!erasing) {
      ch++
      typed.value = full.slice(0, ch)
      if (ch >= full.length) {
        erasing = true
        timer = setTimeout(step, 1600)
        return
      }
    } else {
      ch -= 2
      typed.value = full.slice(0, Math.max(ch, 0))
      if (ch <= 0) {
        erasing = false
        ex++
        ch = 0
      }
    }
    timer = setTimeout(step, erasing ? 18 : 42)
  }
  step()
}
onMounted(startTyping)
onBeforeUnmount(() => clearTimeout(timer))

const shownPlaceholder = computed(() => (props.dark && typed.value ? typed.value : t('search.placeholder')))

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
  <form role="search" class="panel" :class="{ 'panel-dark': dark }" @submit.prevent="go()">
    <label for="q" class="sr-only">{{ t('search.label') }}</label>
    <div class="bar" :class="{ focused }">
      <svg class="mag" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
        <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
      </svg>
      <input
        id="q"
        v-model="q"
        type="search"
        maxlength="300"
        autocomplete="off"
        :placeholder="shownPlaceholder"
        class="search-input"
        @focus="focused = true"
        @blur="focused = false"
      />
      <button type="submit" class="go"><LogoMark :size="26" variant="default" class="spark" /><span>{{ t('search.button') }}</span></button>
    </div>

    <fieldset class="seg">
      <legend class="sr-only">{{ t('search.type') }}</legend>
      <label v-for="opt in ['both', 'movie', 'tv']" :key="opt" :class="{ on: media === opt }">
        <input v-model="media" type="radio" name="media" :value="opt" class="sr-only" />
        <span aria-hidden="true">{{ icons[opt] }}</span> {{ t(`search.types.${opt}`) }}
      </label>
    </fieldset>

    <div v-if="examples" class="mt-3 flex flex-wrap items-center gap-2" :aria-label="t('search.tryLabel')">
      <button v-for="e in exampleList.slice(0, 3)" :key="e" type="button" class="chip chip-dark" @click="pick(e)">{{ e }}</button>
    </div>
  </form>
</template>

<style scoped>
.panel {
  padding: 16px;
  border-radius: 22px;
  background: var(--box);
  border: 1px solid rgb(255 255 255 / 9%);
  box-shadow: 0 30px 60px rgb(0 0 0 / 45%);
}
.panel-dark {
  padding: 16px;
  border-radius: 20px;
  background: rgb(13 23 41 / 88%);
  backdrop-filter: blur(6px);
}
.ai {
  padding: 5px 11px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  color: #6fe0cd;
  background: rgb(79 201 181 / 13%);
  border: 1px solid rgb(79 201 181 / 28%);
}
.bar {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #f8f4ec;
  border-radius: 16px;
  padding: 6px 6px 6px 18px;
  border: 2px solid transparent;
  color: #7a6a4a;
  transition: border-color var(--dur), box-shadow var(--dur);
}
.bar.focused {
  border-color: var(--gold);
  box-shadow: 0 0 0 4px rgb(242 192 102 / 25%);
}
.search-input {
  flex: 1;
  min-width: 0;
  min-height: 50px;
  border: 0;
  outline: none;
  background: transparent;
  font-size: 0.95rem;
  color: #1d1a14;
}
.search-input::placeholder {
  color: #7d7564;
}
.go {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 50px;
  padding: 0 22px;
  border: 0;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 700;
  font-size: 0.95rem;
  color: var(--gold);
  background: #0f1d34;
  transition: transform var(--dur) var(--spring), background var(--dur);
}
.go:hover {
  transform: translateY(-1px);
  background: #16294a;
}
.go:hover .spark {
  transform: rotate(40deg) scale(1.12);
}
.go:active {
  transform: translateY(1px) scale(0.97);
}
.spark {
  flex: none;
  display: inline-block;
  transition: transform 300ms var(--spring);
}
.seg {
  display: inline-flex;
  margin-top: 14px;
  padding: 3px;
  gap: 2px;
  border-radius: 999px;
  background: rgb(255 255 255 / 5%);
  border: 1px solid rgb(255 255 255 / 12%);
}
.seg label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 36px;
  padding: 0 14px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  color: #c3cbd9;
  transition: background var(--dur), color var(--dur);
}
.seg label:hover {
  color: var(--text);
}
.seg label.on {
  background: var(--gold);
  color: var(--accent-ink);
  font-weight: 700;
}
.seg label:focus-within {
  outline: 2px solid var(--gold);
}
@media (max-width: 480px) {
  .go {
    padding: 0 14px;
  }
  .panel-dark {
    padding: 18px;
  }
}
</style>
