<script setup lang="ts">
// The trailer playing silently behind the title hero, like a cinema lobby screen.
// Desktop only, never with "reduce motion" or data saver; a button turns the sound on.
const props = defineProps<{ mediaType: 'movie' | 'tv'; tmdbId: number }>()
const { t } = useI18n()
const trailer = useTrailer(props.mediaType, props.tmdbId)
const modalOpen = useTrailerModal()

const enabled = ref(false)
const visible = ref(false)
const muted = ref(true)
const frame = ref<HTMLIFrameElement | null>(null)

onMounted(() => {
  const saveData = (navigator as unknown as { connection?: { saveData?: boolean } }).connection?.saveData
  enabled.value =
    window.innerWidth >= 768 && !window.matchMedia('(prefers-reduced-motion: reduce)').matches && !saveData
})

const src = computed(() => {
  const key = trailer.value?.key
  if (!key) return ''
  const params = new URLSearchParams({
    autoplay: '1',
    mute: '1',
    loop: '1',
    playlist: key,
    controls: '0',
    rel: '0',
    playsinline: '1',
    disablekb: '1',
    iv_load_policy: '3',
    enablejsapi: '1',
    origin: window.location.origin,
  })
  return `https://www.youtube-nocookie.com/embed/${key}?${params}`
})

function command(func: string, args: unknown[] = []) {
  frame.value?.contentWindow?.postMessage(JSON.stringify({ event: 'command', func, args }), '*')
}
function onLoad() {
  // Let YouTube's title overlay fade out before showing the video.
  setTimeout(() => (visible.value = true), 2200)
}
function toggleSound() {
  muted.value = !muted.value
  if (muted.value) command('mute')
  else {
    command('unMute')
    command('setVolume', [70])
  }
}
watch(modalOpen, (open) => command(open ? 'pauseVideo' : 'playVideo'))
</script>

<template>
  <template v-if="enabled && src">
    <iframe
      ref="frame"
      :src="src"
      class="vid"
      :class="{ on: visible }"
      title=""
      tabindex="-1"
      aria-hidden="true"
      allow="autoplay; encrypted-media"
      @load="onLoad"
    />
    <button v-if="visible" type="button" class="sound" :aria-pressed="!muted" @click="toggleSound">
      <svg v-if="muted" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M11 5 6 9H2v6h4l5 4z" /><path d="m23 9-6 6M17 9l6 6" /></svg>
      <svg v-else viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M11 5 6 9H2v6h4l5 4z" /><path d="M15.5 8.5a5 5 0 0 1 0 7M19 5a10 10 0 0 1 0 14" /></svg>
      {{ muted ? t('title.soundOn') : t('title.soundOff') }}
    </button>
  </template>
</template>

<style scoped>
.vid {
  position: absolute;
  top: 50%;
  left: 50%;
  width: max(100vw, 177.78svh);
  height: max(56.25vw, 100svh);
  transform: translate(-50%, -50%) scale(1.12);
  border: 0;
  pointer-events: none;
  opacity: 0;
  transition: opacity 1.6s ease;
}
.vid.on {
  opacity: 1;
}
.sound {
  position: absolute;
  right: 24px;
  bottom: 24px;
  z-index: 3;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 40px;
  padding: 0 16px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  background: rgb(5 12 30 / 60%);
  border: 1px solid rgb(255 255 255 / 25%);
  backdrop-filter: blur(6px);
  transition: border-color var(--dur), background var(--dur);
}
.sound:hover {
  border-color: var(--gold);
  background: rgb(5 12 30 / 80%);
}
</style>
