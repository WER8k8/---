/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <TenantSite
    v-if="!lProMode"
    :visual-page="legacyPage"
  />
  <TenantLProCarrier
    v-else-if="isCarrier"
    :page="carrierPage"
  />
  <component
    v-else
    :is="lProComponent"
  />
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
import TenantLProCarrier from './premium/TenantLProCarrier.vue';

const props = defineProps<{
  page: 'home' | 'products' | 'about' | 'contact' | 'solutions' | 'downloads'
    | 'test-reports' | 'parameters' | 'certifications' | 'supplier-onboarding' | 'brand-guide' | 'faq';
}>();

const { lProMode, ensureLoaded } = useTenantSiteBootstrap();
await ensureLoaded();

const CARRIER_PAGES = [
  'test-reports',
  'parameters',
  'certifications',
  'supplier-onboarding',
  'brand-guide',
  'faq',
] as const;

const isCarrier = computed(() => (CARRIER_PAGES as readonly string[]).includes(props.page));

const carrierPage = computed(
  () =>
    props.page as
      | 'test-reports'
      | 'parameters'
      | 'certifications'
      | 'supplier-onboarding'
      | 'brand-guide'
      | 'faq',
);

const legacyPage = computed(() => {
  const legacyValid = ['home', 'contact', 'about', 'products'] as const;
  if ((legacyValid as readonly string[]).includes(props.page)) {
    return props.page as (typeof legacyValid)[number];
  }
  return 'home';
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
