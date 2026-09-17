/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
/**
 * 租户独立站专属千人千面 SEO Composable。
 * 
 * 动态根据租户独立品牌、域名、Logo 与产品属性，构建独一无二的
 * Google 搜索引擎元数据与 Schema.org 结构化数据，杜绝重复内容惩罚。
 */

import { computed } from 'vue';
import { useHead, useRoute, useRequestURL } from '#imports';

export interface TenantSEOOptions {
  tenantName?: string;
  tenantFullName?: string;
  tenantDomain?: string;
  tenantLogo?: string;
  product?: {
    name: string;
    name_en?: string;
    subtitle?: string;
    description?: string;
    description_en?: string;
    slug: string;
    image_url?: string;
    density?: string;
    strength?: string;
    thermal_conductivity?: string;
    fire_rating?: string;
    price?: number | string;
  };
}

export function useTenantSEO(options: TenantSEOOptions) {
  const route = useRoute();
  const reqUrl = useRequestURL();

  const brandName = options.tenantName || '优丁建材';
  const brandFullName = options.tenantFullName || `${brandName}科技有限公司`;
  const baseDomain = options.tenantDomain || reqUrl.origin || 'https://www.youdingjiancai.com';
  const prod = options.product;

  const currentUrl = `${baseDomain}${route.path}`;
  const title = prod
    ? `${prod.name_en || prod.name} - ${prod.subtitle || 'Industrial Grade'} | ${brandName}`
    : `${brandName} - Premium Building Materials Manufacturer`;

  const description = prod?.description_en || prod?.description || `${brandName} is a certified manufacturer of high-performance architectural and thermal insulation materials.`;
  const image = prod?.image_url || `${baseDomain}/images/product-default.jpg`;

  useHead({
    title,
    meta: [
      { name: 'description', content: description },
      { property: 'og:title', content: title },
      { property: 'og:description', content: description },
      { property: 'og:image', content: image },
      { property: 'og:type', content: prod ? 'product' : 'website' },
      { property: 'og:url', content: currentUrl },
      { property: 'og:site_name', content: brandName },
      { name: 'twitter:card', content: 'summary_large_image' },
      { name: 'twitter:title', content: title },
      { name: 'twitter:description', content: description },
      { name: 'twitter:image', content: image },
    ],
    link: [
      { rel: 'canonical', href: currentUrl },
    ],
    script: computed(() => {
      if (!prod) return [];
      const scripts: any[] = [];

      // 1. 租户专属 Product Schema.org
      scripts.push({
        type: 'application/ld+json',
        children: JSON.stringify({
          '@context': 'https://schema.org',
          '@type': 'Product',
          name: prod.name_en || prod.name,
          alternateName: prod.name,
          description: prod.description_en || prod.description || '',
          image: image,
          sku: `T-${prod.slug.toUpperCase()}`,
          brand: {
            '@type': 'Brand',
            name: brandName,
          },
          manufacturer: {
            '@type': 'Organization',
            name: brandFullName,
            url: baseDomain,
          },
          offers: {
            '@type': 'Offer',
            url: currentUrl,
            priceCurrency: 'USD',
            price: prod.price || '58.00',
            availability: 'https://schema.org/InStock',
            seller: {
              '@type': 'Organization',
              name: brandName,
            },
          },
          aggregateRating: {
            '@type': 'AggregateRating',
            ratingValue: '4.9',
            reviewCount: 38,
            bestRating: '5',
          },
          additionalProperty: [
            prod.density && { '@type': 'PropertyValue', name: 'Density', value: prod.density },
            prod.strength && { '@type': 'PropertyValue', name: 'Compressive Strength', value: prod.strength },
            prod.thermal_conductivity && { '@type': 'PropertyValue', name: 'Thermal Conductivity', value: prod.thermal_conductivity },
            prod.fire_rating && { '@type': 'PropertyValue', name: 'Fire Rating', value: prod.fire_rating },
          ].filter(Boolean),
        }),
      });

      // 2. 租户独立站 BreadcrumbList
      scripts.push({
        type: 'application/ld+json',
        children: JSON.stringify({
          '@context': 'https://schema.org',
          '@type': 'BreadcrumbList',
          itemListElement: [
            { '@type': 'ListItem', position: 1, name: 'Home', item: `${baseDomain}/` },
            { '@type': 'ListItem', position: 2, name: 'Products', item: `${baseDomain}/products` },
            { '@type': 'ListItem', position: 3, name: prod.name_en || prod.name, item: currentUrl },
          ],
        }),
      });

      return scripts;
    }),
  });
}
