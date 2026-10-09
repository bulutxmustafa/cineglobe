const siteUrl = process.env.NUXT_PUBLIC_SITE_URL || 'http://localhost:3000'

export default defineNuxtConfig({
  compatibilityDate: '2026-10-01',
  devtools: { enabled: false },
  modules: ['@nuxtjs/i18n', '@nuxtjs/tailwindcss'],
  css: ['~/assets/css/tokens.css', '~/assets/css/main.css'],
  runtimeConfig: {
    public: {
      apiBase: 'http://localhost:8000/api/v1',
      siteUrl,
    },
  },
  app: {
    head: {
      titleTemplate: '%s',
      link: [{ rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }],
      meta: [
        { name: 'theme-color', content: '#f7f5f0' },
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
      { code: 'tr', language: 'tr-TR', name: 'Türkçe', file: 'tr.json' },
      { code: 'en', language: 'en-US', name: 'English', file: 'en.json' },
    ],
  },
  // Plan v1.8: pages are served from the CDN; the server renders only on a cache miss.
  routeRules: {
    '/tr': { swr: 3600 },
    '/en': { swr: 3600 },
    '/*/collections': { swr: 3600 },
    '/*/collections/**': { swr: 3600 },
    '/*/upcoming': { swr: 1800 },
    '/*/title/**': { swr: 86400 },
    '/*/person/**': { swr: 86400 },
    '/*/search': { ssr: false },
    '/*/account': { ssr: false },
  },
  typescript: { strict: true },
})
