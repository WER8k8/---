/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
import { computed, type ComputedRef } from 'vue'
import type { TenantCatalogProduct } from '../utils/tenant-product-slug'

export interface TenantGeoJsonLdInput {
  companyName: ComputedRef<string>
  description: ComputedRef<string>
  siteOrigin: ComputedRef<string>
  contactEmail: ComputedRef<string>
  contactPhone: ComputedRef<string>
  products: ComputedRef<TenantCatalogProduct[]>
  faqs?: ComputedRef<Array<{ question: string; answer: string }>>
  services?: ComputedRef<Array<{ name: string; description: string; url?: string }>>
  address?: ComputedRef<{
    streetAddress?: string
    addressLocality?: string
    addressRegion?: string
    postalCode?: string
    addressCountry?: string
  }>
  logoUrl?: ComputedRef<string>
  foundingDate?: ComputedRef<string>
  videos?: ComputedRef<Array<{
    name: string
    description: string
    thumbnailUrl: string
    contentUrl: string
    uploadDate?: string
    duration?: string
  }>>
}

export function useTenantGeoJsonLd(input: TenantGeoJsonLdInput) {
  /** 可选 ComputedRef 安全读值（SSR 下调用方可能未传 logoUrl/foundingDate 等） */
  const read = <T,>(r?: ComputedRef<T>): T | undefined => (r == null ? undefined : r.value)

  const jsonLdGraph = computed(() => {
    const origin = (input.siteOrigin?.value || '').replace(/\/$/, '')
    const graph: Array<Record<string, unknown>> = []

    const org: Record<string, unknown> = {
      '@type': 'Organization',
      '@id': origin || undefined,
      name: input.companyName?.value || '',
      url: origin || undefined,
      description: input.description?.value || undefined,
    }
    if (input.contactEmail?.value) {
      org.email = input.contactEmail.value
    }
    if (input.contactPhone?.value) {
      org.telephone = input.contactPhone.value
    }
    const logoUrl = read(input.logoUrl)
    if (logoUrl) {
      org.logo = logoUrl
    }
    const foundingDate = read(input.foundingDate)
    if (foundingDate) {
      org.foundingDate = foundingDate
    }
    const addr = read(input.address)
    if (addr) {
      org.address = {
        '@type': 'PostalAddress',
        streetAddress: addr.streetAddress || undefined,
        addressLocality: addr.addressLocality || undefined,
        addressRegion: addr.addressRegion || undefined,
        postalCode: addr.postalCode || undefined,
        addressCountry: addr.addressCountry || undefined,
      }
      org.contactPoint = {
        '@type': 'ContactPoint',
        telephone: input.contactPhone?.value || undefined,
        email: input.contactEmail?.value || undefined,
        contactType: 'customer service',
        availableLanguage: ['Chinese', 'English'],
      }
    }
    graph.push(org)

    const items = (read(input.products) ?? []).slice(0, 24).map((p) => {
      const product: Record<string, unknown> = {
        '@type': 'Product',
        name: p.name,
        description: p.summary || p.description || undefined,
        url: p.slug && origin ? `${origin}/tenant/products/${p.slug}` : undefined,
      }
      if (p.image) {
        product.image = p.image
      }
      if (p.specs && p.specs.length > 0) {
        const props = p.specs
          .filter((s) => s.label && s.value)
          .map((s) => ({
            '@type': 'PropertyValue',
            name: s.label,
            value: String(s.value),
          }))
        if (props.length > 0) {
          product.additionalProperty = props
        }
      }
      if (!product.offers) {
        product.offers = {
          '@type': 'Offer',
          priceCurrency: 'USD',
          availability: 'https://schema.org/InStock',
          url: (product.url as string) || origin || undefined,
        }
      }
      return product
    })
    graph.push(...items)

    const faqs = read(input.faqs)
    if (faqs && faqs.length > 0) {
      const faqPage: Record<string, unknown> = {
        '@type': 'FAQPage',
        mainEntity: faqs.map((q) => ({
          '@type': 'Question',
          name: q.question,
          acceptedAnswer: {
            '@type': 'Answer',
            text: q.answer,
          },
        })),
      }
      graph.push(faqPage)
    }

    const services = read(input.services)
    if (services && services.length > 0) {
      services.forEach((service) => {
        const serviceSchema: Record<string, unknown> = {
          '@type': 'Service',
          name: service.name,
          description: service.description,
          provider: {
            '@type': 'Organization',
            name: input.companyName?.value || '',
          },
        }
        if (service.url) {
          serviceSchema.url = service.url.startsWith('http')
            ? service.url
            : `${origin}${service.url}`
        }
        graph.push(serviceSchema)
      })
    }

    // VideoObject schema（产品视频 / 企业视频）
    const videos = read(input.videos)
    if (videos && videos.length > 0) {
      videos.forEach((video) => {
        const videoSchema: Record<string, unknown> = {
          '@type': 'VideoObject',
          name: video.name,
          description: video.description,
          thumbnailUrl: video.thumbnailUrl,
          contentUrl: video.contentUrl,
        }
        if (video.uploadDate) {
          videoSchema.uploadDate = video.uploadDate
        }
        if (video.duration) {
          videoSchema.duration = video.duration
        }
        graph.push(videoSchema)
      })
    }

    return {
      '@context': 'https://schema.org',
      '@graph': graph,
    }
  })

  useHead(() => ({
    script: [
      {
        type: 'application/ld+json',
        key: 'tenant-geo-jsonld',
        innerHTML: JSON.stringify(jsonLdGraph.value),
      },
    ],
  }))

  return { jsonLdGraph }
}

export function generateWebPageSchema(
  pageName: ComputedRef<string>,
  pageUrl: ComputedRef<string>,
  pageDescription?: ComputedRef<string>
) {
  const schema = computed(() => ({
    '@context': 'https://schema.org',
    '@type': 'WebPage',
    name: pageName.value,
    url: pageUrl.value,
    description: pageDescription?.value || undefined,
  }))

  useHead(() => ({
    script: [
      {
        type: 'application/ld+json',
        key: 'webpage-schema',
        innerHTML: JSON.stringify(schema.value),
      },
    ],
  }))

  return { schema }
}

export function generateBreadcrumbSchema(
  items: ComputedRef<Array<{ name: string; url: string }>>,
  baseUrl: string = ''
) {
  const schema = computed(() => ({
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.value.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.name,
      item: item.url.startsWith('http') ? item.url : `${baseUrl}${item.url}`,
    })),
  }))

  useHead(() => ({
    script: [
      {
        type: 'application/ld+json',
        key: 'breadcrumb-schema',
        innerHTML: JSON.stringify(schema.value),
      },
    ],
  }))

  return { schema }
}
