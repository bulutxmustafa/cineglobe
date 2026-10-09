/** Session-cookie auth (ADR-0005): the browser keeps the cookie, we send the CSRF header. */

export interface Me {
  email: string
  preferred_language: string
  email_notifications: boolean
}

function csrfFromCookie(): string {
  const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/)
  return m ? decodeURIComponent(m[1]!) : ''
}

export function useAuth() {
  const base = useApiBase()
  const me = useState<Me | null>('me', () => null)
  const ready = useState('me-ready', () => false)

  async function refresh() {
    try {
      me.value = await $fetch<Me>(`${base}/me/`, { credentials: 'include' })
    } catch {
      me.value = null
    }
    ready.value = true
  }

  async function post<T>(path: string, body?: object): Promise<T> {
    await $fetch(`${base}/auth/csrf/`, { credentials: 'include' })
    return await $fetch<T>(`${base}${path}`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'X-CSRFToken': csrfFromCookie() },
      body,
    })
  }

  async function login(email: string, password: string) {
    await post('/auth/login/', { email, password })
    await refresh()
  }
  async function register(email: string, password: string, language: string) {
    await post('/auth/register/', { email, password, preferred_language: language, age_confirmed: true })
    await refresh()
  }
  async function logout() {
    await post('/auth/logout/')
    me.value = null
  }

  return { me, ready, refresh, login, register, logout }
}

/** Human message from a DRF error body (`error.message` or field errors). */
export function apiErrorText(e: unknown, fallback: string): string {
  const data = (e as { data?: { error?: { message?: string; details?: Record<string, string[]> | null } } })?.data
  const details = data?.error?.details
  if (details) {
    const first = Object.values(details).flat()[0]
    if (first) return String(first)
  }
  return data?.error?.message || fallback
}
