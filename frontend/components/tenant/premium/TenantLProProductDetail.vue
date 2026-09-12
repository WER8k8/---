<template>
  <PremiumB2bShell
    active-key="products"
    :document-title="documentTitle"
    :document-description="documentDescription"
  >
    <section class="lpro-section lpro-section--white">
      <div class="lpro-container">
        <NuxtLink to="/tenant/products" class="lpro-link mb-4 inline-block">← {{ tSite('nav_products') }}</NuxtLink>
        <div v-if="product" class="lpro-detail-layout">
          <div>
            <div class="lpro-thumb mb-4">
              <img
                v-if="product.image"
                :src="resolveMediaUrl(product.image)"
                :alt="product.imageAlt || product.name"
              />
            </div>
            <a
              v-if="product.downloadUrl"
              :href="resolveMediaUrl(product.downloadUrl)"
              class="lpro-btn lpro-btn-primary"
              target="_blank"
              rel="noopener noreferrer"
            >
              {{ tSite('download_datasheet') }}
            </a>
          </div>
          <div>
            <h1 class="text-2xl font-bold mb-2">{{ product.name }}</h1>
            <p v-if="product.category" class="text-sm text-[var(--lpro-muted)] mb-3">{{ product.category }}</p>
            <p class="mb-4">{{ product.summary }}</p>
            <table v-if="product.specs?.length" class="lpro-spec-table mb-6">
              <tbody>
                <tr v-for="(row, i) in product.specs" :key="i">
                  <th>{{ row.label }}</th>
                  <td>{{ row.value }}</td>
                </tr>
              </tbody>
            </table>
            <TenantInquiryForm
              :tenant-id="tenant?.id"
              :tenant-domain="tenant?.domain"
              :api-base="apiBase"
              :product-placeholder="product.name"
              :cn-compliant-only="cnCompliantOnly"
              :t-site="tSite"
              :attribution="inquiryAttribution"
            />
          </div>
        </div>
        <div v-else>
          <h1 class="lpro-section-title">{{ tSite('product_not_found') }}</h1>
          <NuxtLink to="/tenant/products" class="lpro-link">{{ tSite('nav_products') }}</NuxtLink>
        </div>
      </div>
    </section>
  </PremiumB2bShell>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import PremiumB2bShell from './PremiumB2bShell.vue';
import TenantInquiryForm from '../TenantInquiryForm.vue';
import { useTenantSiteBootstrap } from '../../../composables/useTenantSiteBootstrap';
import { findProductBySlug } from '../../../utils/tenant-product-slug';
import { useTenantMediaUrl } from '../../../composables/useTenantMediaUrl';

const route = useRoute();
const { resolveMediaUrl } = useTenantMediaUrl();
const {
  tenant,
  localizedCatalogProducts,
  tSite,
  cnCompliantOnly,
  apiBase,
} = useTenantSiteBootstrap();

const slug = computed(() => String(route.params.slug || ''));
const product = computed(() => findProductBySlug(localizedCatalogProducts.value, slug.value));
const documentTitle = computed(() => product.value?.name || '');
const documentDescription = computed(() => product.value?.summary || '');

// ── Product JSON-LD 结构化数据（SEO 核心） ──
const siteOrigin = computed(() => {
  if (typeof window !== 'undefined') return window.location.origin;
  return '';
});

const productJsonLd = computed(() => {
  const p = product.value;
  if (!p) return null;
  const origin = siteOrigin.value;
  const schema: Record<string, unknown> = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: p.name,
    description: p.summary || p.description || p.name,
    url: `${origin}/tenant/products/${p.slug}`,
    brand: {
      '@type': 'Brand',
      name: tenant.value?.name || '',
    },
    manufacturer: {
      '@type': 'Organization',
      name: tenant.value?.name || '',
    },
  };
  if (p.image) {
    schema.image = resolveMediaUrl(p.image);
  }
  // 规格参数 → additionalProperty
  if (p.specs?.length) {
    schema.additionalProperty = p.specs.map((s: { label: string; value: string }) => ({
      '@type': 'PropertyValue',
      name: s.label,
      value: s.value,
    }));
  }
  return schema;
});

// ── VideoObject JSON-LD（如果产品有视频） ──
const videoJsonLd = computed(() => {
  const p = product.value;
  if (!p || !(p as any).videoUrl) return null;
  return {
    '@context': 'https://schema.org',
    '@type': 'VideoObject',
    name: `${p.name} - Product Video`,
    description: p.summary || p.description || p.name,
    thumbnailUrl: p.image ? resolveMediaUrl(p.image) : '',
    uploadDate: (p as any).videoUpdatedAt || new Date().toISOString(),
    contentUrl: resolveMediaUrl((p as any).videoUrl),
    embedUrl: resolveMediaUrl((p as any).videoUrl),
  };
});

// 注入 JSON-LD 到页面 head
useHead(() => {
  const scripts: Array<{ type: string; key: string; innerHTML: string }> = [];
  if (productJsonLd.value) {
    scripts.push({
      type: 'application/ld+json',
      key: 'product-jsonld',
      innerHTML: JSON.stringify(productJsonLd.value),
    });
  }
  if (videoJsonLd.value) {
    scripts.push({
      type: 'application/ld+json',
      key: 'video-jsonld',
      innerHTML: JSON.stringify(videoJsonLd.value),
    });
  }
  return { script: scripts };
});

function inquiryAttribution() {
  return {
    landing_path: typeof window !== 'undefined' ? window.location.pathname : '/tenant/products',
    last_click_label: 'lpro_product_detail',
    tenant_id: tenant.value?.id,
  };
}
</script>
