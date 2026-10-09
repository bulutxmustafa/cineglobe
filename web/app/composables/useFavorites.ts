/** Guest favourites, kept in this browser only (localStorage). They are merged into
 * the account notebook after sign-in (POST /me/notebook/merge/). */

export interface Favorite {
  media_type: 'movie' | 'tv'
  tmdb_id: number
  title: string
  poster_url: string | null
  release_date?: string | null
  vote_average?: number
}

const KEY = 'cineglob:favorites'

export function useFavorites() {
  const items = useState<Favorite[]>('favorites', () => [])

  onMounted(() => {
    try {
      items.value = JSON.parse(localStorage.getItem(KEY) || '[]')
    } catch {
      items.value = []
    }
  })

  function save() {
    try {
      localStorage.setItem(KEY, JSON.stringify(items.value))
    } catch {
      /* private mode: favourites live for this visit only */
    }
  }
  const has = (type: string, id: number) => items.value.some((f) => f.media_type === type && f.tmdb_id === id)
  function toggle(fav: Favorite) {
    if (has(fav.media_type, fav.tmdb_id)) {
      items.value = items.value.filter((f) => !(f.media_type === fav.media_type && f.tmdb_id === fav.tmdb_id))
    } else {
      items.value = [fav, ...items.value].slice(0, 500)
    }
    save()
  }
  return { items, has, toggle }
}
