/** The YouTube trailer of a title, fetched once in the browser and shared by the
 * "watch trailer" button and the playing hero background. `undefined` = not loaded yet. */
export interface Trailer {
  key: string
  name: string
  language: string
}

export function useTrailer(mediaType: string, tmdbId: number) {
  const { locale } = useI18n()
  const base = useApiBase()
  const trailer = useState<Trailer | null | undefined>(`trailer:${mediaType}:${tmdbId}`, () => undefined)
  const loading = useState<boolean>(`trailer-loading:${mediaType}:${tmdbId}`, () => false)

  onMounted(async () => {
    if (trailer.value !== undefined || loading.value) return
    loading.value = true
    try {
      const res = await $fetch<{ trailer: Trailer | null }>(`${base}/titles/${mediaType}/${tmdbId}/trailer/`, {
        query: { lang: locale.value },
      })
      trailer.value = res.trailer
    } catch {
      trailer.value = null
    } finally {
      loading.value = false
    }
  })
  return trailer
}

/** Whether the trailer pop-up is open (the hero background pauses meanwhile). */
export const useTrailerModal = () => useState<boolean>('trailer-modal', () => false)

/** True while the trailer plays behind the title hero (the poster steps aside). */
export const useHeroVideoOn = () => useState<boolean>('hero-video-on', () => false)
