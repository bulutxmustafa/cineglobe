const isDev = process.env.NODE_ENV === 'development'
const swr = (seconds: number) => (isDev ? {} : { swr: seconds })
const siteUrl = process.env.NUXT_PUBLIC_SITE_URL || 'http://localhost:3000'

export default defineNuxtConfig({
  compatibilityDate: '2026-10-01',
  devtools: { enabled: false },
  modules: ['@nuxtjs/i18n', '@nuxtjs/tailwindcss'],
  css: ['~/assets/css/tokens.css', '~/assets/css/main.css'],
  runtimeConfig: {
    // Server-side only: where the Django API lives (NUXT_API_ORIGIN).
    apiOrigin: 'http://localhost:8000',
    public: { siteUrl },
  },
  app: {
    pageTransition: { name: 'page', mode: 'out-in' },
    head: {
      titleTemplate: '%s',
      link: [{ rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }],
      meta: [
        { name: 'theme-color', content: '#0b1f3a' },
        { name: 'application-name', content: 'CINEGLOB' },
      ],
    },
  },
  i18n: {
    baseUrl: siteUrl,
    seo: true,
    strategy: 'prefix',
    defaultLocale: 'tr',
    detectBrowserLanguage: false,
    locales: [
      { code: 'tr', language: 'tr-TR', name: 'TÃ¼rkÃ§e', file: 'tr.json' },
      { code: 'en', language: 'en-US', name: 'English', file: 'en.json' },
    ],
  },
  // Plan v1.8: pages are served from the CDN; the server renders only on a cache miss.
  routeRules: {
    // The browser always talks to /api/v1 on this same origin, so the session and CSRF
    // cookies are first-party; the server forwards it to Django.
    '/api/v1/**': { proxy: `${process.env.NUXT_API_ORIGIN || 'http://localhost:8000'}/api/v1/**` },
    '/tr': swr(3600),
    '/en': swr(3600),
    '/*/collections': swr(3600),
    '/*/collections/**': swr(3600),
    '/*/upcoming': swr(1800),
    '/*/title/**': swr(86400),
    '/*/person/**': swr(86400),
    '/*/search': { ssr: false },
    '/*/account': { ssr: false },
  },
  typescript: { strict: true },
})
