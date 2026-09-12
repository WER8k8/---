<template>
  <TenantLProProductDetail v-if="lProMode" />
  <TenantSite v-else visual-page="products" />
</template>

<script setup lang="ts">
import TenantLProProductDetail from '../../../components/tenant/premium/TenantLProProductDetail.vue';
import { useTenantSiteBootstrap } from '../../../composables/useTenantSiteBootstrap';

definePageMeta({ layout: 'tenant-blank' });

const { lProMode, ensureLoaded } = useTenantSiteBootstrap();
await ensureLoaded();
</script>
