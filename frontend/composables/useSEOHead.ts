/**
 * SEO Helper Functions - Generate structured data and metadata
 */

import type { Product, Case } from '~/types';
import { SITE_CONFIG } from '~/config/site';

export interface SEOMetadata {
  title: string;
  description: string;
  keywords?: string[];
  ogImage?: string;
  canonicalUrl?: string;
  structuredData?: Record<string, any>;
}

/**
 * Generate Organization Schema
 */
export function generateOrganizationSchema() {
  return {
    '@type': 'Organization',
    name: SITE_CONFIG.fullName,
    alternateName: 'Youding Building Materials Co., Ltd.',
    url: SITE_CONFIG.url,
    logo: `${SITE_CONFIG.url}/images/logo.png`,
    description: SITE_CONFIG.description,
    address: {
      '@type': 'PostalAddress',
      streetAddress: SITE_CONFIG.address,
      addressLocality: '北京',
      addressRegion: '北京市',
      postalCode: '100000',
      addressCountry: 'CN',
    },
    contactPoint: {
      '@type': 'ContactPoint',
      telephone: SITE_CONFIG.phone,
      contactType: 'customer service',
      availableLanguage: ['Chinese', 'English'],
    },
    sameAs: ['https://weibo.com/youding', 'https://www.linkedin.com/company/youding'],
  };
}

/**
 * Generate Product Schema
 */
export function generateProductSchema(product: Product) {
  return {
    '@type': 'Product',
    name: product.name,
    description: product.description || '',
    image: product.images?.[0] || `${SITE_CONFIG.url}${SITE_CONFIG.productDefaultImage}`,
    sku: product.id,
    brand: {
      '@type': 'Brand',
      name: SITE_CONFIG.name,
    },
    offers: {
      '@type': 'Offer',
      url: `${SITE_CONFIG.url}/products/${product.slug || product.id}`,
      priceCurrency: 'CNY',
      price: product.price || 0,
      availability:
        product.stock && product.stock > 0
          ? 'https://schema.org/InStock'
          : 'https://schema.org/OutOfStock',
      seller: {
        '@type': 'Organization',
        name: SITE_CONFIG.fullName,
      },
    },
    aggregateRating: product.rating
      ? {
          '@type': 'AggregateRating',
          ratingValue: product.rating,
          reviewCount: product.reviewCount || 0,
        }
      : undefined,
    additionalProperty: [
      product.category && {
        '@type': 'PropertyValue',
        name: '类别',
        value: product.category,
      },
      product.specifications?.density && {
        '@type': 'PropertyValue',
        name: '密度',
        value: product.specifications.density,
      },
      product.specifications?.strength && {
        '@type': 'PropertyValue',
        name: '强度',
        value: product.specifications.strength,
      },
    ].filter(Boolean),
  };
}

/**
 * Generate Article Schema (for news/cases)
 */
export function generateArticleSchema(article: {
  title: string;
  description: string;
  image?: string;
  author?: string;
  datePublished?: string;
  dateModified?: string;
  url: string;
}) {
  return {
    '@type': 'Article',
    headline: article.title,
    description: article.description,
    image: article.image || '/images/article-default.jpg',
    author: {
      '@type': 'Organization',
      name: article.author || SITE_CONFIG.fullName,
    },
    publisher: {
      '@type': 'Organization',
      name: SITE_CONFIG.fullName,
      logo: {
        '@type': 'ImageObject',
        url: `${SITE_CONFIG.url}/images/logo.png`,
      },
    },
    datePublished: article.datePublished,
    dateModified: article.dateModified || article.datePublished,
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': article.url,
    },
  };
}

/**
 * Generate Case Study Schema
 */
export function generateCaseSchema(caseStudy: Case) {
  return {
    '@type': 'CreativeWork',
    name: caseStudy.title,
    description: caseStudy.description || '',
    image: caseStudy.images?.[0] || '/images/case-default.jpg',
    url: `${SITE_CONFIG.url}/cases/${caseStudy.slug || caseStudy.id}`,
    author: {
      '@type': 'Organization',
      name: SITE_CONFIG.fullName,
    },
    about: caseStudy.category || '保温工程案例',
    locationCreated: {
      '@type': 'Place',
      name: caseStudy.location || '',
    },
    dateCreated: caseStudy.completionDate,
    text: caseStudy.description,
  };
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
      item: item.url.startsWith('http') ? item.url : `${SITE_CONFIG.url}${item.url}`,
    })),
  };
}

/**
 * Generate FAQPage Schema
 */
export function generateFAQSchema(questions: Array<{ question: string; answer: string }>) {
  return {
    '@type': 'FAQPage',
    mainEntity: questions.map((q) => ({
      '@type': 'Question',
      name: q.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: q.answer,
      },
    })),
  };
}

/**
 * Generate LocalBusiness Schema
 */
export function generateLocalBusinessSchema() {
  return {
    '@type': 'LocalBusiness',
    name: SITE_CONFIG.fullName,
    image: `${SITE_CONFIG.url}/images/store.jpg`,
    telephone: SITE_CONFIG.phone,
    email: SITE_CONFIG.email,
    address: {
      '@type': 'PostalAddress',
      streetAddress: SITE_CONFIG.address,
      addressLocality: '北京',
      addressRegion: '北京市',
      postalCode: '100000',
      addressCountry: 'CN',
    },
    geo: {
      '@type': 'GeoCoordinates',
      latitude: 39.9042,
      longitude: 116.4074,
    },
    openingHoursSpecification: {
      '@type': 'OpeningHoursSpecification',
      dayOfWeek: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
      opens: '09:00',
      closes: '18:00',
    },
    priceRange: '$$',
  };
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
    generateLocalBusinessSchema,
  };
}
