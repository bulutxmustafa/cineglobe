/** Typed, language-aware calls to the Django API. `lang` is always explicit so the
 * CDN can cache each language separately (see backend `cdn_cache`). */

export interface TitleItem {
  media_type: 'movie' | 'tv'
  tmdb_id: number
  title: string
  display_title?: string
  original_title?: string
  overview?: string
  poster_url: string | null
  backdrop_url?: string | null
  vote_average?: number
  vote_count?: number
  release_date?: string | null
  reason?: string
  group?: string
  season_number?: number | null
}

export interface Collection {
  slug: string
  name: string
  description: string
  icon: string
  media_type: string
}

/** Server render calls Django directly; the browser uses the same-origin proxy. */
export function useApiBase() {
  if (import.meta.server) return `${useRuntimeConfig().apiOrigin.replace(/\/$/, '')}/api/v1`
  return '/api/v1'
}

export function useApiFetch<T>(path: string, query: Record<string, unknown> = {}) {
  const { locale } = useI18n()
  const base = useApiBase()
  return useFetch<T>(() => `${base}${path}`, {
    query: computed(() => ({ ...query, lang: locale.value })),
    key: `${path}:${JSON.stringify(query)}`,
    watch: [locale],
  })
}

export function titleName(item: Pick<TitleItem, 'title' | 'display_title' | 'original_title'>) {
  return item.display_title || item.title || item.original_title || ''
}

export function yearOf(date?: string | null) {
  return date ? date.slice(0, 4) : ''
}
