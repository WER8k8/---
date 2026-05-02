/**
 * SEO Helper Functions - Generate structured data and metadata
 */

import type { Product, Case } from '~/types'

export interface SEOMetadata {
  title: string
  description: string
  keywords?: string[]
  ogImage?: string
  canonicalUrl?: string
  structuredData?: Record<string, any>
}

/**
 * Generate Organization Schema
 */
export function generateOrganizationSchema() {
  return {
    '@type': 'Organization',
    name: '优丁建材有限公司',
    alternateName: 'Youding Building Materials Co., Ltd.',
    url: 'https://www.youdingjiancai.com',
    logo: 'https://www.youdingjiancai.com/images/logo.png',
    description: '专注新型建筑材料研发与生产，为客户提供优质、环保、高性能的轻集料混凝土产品',
    address: {
      '@type': 'PostalAddress',
      streetAddress: '北京市朝阳区xxx路xxx号',
      addressLocality: '北京',
      addressRegion: '北京市',
      postalCode: '100000',
      addressCountry: 'CN'
    },
    contactPoint: {
      '@type': 'ContactPoint',
      telephone: '+86-400-888-8888',
      contactType: 'customer service',
      availableLanguage: ['Chinese', 'English']
    },
    sameAs: [
      'https://weibo.com/youding',
      'https://www.linkedin.com/company/youding'
    ]
  }
}

/**
 * Generate Product Schema
 */
export function generateProductSchema(product: Product) {
  const baseUrl = 'https://www.youdingjiancai.com'
  
  return {
    '@type': 'Product',
    name: product.name,
    description: product.description || '',
    image: product.images?.[0] || '/images/product-default.jpg',
    sku: product.id,
    brand: {
      '@type': 'Brand',
      name: '优丁建材'
    },
    offers: {
      '@type': 'Offer',
      url: `${baseUrl}/products/${product.slug || product.id}`,
      priceCurrency: 'CNY',
      price: product.price || 0,
      availability: product.stock && product.stock > 0 
        ? 'https://schema.org/InStock' 
        : 'https://schema.org/OutOfStock',
      seller: {
        '@type': 'Organization',
        name: '优丁建材有限公司'
      }
    },
    aggregateRating: product.rating ? {
      '@type': 'AggregateRating',
      ratingValue: product.rating,
      reviewCount: product.reviewCount || 0
    } : undefined,
    additionalProperty: [
      product.category && {
        '@type': 'PropertyValue',
        name: '类别',
        value: product.category
      },
      product.specifications?.density && {
        '@type': 'PropertyValue',
        name: '密度',
        value: product.specifications.density
      },
      product.specifications?.strength && {
        '@type': 'PropertyValue',
        name: '强度',
        value: product.specifications.strength
      }
    ].filter(Boolean)
  }
}

/**
 * Generate Article Schema (for news/cases)
 */
export function generateArticleSchema(article: {
  title: string
  description: string
  image?: string
  author?: string
  datePublished?: string
  dateModified?: string
  url: string
}) {
  return {
    '@type': 'Article',
    headline: article.title,
    description: article.description,
    image: article.image || '/images/article-default.jpg',
    author: {
      '@type': 'Organization',
      name: article.author || '优丁建材有限公司'
    },
    publisher: {
      '@type': 'Organization',
      name: '优丁建材有限公司',
      logo: {
        '@type': 'ImageObject',
        url: 'https://www.youdingjiancai.com/images/logo.png'
      }
    },
    datePublished: article.datePublished,
    dateModified: article.dateModified || article.datePublished,
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': article.url
    }
  }
}

/**
 * Generate Case Study Schema
 */
export function generateCaseSchema(caseStudy: Case) {
  const baseUrl = 'https://www.youdingjiancai.com'
  
  return {
    '@type': 'CreativeWork',
    name: caseStudy.title,
    description: caseStudy.description || '',
    image: caseStudy.images?.[0] || '/images/case-default.jpg',
    url: `${baseUrl}/cases/${caseStudy.slug || caseStudy.id}`,
    author: {
      '@type': 'Organization',
      name: '优丁建材有限公司'
    },
    about: caseStudy.category || '保温工程案例',
    locationCreated: {
      '@type': 'Place',
      name: caseStudy.location || ''
    },
    dateCreated: caseStudy.completionDate,
    text: caseStudy.description
  }
}

/**
 * Generate BreadcrumbList Schema
 */
export function generateBreadcrumbSchema(items: Array<{ name: string; url: string }>) {
  return {
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.name,
      item: item.url.startsWith('http') ? item.url : `https://www.youdingjiancai.com${item.url}`
    }))
  }
}

/**
 * Generate FAQPage Schema
 */
export function generateFAQSchema(questions: Array<{ question: string; answer: string }>) {
  return {
    '@type': 'FAQPage',
    mainEntity: questions.map(q => ({
      '@type': 'Question',
      name: q.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: q.answer
      }
    }))
  }
}

/**
 * Generate LocalBusiness Schema
 */
export function generateLocalBusinessSchema() {
  return {
    '@type': 'LocalBusiness',
    name: '优丁建材有限公司',
    image: 'https://www.youdingjiancai.com/images/store.jpg',
    telephone: '+86-400-888-8888',
    email: 'info@youdingjiancai.com',
    address: {
      '@type': 'PostalAddress',
      streetAddress: '北京市朝阳区xxx路xxx号',
      addressLocality: '北京',
      addressRegion: '北京市',
      postalCode: '100000',
      addressCountry: 'CN'
    },
    geo: {
      '@type': 'GeoCoordinates',
      latitude: 39.9042,
      longitude: 116.4074
    },
    openingHoursSpecification: {
      '@type': 'OpeningHoursSpecification',
      dayOfWeek: [
        'Monday',
        'Tuesday',
        'Wednesday',
        'Thursday',
        'Friday'
      ],
      opens: '09:00',
      closes: '18:00'
    },
    priceRange: '$$'
  }
}

/**
 * Composable for easy SEO usage in components
 */
export function useSEOHead() {
  return {
    generateOrganizationSchema,
    generateProductSchema,
    generateArticleSchema,
    generateCaseSchema,
    generateBreadcrumbSchema,
    generateFAQSchema,
    generateLocalBusinessSchema
  }
}
