/**
 * SEO Meta composable - ported from sourcechain-geo-engine.
 * Provides setSEO() for dynamic page meta management.
 */
import { SITE_CONFIG } from '~/config/site'

export interface SEOMeta {
  title?: string
  description?: string
  keywords?: string
  image?: string
  url?: string
  type?: 'website' | 'article' | 'product'
  article?: {
    publishedTime?: string
    modifiedTime?: string
    author?: string
    section?: string
    tags?: string[]
  }
  product?: {
    price?: number
    priceCurrency?: string
    availability?: 'InStock' | 'OutOfStock' | 'PreOrder'
    brand?: string
  }
}

export function useSEOMeta() {
  const config = useRuntimeConfig()
  const route = useRoute()

  const defaultMeta: SEOMeta = {
    title: `${SITE_CONFIG.name} - 专业保温材料制造商`,
    description: SITE_CONFIG.description,
    keywords: '轻集料混凝土,保温材料,陶粒混凝土,泡沫水泥,建材厂家',
    type: 'website',
    image: SITE_CONFIG.ogImage,
  }

  function generateTitle(pageTitle: string, siteName: string = SITE_CONFIG.name): string {
    if (!pageTitle) return siteName
    return `${pageTitle} - ${siteName}`
  }

  function generateCanonicalUrl(path: string): string {
    const baseUrl = (config.public.siteUrl as string) || SITE_CONFIG.url
    return `${baseUrl}${path}`
  }

  function setSEO(meta: SEOMeta) {
    const seo = { ...defaultMeta, ...meta }

    const title = seo.title ? generateTitle(seo.title) : (defaultMeta.title || '')
    const canonicalUrl = seo.url || generateCanonicalUrl(route.path)
    const imageUrl = seo.image || defaultMeta.image

    useHead({
      title,
      link: [
        { rel: 'canonical', href: canonicalUrl },
      ],
      meta: [
        { name: 'description', content: seo.description || defaultMeta.description! },
        { name: 'keywords', content: seo.keywords || defaultMeta.keywords! },
        { property: 'og:title', content: title },
        { property: 'og:description', content: seo.description || defaultMeta.description! },
        { property: 'og:image', content: imageUrl! },
        { property: 'og:url', content: canonicalUrl },
        { property: 'og:type', content: seo.type || 'website' },
        { property: 'og:site_name', content: SITE_CONFIG.name },
        { name: 'twitter:title', content: title },
        { name: 'twitter:description', content: seo.description || defaultMeta.description! },
        { name: 'twitter:image', content: imageUrl! },
        { name: 'twitter:url', content: canonicalUrl },
      ],
    })

    if (seo.article) {
      useHead({
        meta: [
          { property: 'article:published_time', content: seo.article.publishedTime },
          { property: 'article:modified_time', content: seo.article.modifiedTime },
          { property: 'article:author', content: seo.article.author },
          { property: 'article:section', content: seo.article.section },
          { property: 'article:tag', content: seo.article.tags?.join(',') },
        ].filter(Boolean) as any[],
      })
    }

    if (seo.product) {
      useHead({
        meta: [
          { property: 'product:price:amount', content: String(seo.product.price) },
          { property: 'product:price:currency', content: seo.product.priceCurrency || 'CNY' },
          { property: 'product:availability', content: seo.product.availability || 'InStock' },
          { property: 'product:brand', content: seo.product.brand || SITE_CONFIG.name },
        ].filter(Boolean) as any[],
      })
    }
  }

  return {
    setSEO,
    generateTitle,
    generateCanonicalUrl,
    defaultMeta,
  }
}
