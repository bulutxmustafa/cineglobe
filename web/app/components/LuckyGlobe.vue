<script setup lang="ts">
// A 3D globe that spins fast while a pick is being made and slows down when it is done.
import * as THREE from 'three'

const props = defineProps<{ spinning: boolean }>()
const host = ref<HTMLDivElement | null>(null)
let raf = 0
let cleanup = () => {}

function earthTexture(): THREE.CanvasTexture {
  const c = document.createElement('canvas')
  c.width = 1024
  c.height = 512
  const g = c.getContext('2d')!
  const sea = g.createLinearGradient(0, 0, 0, 512)
  sea.addColorStop(0, '#1d2a8f')
  sea.addColorStop(0.5, '#2563eb')
  sea.addColorStop(1, '#1d2a8f')
  g.fillStyle = sea
  g.fillRect(0, 0, 1024, 512)
  // soft "continents": random blobs, deterministic so it never flickers
  let seed = 7
  const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647)
  for (let i = 0; i < 70; i++) {
    const x = rnd() * 1024
    const y = 60 + rnd() * 392
    const r = 18 + rnd() * 58
    const land = g.createRadialGradient(x, y, 2, x, y, r)
    land.addColorStop(0, '#34d399')
    land.addColorStop(1, 'rgba(52,211,153,0)')
    g.fillStyle = land
    g.beginPath()
    g.arc(x, y, r, 0, Math.PI * 2)
    g.fill()
  }
  g.strokeStyle = 'rgba(255,255,255,0.14)'
  g.lineWidth = 1
  for (let x = 0; x <= 1024; x += 64) {
    g.beginPath()
    g.moveTo(x, 0)
    g.lineTo(x, 512)
    g.stroke()
  }
  for (let y = 0; y <= 512; y += 64) {
    g.beginPath()
    g.moveTo(0, y)
    g.lineTo(1024, y)
    g.stroke()
  }
  return new THREE.CanvasTexture(c)
}

onMounted(() => {
  const el = host.value!
  const size = () => Math.min(el.clientWidth, 420)
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(size(), size())
  el.appendChild(renderer.domElement)
  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100)
  camera.position.z = 3.6

  const globe = new THREE.Mesh(
    new THREE.SphereGeometry(1, 64, 64),
    new THREE.MeshStandardMaterial({ map: earthTexture(), roughness: 0.55, metalness: 0.1 }),
  )
  globe.rotation.z = 0.35
  scene.add(globe)
  const glow = new THREE.Mesh(
    new THREE.SphereGeometry(1.12, 48, 48),
    new THREE.MeshBasicMaterial({ color: 0xf2c25c, transparent: true, opacity: 0.14, side: THREE.BackSide }),
  )
  scene.add(glow)
  scene.add(new THREE.AmbientLight(0xffffff, 0.9))
  const sun = new THREE.DirectionalLight(0xffd9a0, 2.2)
  sun.position.set(3, 2, 4)
  scene.add(sun)

  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  let speed = 0.004
  const tick = () => {
    const target = props.spinning ? (reduced ? 0.03 : 0.32) : 0.004
    speed += (target - speed) * (props.spinning ? 0.08 : 0.025)
    globe.rotation.y += speed
    renderer.render(scene, camera)
    raf = requestAnimationFrame(tick)
  }
  tick()
  const onResize = () => renderer.setSize(size(), size())
  window.addEventListener('resize', onResize)
  cleanup = () => {
    cancelAnimationFrame(raf)
    window.removeEventListener('resize', onResize)
    renderer.dispose()
    renderer.domElement.remove()
  }
})
onBeforeUnmount(() => cleanup())
</script>

<template>
  <div ref="host" class="mx-auto flex aspect-square w-full max-w-[420px] items-center justify-center" role="img" :aria-label="$t('lucky.globeAlt')" />
</template>
