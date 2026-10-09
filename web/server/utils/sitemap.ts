import type { H3Event } from 'h3'

// Builds a sitemap: static pages, collections and the titles listed in them.
interface Item { media_type: 'movie' | 'tv'; tmdb_id: number }

export async function buildSitemap(event: H3Event, langs: readonly string[] = ['tr', 'en']) {
  const config = useRuntimeConfig()
  const site = String(config.public.siteUrl).replace(/\/$/, '')
  const api = `${String(config.apiOrigin).replace(/\/$/, '')}/api/v1`
  const get = <T>(path: string, query: Record<string, unknown> = {}) =>
    $fetch<T>(`${api}${path}`, { query: { lang: 'tr', ...query }, timeout: 8000 }).catch(() => null)

  const paths = new Set<string>(['', '/collections', '/upcoming', '/lucky'])
  const cols = await get<{ collections: { slug: string }[] }>('/collections/')
  const slugs = (cols?.collections ?? []).map((c) => c.slug)
  slugs.forEach((s) => paths.add(`/collections/${s}`))

  const lists = await Promise.all([
    get<{ results: Item[] }>('/popular/'),
    get<{ results: Item[] }>('/upcoming/', { media_type: 'both' }),
    ...slugs.map((s) => get<{ results: Item[] }>(`/collections/${s}/`)),
  ])
  for (const l of lists) for (const i of l?.results ?? []) paths.add(`/title/${i.media_type}/${i.tmdb_id}`)

  const urls = [...paths].map((p) => {
    const alts = ['tr', 'en'].filter((l) => langs.includes(l)).map((l) => `<xhtml:link rel="alternate" hreflang="${l}" href="${site}/${l}${p}"/>`).join('')
    return langs.map((l) => `<url><loc>${site}/${l}${p}</loc>${alts}</url>`).join('')
  })

  setHeader(event, 'content-type', 'application/xml; charset=utf-8')
  setHeader(event, 'cache-control', 'public, s-maxage=86400, stale-while-revalidate=604800')
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">${urls.join('')}</urlset>`
}
