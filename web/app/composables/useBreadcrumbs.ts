/** Adds a schema.org BreadcrumbList so Google understands where a page sits
 * (Home › Lists › Best thriller films). `path` is locale-free, e.g. '/liste'. */
export function useBreadcrumbs(items: () => { name: string; path: string }[]) {
  const config = useRuntimeConfig()
  const localePath = useLocalePath()
  const site = String(config.public.siteUrl).replace(/\/$/, '')
  useHead({
    script: [
      {
        type: 'application/ld+json',
        key: 'breadcrumbs',
        innerHTML: computed(() =>
          JSON.stringify({
            '@context': 'https://schema.org',
            '@type': 'BreadcrumbList',
            itemListElement: items().map((item, i) => ({
              '@type': 'ListItem',
              position: i + 1,
              name: item.name,
              item: `${site}${localePath(item.path)}`,
            })),
          }),
        ),
      },
    ],
  })
}
