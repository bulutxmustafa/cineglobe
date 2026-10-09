<script setup lang="ts">
// A 3D carousel of posters. While `spinning` it whirls; when it stops it lands exactly
// on `pickPoster` (the title that was chosen).
const props = defineProps<{ posters: string[]; spinning: boolean; pickPoster: string | null }>()
const emit = defineEmits<{ landed: [] }>()

const N = 9
const step = 360 / N
const slots = ref<string[]>([])
const angle = ref(0)
let raf = 0
let landing: { from: number; to: number; start: number; dur: number } | null = null
let speed = 0.12 // degrees per frame while idle

function fill() {
  const base = props.posters.length ? props.posters : []
  slots.value = Array.from({ length: N }, (_, i) => base[i % Math.max(base.length, 1)] ?? '')
}
watch(() => props.posters, fill, { immediate: true })

function land() {
  const front = Math.round(-angle.value / step)
  const back = (((front + Math.floor(N / 2)) % N) + N) % N
  if (props.pickPoster) slots.value[back] = props.pickPoster
  const targetSlot = props.pickPoster ? back : ((front % N) + N) % N
  // end with targetSlot facing front, after at least two more turns
  let to = -targetSlot * step
  while (to > angle.value - 720) to -= 360
  landing = { from: angle.value, to, start: performance.now(), dur: 2400 }
}

watch(
  () => props.spinning,
  (on) => {
    if (!on) land()
    else landing = null
  },
)

onMounted(() => {
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const tick = (now: number) => {
    if (landing) {
      const t = Math.min((now - landing.start) / landing.dur, 1)
      const e = 1 - Math.pow(1 - t, 4)
      angle.value = landing.from + (landing.to - landing.from) * e
      if (t >= 1) {
        landing = null
        speed = 0
        emit('landed')
      }
    } else if (props.spinning) {
      speed += (reduced ? 2 : 14 - speed) * 0.05
      angle.value -= speed
    } else {
      speed += (0.12 - speed) * 0.02
      angle.value -= speed
    }
    raf = requestAnimationFrame(tick)
  }
  raf = requestAnimationFrame(tick)
})
onBeforeUnmount(() => cancelAnimationFrame(raf))
</script>

<template>
  <div class="stage" role="img" :aria-label="$t('lucky.wheelAlt')">
    <div class="glow" />
    <div class="ring" :style="{ transform: `translateZ(calc(var(--w) * -1.75)) rotateY(${angle}deg)` }">
      <div
        v-for="(src, i) in slots"
        :key="i"
        class="card"
        :style="{ transform: `rotateY(${i * step}deg) translateZ(calc(var(--w) * 1.75))` }"
      >
        <img v-if="src" :src="src" alt="" width="200" height="300" />
      </div>
    </div>
    <div class="floor" />
  </div>
</template>

<style scoped>
.stage {
  --w: 128px;
  position: relative;
  margin: 0 auto;
  height: calc(var(--w) * 1.5 + 70px);
  width: 100%;
  max-width: 640px;
  perspective: 1100px;
  overflow: visible;
}
@media (min-width: 640px) {
  .stage {
    --w: 160px;
  }
}
.ring {
  position: absolute;
  left: 50%;
  top: 20px;
  width: 0;
  height: calc(var(--w) * 1.5);
  transform-style: preserve-3d;
}
.card {
  position: absolute;
  left: calc(var(--w) / -2);
  width: var(--w);
  height: calc(var(--w) * 1.5);
  backface-visibility: hidden;
  border-radius: 10px;
  overflow: hidden;
  background: #2a2119;
  border: 2px solid rgb(233 180 76 / 90%);
  box-shadow: 0 16px 40px rgb(0 0 0 / 55%);
}
.card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.glow {
  position: absolute;
  left: 50%;
  top: 10%;
  width: 70%;
  height: 80%;
  transform: translateX(-50%);
  background: radial-gradient(ellipse, rgb(233 180 76 / 16%), transparent 65%);
  pointer-events: none;
}
.floor {
  position: absolute;
  left: 50%;
  bottom: 6px;
  width: 60%;
  height: 22px;
  transform: translateX(-50%);
  background: radial-gradient(ellipse, rgb(0 0 0 / 55%), transparent 70%);
}
</style>
