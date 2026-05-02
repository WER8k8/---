import { defineEventHandler, setHeader } from 'h3'

export default defineEventHandler((event) => {
  const baseUrl = 'https://youding.com'
  
  const pages = [
    { path: '/', priority: '1.0', changefreq: 'daily' },
    { path: '/products', priority: '0.9', changefreq: 'weekly' },
    { path: '/cases', priority: '0.8', changefreq: 'weekly' },
    { path: '/about', priority: '0.7', changefreq: 'monthly' },
    { path: '/news', priority: '0.8', changefreq: 'daily' },
    { path: '/contact', priority: '0.6', changefreq: 'monthly' },
    { path: '/privacy', priority: '0.5', changefreq: 'yearly' },
    { path: '/terms', priority: '0.5', changefreq: 'yearly' },
  ]

  const today = new Date().toISOString().split('T')[0]

  let xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
  xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

  pages.forEach((page) => {
    xml += '  <url>\n'
    xml += `    <loc>${baseUrl}${page.path}</loc>\n`
    xml += `    <lastmod>${today}</lastmod>\n`
    xml += `    <changefreq>${page.changefreq}</changefreq>\n`
    xml += `    <priority>${page.priority}</priority>\n`
    xml += '  </url>\n'
  })

  xml += '</urlset>'

  setHeader(event, 'Content-Type', 'application/xml')
  return xml
})
