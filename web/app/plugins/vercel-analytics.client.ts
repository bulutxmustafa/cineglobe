// Cookie-free page view counting (Vercel Web Analytics, free on Hobby). Loaded in the browser only.
// Same snippet as the @vercel/analytics package without adding a dependency; Vercel serves the script.
export default defineNuxtPlugin(() => {
  if (import.meta.dev) return
  const w = window as unknown as { va?: (...args: unknown[]) => void; vaq?: unknown[] }
  w.va =
    w.va ||
    function (...args: unknown[]) {
      ;(w.vaq = w.vaq || []).push(args)
    }
  const s = document.createElement('script')
  s.defer = true
  s.src = '/_vercel/insights/script.js'
  document.head.appendChild(s)
})
