/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <TenantLProProductDetail v-if="lProMode" />
  <TenantSite
    v-else
    visual-page="products"
  />
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router';
import TenantLProProductDetail from '../../../components/tenant/premium/TenantLProProductDetail.vue';
import { useTenantSiteBootstrap } from '../../../composables/useTenantSiteBootstrap';
import { useTenantSEO } from '../../../composables/useTenantSEO';

definePageMeta({ layout: 'tenant-blank' });

const route = useRoute();
const slug = String(route.params.slug || '');
const { lProMode, ensureLoaded, tenant } = useTenantSiteBootstrap();
await ensureLoaded();

// 注入租户专属千人千面 SEO 与 Schema.org 结构化数据
useTenantSEO({
  tenantName: tenant.value?.company_name || tenant.value?.name || '优丁建材',
  tenantFullName: tenant.value?.company_name || '优丁新型建材科技有限公司',
  tenantDomain: tenant.value?.domain ? `https://${tenant.value.domain}` : undefined,
  product: {
    name: slug.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
    slug,
    subtitle: 'High-Performance Industrial Grade Material',
    description: 'Certified architectural lightweight and thermal insulation product manufactured under ISO/CE standards.',
  },
});
</script>
