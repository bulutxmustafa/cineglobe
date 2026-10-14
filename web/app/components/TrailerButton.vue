<script setup lang="ts">
// "Watch trailer": asks the API for a YouTube trailer after the page loads (no cost to
// first paint) and shows the button only when one exists. The privacy-friendly
// youtube-nocookie player is created only after a click.
const props = defineProps<{ mediaType: 'movie' | 'tv'; tmdbId: number; title: string }>()
const { t, locale } = useI18n()
const base = useApiBase()

interface Trailer {
  key: string
  name: string
  language: string
}
const trailer = ref<Trailer | null>(null)
const open = ref(false)

onMounted(async () => {
  try {
    const res = await $fetch<{ trailer: Trailer | null }>(`${base}/titles/${props.mediaType}/${props.tmdbId}/trailer/`, {
      query: { lang: locale.value },
    })
    trailer.value = res.trailer
  } catch {
    trailer.value = null
  }
})

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') open.value = false
}
watch(open, (on) => {
  document.body.style.overflow = on ? 'hidden' : ''
  if (on) window.addEventListener('keydown', onKey)
  else window.removeEventListener('keydown', onKey)
})
onBeforeUnmount(() => {
  document.body.style.overflow = ''
  window.removeEventListener('keydown', onKey)
})
</script>

<template>
  <button v-if="trailer" type="button" class="btn btn-primary" @click="open = true">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M8 5v14l11-7z" /></svg>
    {{ t('title.trailer') }}
  </button>
  <Teleport to="body">
    <div v-if="open && trailer" class="overlay" role="dialog" aria-modal="true" :aria-label="t('title.trailerOf', { name: title })" @click.self="open = false">
      <div class="box">
        <button type="button" class="close" :aria-label="t('title.closeTrailer')" @click="open = false">✕</button>
        <iframe
          :src="`https://www.youtube-nocookie.com/embed/${trailer.key}?autoplay=1&rel=0`"
          :title="t('title.trailerOf', { name: title })"
          allow="autoplay; encrypted-media; picture-in-picture; fullscreen"
          allowfullscreen
        />
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: rgb(5 12 30 / 88%);
  backdrop-filter: blur(4px);
  animation: fade 200ms ease;
}
.box {
  position: relative;
  width: min(100%, 1000px);
  aspect-ratio: 16 / 9;
  border-radius: 16px;
  overflow: hidden;
  background: #000;
  box-shadow: 0 30px 80px rgb(0 0 0 / 60%);
}
.box iframe {
  width: 100%;
  height: 100%;
  border: 0;
  display: block;
}
.close {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1;
  width: 40px;
  height: 40px;
  border-radius: 999px;
  background: rgb(5 12 30 / 75%);
  color: #fff;
  font-size: 18px;
  border: 1px solid rgb(255 255 255 / 25%);
}
.close:hover {
  border-color: var(--gold);
}
@keyframes fade {
  from {
    opacity: 0;
  }
}
</style>
