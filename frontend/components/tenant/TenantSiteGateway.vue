/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <TenantSite v-if="!lProMode" :visual-page="legacyPage" />
  <component v-else :is="lProComponent" />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useTenantSiteBootstrap } from '../../composables/useTenantSiteBootstrap';
import TenantLProHome from './premium/TenantLProHome.vue';
import TenantLProProducts from './premium/TenantLProProducts.vue';
import TenantLProAbout from './premium/TenantLProAbout.vue';
import TenantLProContact from './premium/TenantLProContact.vue';
import TenantLProSolutions from './premium/TenantLProSolutions.vue';
import TenantLProDownloads from './premium/TenantLProDownloads.vue';

const props = defineProps<{
  page: 'home' | 'products' | 'about' | 'contact' | 'solutions' | 'downloads';
}>();

const { lProMode, ensureLoaded } = useTenantSiteBootstrap();
await ensureLoaded();

const legacyPage = computed(() => {
  if (props.page === 'solutions' || props.page === 'downloads') return 'home';
  return props.page;
});

const lProComponent = computed(() => {
  switch (props.page) {
    case 'products':
      return TenantLProProducts;
    case 'about':
      return TenantLProAbout;
    case 'contact':
      return TenantLProContact;
    case 'solutions':
      return TenantLProSolutions;
    case 'downloads':
      return TenantLProDownloads;
    default:
      return TenantLProHome;
  }
});
</script>
