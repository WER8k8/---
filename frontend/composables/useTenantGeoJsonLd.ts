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
  reviews?: ComputedRef<Array<{ author: string; rating: number; reviewBody: string; datePublished?: string }>>
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
  const jsonLdGraph = computed(() => {
    const origin = input.siteOrigin.value.replace(/\/$/, '')
    const graph: Array<Record<string, unknown>> = []

    const org: Record<string, unknown> = {
      '@type': 'Organization',
      name: input.companyName.value,
      url: origin || undefined,
      description: input.description.value || undefined,
    }
    if (input.contactEmail.value) {
      org.email = input.contactEmail.value
    }
    if (input.contactPhone.value) {
      org.telephone = input.contactPhone.value
    }
    if (input.logoUrl.value) {
      org.logo = input.logoUrl.value
    }
    if (input.foundingDate.value) {
      org.foundingDate = input.foundingDate.value
    }
    if (input.address?.value) {
      const addr = input.address.value
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
        telephone: input.contactPhone.value || undefined,
        email: input.contactEmail.value || undefined,
        contactType: 'customer service',
        availableLanguage: ['Chinese', 'English'],
      }
    }
    graph.push(org)

    const items = (input.products.value ?? []).slice(0, 24).map((p) => {
      const product: Record<string, unknown> = {
        '@type': 'Product',
        name: p.name,
        description: p.summary || p.description || undefined,
        url: p.slug && origin ? `${origin}/tenant/products/${p.slug}` : undefined,
      }
      if (p.image_url) {
        product.image = p.image_url
      }
      if (p.specifications) {
        const props: Array<Record<string, unknown>> = []
        Object.entries(p.specifications).forEach(([key, value]) => {
          if (value) {
            props.push({
              '@type': 'PropertyValue',
              name: key,
              value: String(value),
            })
          }
        })
        if (props.length > 0) {
          product.additionalProperty = props
        }
      }
      return product
    })
    graph.push(...items)

    if (input.faqs?.value && input.faqs.value.length > 0) {
      const faqPage: Record<string, unknown> = {
        '@type': 'FAQPage',
        mainEntity: input.faqs.value.map((q) => ({
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

    if (input.services?.value && input.services.value.length > 0) {
      input.services.value.forEach((service) => {
        const serviceSchema: Record<string, unknown> = {
          '@type': 'Service',
          name: service.name,
          description: service.description,
          provider: {
            '@type': 'Organization',
            name: input.companyName.value,
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

    if (input.reviews?.value && input.reviews.value.length > 0) {
      const avgRating = input.reviews.value.reduce((sum, r) => sum + r.rating, 0) / input.reviews.value.length
      const aggregateRating: Record<string, unknown> = {
        '@type': 'AggregateRating',
        ratingValue: avgRating.toFixed(1),
        reviewCount: input.reviews.value.length,
        worstRating: 1,
        bestRating: 5,
      }
      org.aggregateRating = aggregateRating

      input.reviews.value.forEach((review) => {
        const reviewSchema: Record<string, unknown> = {
          '@type': 'Review',
          author: {
            '@type': 'Person',
            name: review.author,
          },
          reviewRating: {
            '@type': 'Rating',
            ratingValue: review.rating,
            worstRating: 1,
            bestRating: 5,
          },
          reviewBody: review.reviewBody,
        }
        if (review.datePublished) {
          reviewSchema.datePublished = review.datePublished
        }
        graph.push(reviewSchema)
      })
    }

    // VideoObject schema（产品视频 / 企业视频）
    if (input.videos?.value && input.videos.value.length > 0) {
      input.videos.value.forEach((video) => {
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
  items: ComputedRef<Array<{ name: string; url: string }>>
) {
  const schema = computed(() => ({
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.value.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.name,
      item: item.url.startsWith('http') ? item.url : item.url,
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
