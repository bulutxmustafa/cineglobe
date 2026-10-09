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
  <form role="search" class="panel" @submit.prevent="go()">
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
      <button type="submit" class="go"><span class="spark" aria-hidden="true">✨</span><span>{{ t('search.button') }}</span></button>
    </div>

    <fieldset class="seg">
      <legend class="sr-only">{{ t('search.type') }}</legend>
      <label v-for="opt in ['both', 'movie', 'tv']" :key="opt" :class="{ on: media === opt }">
        <input v-model="media" type="radio" name="media" :value="opt" class="sr-only" />
        <span aria-hidden="true">{{ icons[opt] }}</span> {{ t(`search.types.${opt}`) }}
      </label>
    </fieldset>

    <div v-if="examples" class="mt-4 flex flex-wrap items-center gap-2" :aria-label="t('search.tryLabel')">
      <span class="text-xs font-semibold uppercase tracking-wider" style="color: var(--ink-faint)">{{ t('search.try') }}</span>
      <button v-for="e in exampleList" :key="e" type="button" class="chip" @click="pick(e)">{{ e }}</button>
    </div>
  </form>
</template>

<style scoped>
.panel {
  padding: 14px;
  border-radius: 20px;
  background: rgb(23 37 54 / 92%);
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
}
.bar {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #0e1620;
  border-radius: 14px;
  padding: 5px 5px 5px 16px;
  border: 1px solid var(--border);
  color: var(--text-2);
  transition: border-color var(--dur), box-shadow var(--dur);
}
.bar.focused {
  border-color: var(--gold);
  box-shadow: 0 0 0 3px rgb(242 185 80 / 18%);
}
.search-input {
  flex: 1;
  min-width: 0;
  min-height: 48px;
  border: 0;
  outline: none;
  background: transparent;
  font-size: 1rem;
  color: var(--text);
}
.search-input::placeholder {
  color: #7f90a2;
}
.go {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 48px;
  padding: 0 22px;
  border: 0;
  border-radius: 12px;
  cursor: pointer;
  font-weight: 800;
  font-size: 1rem;
  color: var(--accent-ink);
  background: var(--gold);
  box-shadow: 0 2px 0 #b9852a, 0 10px 20px rgb(0 0 0 / 30%);
  transition: transform var(--dur) var(--spring), filter var(--dur), box-shadow var(--dur);
}
.go:hover {
  transform: translateY(-2px);
  filter: brightness(1.07);
}
.go:hover .spark {
  transform: rotate(18deg) scale(1.2);
}
.go:active {
  transform: translateY(1px) scale(0.97);
  box-shadow: 0 0 0 #b9852a, 0 4px 8px rgb(0 0 0 / 30%);
}
.spark {
  display: inline-block;
  transition: transform 300ms var(--spring);
}
.seg {
  display: inline-flex;
  margin-top: 12px;
  padding: 3px;
  gap: 2px;
  border-radius: 999px;
  background: #0e1620;
  border: 1px solid var(--border);
}
.seg label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 38px;
  padding: 0 14px;
  border-radius: 999px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  color: var(--text-2);
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
  .go span:last-child {
    font-size: 0.9rem;
  }
}
</style>
