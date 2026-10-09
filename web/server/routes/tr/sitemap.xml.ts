import { buildSitemap } from '../../utils/sitemap'

// Search Console property is https://<site>/tr/, so this sitemap lists only /tr URLs.
export default defineEventHandler((event) => buildSitemap(event, ['tr']))
