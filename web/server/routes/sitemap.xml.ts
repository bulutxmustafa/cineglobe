import { buildSitemap } from '../utils/sitemap'

export default defineEventHandler((event) => buildSitemap(event))
