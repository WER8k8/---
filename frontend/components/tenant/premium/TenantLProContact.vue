/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <PremiumB2bShell active-key="contact">
    <section class="lpro-hero">
      <div class="lpro-container">
        <h1>{{ tSite('section_contact') }}</h1>
        <p>{{ tSite('form_hint') }}</p>
      </div>
    </section>
    <section class="lpro-section lpro-section--white">
      <div class="lpro-container lpro-detail-layout">
        <div>
          <h2 class="lpro-section-title">
            {{ tSite('footer_contact') }}
          </h2>
          <div class="space-y-3">
            <a
              v-for="ch in contactDisplayChannels"
              :key="`${ch.channel_type}-${ch.value}`"
              :href="topbarContactHref(ch)"
              class="block lpro-card"
            >
              <strong>{{ ch.label }}</strong>
              <span class="block text-[var(--lpro-muted)]">{{ ch.value }}</span>
            </a>
            <div
              v-if="factoryAddress"
              class="lpro-card"
            >
              <strong>{{ tSite('factory_label') }}</strong>
              <span class="block text-[var(--lpro-muted)]">{{ factoryAddress }}</span>
            </div>
          </div>
        </div>
        <div>
          <TenantInquiryForm
            :tenant-id="tenant?.id"
            :tenant-domain="tenant?.domain"
            :api-base="apiBase"
            :cn-compliant-only="cnCompliantOnly"
            :t-site="tSite"
            :attribution="inquiryAttribution"
          />
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
import {
  topbarContactHref,
  useTenantVisitorContacts,
} from '../../../composables/useTenantVisitorContacts';

const {
  tenant,
  contactPage,
  homePage,
  tSite,
  cnCompliantOnly,
  contactChannels,
  language,
  apiBase,
} = useTenantSiteBootstrap();

const contactPhone = computed(() =>
  String(contactPage.value.phone || tenant.value?.brand.contact_phone || ''),
);
const contactEmail = computed(() =>
  String(contactPage.value.email || tenant.value?.brand.contact_email || ''),
);
const contactWhatsapp = computed(() => String(contactPage.value.whatsapp || ''));
const contactWechat = computed(() => String(contactPage.value.wechat || ''));
const contactQq = computed(() => String(contactPage.value.qq || ''));
const factoryAddress = computed(() =>
  String(contactPage.value.factoryAddress || contactPage.value.address || ''),
);
const ctaPrimary = computed(() =>
  String(homePage.value.ctaPrimary || tSite('cta_primary')),
);

const { contactDisplayChannels } = useTenantVisitorContacts({
  contactChannels: () => contactChannels.value,
  cnCompliantOnly: () => cnCompliantOnly.value,
  language: () => language.value,
  rawContacts: () => ({
    phone: contactPhone.value,
    email: contactEmail.value,
    whatsapp: contactWhatsapp.value,
    wechat: contactWechat.value,
    qq: contactQq.value,
  }),
  quoteLabel: () => ctaPrimary.value,
});

function inquiryAttribution() {
  return {
    landing_path: typeof window !== 'undefined' ? window.location.pathname : '/tenant/contact',
    last_click_label: 'lpro_contact',
    tenant_id: tenant.value?.id,
  };
}
</script>
