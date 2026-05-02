<template>
  <div>
    <!-- This component doesn't render anything visible -->
  </div>
</template>

<script setup lang="ts">
/**
 * SEO Head Component - Enhanced SEO metadata management
 * 
 * Features:
 * - Dynamic meta titles and descriptions
 * - Open Graph tags for social sharing (Facebook, LinkedIn, etc.)
 * - Twitter Card support
 * - Canonical URLs
 * - Structured data (JSON-LD) for products, cases, articles, and organization
 * - Multi-language support
 */

interface SEOProps {
  // Basic SEO
  title?: string
  description?: string
  keywords?: string[]
  
  // Open Graph
  ogType?: 'website' | 'article' | 'product' | 'profile'
  ogImage?: string
  ogImageWidth?: number
  ogImageHeight?: number
  
  // Twitter Card
  twitterCard?: 'summary' | 'summary_large_image' | 'app' | 'player'
  twitterImage?: string
  
  // Canonical URL
  canonicalUrl?: string
  
  // Structured Data
  structuredData?: Record<string, any> | Array<Record<string, any>>
  
  // Additional meta
  noindex?: boolean
  nofollow?: boolean
  robots?: string
  
  // Language
  language?: 'zh' | 'en'
}

const props = withDefaults(defineProps<SEOProps>(), {
  title: '',
  description: '',
  keywords: () => [],
  ogType: 'website',
  ogImage: '',
  ogImageWidth: 1200,
  ogImageHeight: 630,
  twitterCard: 'summary_large_image',
  twitterImage: '',
  canonicalUrl: '',
  structuredData: undefined,
  noindex: false,
  nofollow: false,
  robots: '',
  language: 'zh'
})

const config = useRuntimeConfig()
const route = useRoute()

// Base URL from environment or default
const baseUrl = config.public.siteUrl || 'https://www.youdingjiancai.com'

// Generate full URL
const fullUrl = computed(() => {
  if (props.canonicalUrl) return props.canonicalUrl
  return `${baseUrl}${route.fullPath}`
})

// Default images
const defaultOgImage = '/images/og-default.jpg'
const defaultTwitterImage = '/images/twitter-card.jpg'

// Build meta tags
const metaTags = computed(() => {
  const tags: Array<Record<string, string>> = []
  
  // Basic meta tags
  if (props.description) {
    tags.push({ name: 'description', content: props.description })
  }
  
  if (props.keywords.length > 0) {
    tags.push({ name: 'keywords', content: props.keywords.join(',') })
  }
  
  // Robots meta
  if (props.noindex || props.nofollow || props.robots) {
    const robotsValue = props.robots || `${props.noindex ? 'noindex' : 'index'},${props.nofollow ? 'nofollow' : 'follow'}`
    tags.push({ name: 'robots', content: robotsValue })
  }
  
  // Open Graph tags
  tags.push({ property: 'og:type', content: props.ogType })
  tags.push({ property: 'og:url', content: fullUrl.value })
  
  if (props.title) {
    tags.push({ property: 'og:title', content: props.title })
  }
  
  if (props.description) {
    tags.push({ property: 'og:description', content: props.description })
  }
  
  const ogImage = props.ogImage || defaultOgImage
  tags.push({ property: 'og:image', content: ogImage })
  tags.push({ property: 'og:image:width', content: String(props.ogImageWidth) })
  tags.push({ property: 'og:image:height', content: String(props.ogImageHeight) })
  
  // Twitter Card tags
  tags.push({ name: 'twitter:card', content: props.twitterCard })
  
  if (props.title) {
    tags.push({ name: 'twitter:title', content: props.title })
  }
  
  if (props.description) {
    tags.push({ name: 'twitter:description', content: props.description })
  }
  
  const twitterImage = props.twitterImage || defaultTwitterImage
  tags.push({ name: 'twitter:image', content: twitterImage })
  
  return tags
})

// Generate structured data
const jsonLd = computed(() => {
  if (!props.structuredData) return null
  
  const data = Array.isArray(props.structuredData) 
    ? props.structuredData 
    : [props.structuredData]
  
  return {
    type: 'application/ld+json',
    children: JSON.stringify({
      '@context': 'https://schema.org',
      '@graph': data
    })
  }
})

// Use Nuxt's useHead composable
useHead({
  title: props.title || undefined,
  meta: metaTags.value,
  link: props.canonicalUrl ? [{ rel: 'canonical', href: fullUrl.value }] : [],
  script: jsonLd.value ? [jsonLd.value] : []
})
</script>
