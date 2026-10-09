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

// Placeholder "types" the example sentences, so the box shows what it can do.
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
      <button type="submit" class="go"><span class="gomark" aria-hidden="true">✨</span><span>{{ t('search.button') }}</span></button>
    </div>

    <fieldset class="seg dark">
      <legend class="sr-only">{{ t('search.type') }}</legend>
      <label v-for="opt in ['both', 'movie', 'tv']" :key="opt" :class="{ on: media === opt }">
        <input v-model="media" type="radio" name="media" :value="opt" class="sr-only" />
        <span aria-hidden="true">{{ icons[opt] }}</span> {{ t(`search.types.${opt}`) }}
      </label>
    </fieldset>

    <div v-if="examples" class="mt-4 flex flex-wrap items-center gap-2" :aria-label="t('search.tryLabel')">
      <span class="text-xs font-medium uppercase tracking-wider" style="color: rgb(255 255 255 / 55%)">{{ t('search.try') }}</span>
      <button v-for="e in exampleList" :key="e" type="button" class="chip chip-dark" @click="pick(e)">{{ e }}</button>
    </div>
  </form>
</template>

<style scoped>
.panel {
  padding: 14px;
  border-radius: 22px;
  background: rgb(255 255 255 / 7%);
  border: 1px solid rgb(255 255 255 / 14%);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  box-shadow: 0 24px 60px rgb(0 0 0 / 45%), inset 0 1px 0 rgb(255 255 255 / 10%);
}
.bar {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgb(11 15 25 / 55%);
  border-radius: 16px;
  padding: 6px 6px 6px 16px;
  border: 1px solid rgb(255 255 255 / 16%);
  transition: border-color var(--dur), box-shadow var(--dur);
  color: rgb(255 255 255 / 60%);
}
.bar.focused {
  border-color: #a78bfa;
  box-shadow: 0 0 0 4px rgb(139 92 246 / 30%), 0 0 28px rgb(139 92 246 / 35%);
}
.search-input {
  flex: 1;
  min-width: 0;
  min-height: 48px;
  border: 0;
  outline: none;
  background: transparent;
  font-size: 1rem;
  color: #fff;
}
.search-input::placeholder {
  color: rgb(255 255 255 / 50%);
}
.go {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 48px;
  padding: 0 24px;
  border: 0;
  border-radius: 14px;
  cursor: pointer;
  font-weight: 700;
  font-size: 1rem;
  color: #fff;
  background: linear-gradient(135deg, #8b5cf6, #ec4899);
  box-shadow: 0 0 24px rgb(236 72 153 / 50%), 0 6px 20px rgb(139 92 246 / 40%);
  transition: transform 200ms var(--ease), box-shadow 200ms var(--ease), filter 200ms var(--ease);
  animation: glow 2.8s ease-in-out infinite;
}
.go:hover {
  transform: translateY(-2px) scale(1.04);
  filter: brightness(1.12);
  box-shadow: 0 0 36px rgb(236 72 153 / 70%), 0 8px 26px rgb(139 92 246 / 55%);
}
.go:hover .gomark {
  display: inline-block;
  font-size: 1.15rem;
  transition: transform 320ms var(--ease);
}
@keyframes glow {
  50% {
    box-shadow: 0 0 34px rgb(236 72 153 / 70%), 0 6px 22px rgb(139 92 246 / 50%);
  }
}
.go:active {
  transform: scale(0.97);
}
.gomark {
  transition: transform 320ms var(--ease);
  filter: drop-shadow(0 2px 3px rgb(42 19 6 / 30%));
}
@media (prefers-reduced-motion: reduce) {
  .go {
    animation: none;
  }
}
.seg {
  display: inline-flex;
  margin-top: 12px;
  padding: 4px;
  gap: 2px;
  border-radius: 999px;
  background: rgb(11 15 25 / 55%);
  border: 1px solid rgb(255 255 255 / 12%);
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
  color: var(--ink-soft);
  transition: background var(--dur), color var(--dur);
}
.seg.dark label {
  color: rgb(255 255 255 / 80%);
}
.seg label.on {
  background: linear-gradient(135deg, #8b5cf6, #ec4899);
  color: #fff;
  font-weight: 600;
  box-shadow: 0 0 16px rgb(236 72 153 / 40%);
}
.seg label:focus-within {
  outline: 2px solid #a78bfa;
}
@media (max-width: 480px) {
  .go {
    padding: 0 16px;
  }
}
</style>
