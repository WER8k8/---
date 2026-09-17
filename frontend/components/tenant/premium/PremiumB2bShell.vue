/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div
    class="lpro-root min-h-screen flex flex-col"
    :style="{ '--tenant-primary': themePrimary, '--lpro-primary': themePrimary }"
  >
    <div v-if="loading" class="lpro-loading">
      <p>{{ tSite('loading') }}</p>
    </div>
    <div v-else-if="error" class="lpro-error">
      <h1>{{ tSite('site_unavailable') }}</h1>
      <p>{{ error }}</p>
    </div>
    <template v-else-if="tenant">
      <div class="lpro-topbar">
        <div class="lpro-container lpro-topbar-inner">
          <span v-if="establishedYear">{{ tSite('hero_since', { year: establishedYear }) }}</span>
          <div class="flex flex-wrap gap-3">
            <a
              v-for="ch in topbarChannels"
              :key="`${ch.channel_type}-${ch.value}`"
              :href="topbarContactHref(ch)"
              :target="isExternalContactChannel(ch) ? '_blank' : undefined"
              :rel="isExternalContactChannel(ch) ? 'noopener noreferrer' : undefined"
            >
              {{ ch.label }}: {{ ch.value }}
            </a>
          </div>
        </div>
      </div>

      <header class="lpro-header">
        <div class="lpro-container lpro-header-inner">
          <NuxtLink to="/tenant" class="lpro-brand">
            <img v-if="tenant.brand.logo_url" :src="tenant.brand.logo_url" :alt="companyName" />
            <div>
              <div class="lpro-brand-title">{{ companyName }}</div>
              <div v-if="brandTagline" class="lpro-brand-tag">{{ brandTagline }}</div>
            </div>
          </NuxtLink>
          <nav class="lpro-nav" aria-label="Main">
            <NuxtLink
              v-for="item in navItems"
              :key="item.key"
              :to="item.href"
              :class="{ 'is-active': activeKey === item.key }"
            >
              {{ item.label }}
            </NuxtLink>
          </nav>
          <div class="lpro-header-actions">
            <div class="lpro-header-lang lpro-header-lang--desktop">
              <LProLanguagePicker
                v-if="tenant.domain"
                :domain="tenant.domain"
                :current-language="language"
                :t-site="tSite"
                :tier1-options="supportedLanguages"
                :on-language-change="onLanguageChange"
              />
            </div>
            <NuxtLink to="/tenant/contact" class="lpro-header-cta">{{ ctaPrimary }}</NuxtLink>
          </div>
          <button type="button" class="lpro-menu-btn md:hidden" :aria-expanded="menuOpen" @click="menuOpen = !menuOpen">
            ☰
          </button>
        </div>
        <div v-if="menuOpen" class="lpro-container lpro-mobile-nav md:hidden">
          <LProLanguagePicker
            v-if="tenant.domain"
            class="lpro-mobile-lang"
            :domain="tenant.domain"
            :current-language="language"
            :t-site="tSite"
            :tier1-options="supportedLanguages"
            :on-language-change="onLanguageChange"
          />
          <NuxtLink
            v-for="item in navItems"
            :key="item.key"
            :to="item.href"
            :class="{ 'is-active': activeKey === item.key }"
            @click="menuOpen = false"
          >
            {{ item.label }}
          </NuxtLink>
        </div>
      </header>

      <main class="lpro-main">
        <slot />
      </main>

      <footer class="lpro-footer">
        <div class="lpro-container lpro-footer-grid">
          <div>
            <div class="font-bold text-lg mb-1">{{ companyName }}</div>
            <p class="text-white/70 text-sm">{{ brandTagline }}</p>
          </div>
          <div>
            <div class="font-semibold mb-2">{{ tSite('footer_quick_links') }}</div>
            <NuxtLink v-for="item in navItems" :key="item.key" :to="item.href">{{ item.label }}</NuxtLink>
          </div>
          <div>
            <div class="font-semibold mb-2">{{ tSite('footer_contact') }}</div>
            <a
              v-for="ch in contactDisplayChannels"
              :key="`footer-${ch.channel_type}-${ch.value}`"
              :href="topbarContactHref(ch)"
            >
              {{ ch.label }}: {{ ch.value }}
            </a>
          </div>
        </div>
        <div class="lpro-container lpro-footer-copy">{{ footerText }}</div>
      </footer>

      <TenantSiteCompanion
        :company-name="companyName"
        :phone="contactPhone"
        :email="contactEmail"
        :whatsapp="contactWhatsapp"
        :wechat="contactWechat"
        :qq="contactQq"
        :accent="themePrimary"
        :product-hint="productHint"
        :tenant-domain="tenant.domain"
        :api-base="apiBase"
        :visitor-language="language"
        :visitor-country="countryCode"
        :cn-compliant-only="cnCompliantOnly"
        :wangcai-ui="wangcaiUi"
        :contact-channels="effectiveChannels"
        :trade-qa-enabled="tradeQaEnabled"
        :is-rtl="language === 'ar'"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, toRef, watch } from 'vue';
import LProLanguagePicker from './LProLanguagePicker.vue';
import { buildTenantLProNavItems, type TenantLProNavKey } from '../../../composables/useTenantLProNav';
import { useTenantSiteBootstrap } from '../../../composables/useTenantSiteBootstrap';
import {
  isExternalContactChannel,
  topbarContactHref,
  useTenantVisitorContacts,
} from '../../../composables/useTenantVisitorContacts';
import { localizedSiteString } from '../../../utils/tenant-site-i18n';
import { useTenantLProSeoHead } from '../../../composables/useTenantLProSeoHead';
import { useTenantGeoJsonLd } from '../../../composables/useTenantGeoJsonLd';
import { writeStoredTenantLanguage, TIER1_LANGUAGES } from '../../../composables/useTenantLanguagePicker';

import './premium-b2b-v1.css';

const props = defineProps<{
  activeKey: TenantLProNavKey;
  /** 产品详情等子页覆盖标签标题（不含公司名后缀） */
  documentTitle?: string;
  documentDescription?: string;
}>();

const menuOpen = ref(false);
const bootstrap = useTenantSiteBootstrap();
const {
  tenant,
  loading,
  error,
  homePage,
  contactPage,
  catalogProducts,
  localizedCatalogProducts,
  tSite,
  language,
  countryCode,
  contactChannels,
  cnCompliantOnly,
  tradeQaEnabled,
  wangcaiUi,
  context: visitorContext,
  siteContent,
  apiBase,
  fetchVisitorContext,
  prefetchLanguages,
  supportedLanguages,
} = bootstrap;

const overlay = computed(() => visitorContext.value?.site_content_localized || null);

const companyName = computed(() =>
  localizedSiteString(
    siteContent.value,
    overlay.value?.brand,
    'brand',
    'name',
    language.value,
    [
      (siteContent.value?.brand as { name?: string })?.name,
      tenant.value?.brand.company_name,
      tenant.value?.name,
    ].filter((x): x is string => typeof x === 'string'),
  ) || 'Company',
);
const brandTagline = computed(() =>
  localizedSiteString(
    siteContent.value,
    overlay.value?.brand,
    'brand',
    'tagline',
    language.value,
    [
      (siteContent.value?.brand as { tagline?: string })?.tagline,
      tenant.value?.brand.slogan,
    ].filter((x): x is string => typeof x === 'string'),
  ),
);
const themePrimary = computed(() =>
  (siteContent.value?.theme as { headerBg?: string })?.headerBg
  || tenant.value?.brand.brand_colors?.primary
  || '#0f2942',
);
const establishedYear = computed(() => String(homePage.value.establishedYear || ''));
const ctaPrimary = computed(() =>
  String(overlay.value?.home?.ctaPrimary || homePage.value.ctaPrimary || tSite('cta_primary')),
);
const contactPhone = computed(() =>
  String(contactPage.value.phone || tenant.value?.brand.contact_phone || ''),
);
const contactEmail = computed(() =>
  String(contactPage.value.email || tenant.value?.brand.contact_email || ''),
);
const contactWhatsapp = computed(() => String(contactPage.value.whatsapp || ''));
const contactWechat = computed(() => String(contactPage.value.wechat || ''));
const contactQq = computed(() => String(contactPage.value.qq || ''));
const productHint = computed(() => localizedCatalogProducts.value[0]?.name || '');

const solutionsCount = computed(() => {
  const overlay = visitorContext.value?.site_content_localized?.home;
  const raw = overlay?.solutions ?? homePage.value.solutions;
  return Array.isArray(raw) ? raw.length : 0;
});
const downloadsCount = computed(() => {
  const raw = bootstrap.downloadsPage.value.items;
  return Array.isArray(raw) ? raw.length : 0;
});

const navItems = computed(() =>
  buildTenantLProNavItems(tSite, {
    hasSolutions: solutionsCount.value > 0,
    hasDownloads: downloadsCount.value > 0,
  }),
);

const {
  effectiveChannels,
  topbarChannels,
  contactDisplayChannels,
} = useTenantVisitorContacts({
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

const footerText = computed(() => {
  const custom = (siteContent.value?.footer as { text?: string })?.text || tenant.value?.brand.footer_text;
  if (custom) return custom;
  return tSite('footer_copyright', {
    year: String(new Date().getFullYear()),
    name: companyName.value,
  });
});

const localizedHeroTitle = computed(() =>
  localizedSiteString(
    siteContent.value,
    overlay.value?.home,
    'home',
    'title',
    language.value,
    [
      String(homePage.value.title || ''),
      tenant.value?.brand.site_title,
      companyName.value,
    ].filter((x): x is string => typeof x === 'string' && x.trim().length > 0),
  ),
);

const seoBaseTitle = computed(() => localizedHeroTitle.value || companyName.value);

const localizedHeroDescription = computed(() =>
  localizedSiteString(
    siteContent.value,
    overlay.value?.home,
    'home',
    'description',
    language.value,
    [String(homePage.value.description || '')].filter(
      (x): x is string => typeof x === 'string' && x.trim().length > 0,
    ),
  ),
);

const localizedSeoDescription = computed(() =>
  localizedSiteString(
    siteContent.value,
    overlay.value?.home,
    'home',
    'seoDescription',
    language.value,
    [
      String(homePage.value.seoDescription || ''),
      localizedHeroDescription.value,
      String(homePage.value.description || ''),
    ].filter((x): x is string => typeof x === 'string' && x.trim().length > 0),
  ),
);

const localizedSeoKeywords = computed(() =>
  localizedSiteString(
    siteContent.value,
    overlay.value?.home,
    'home',
    'seoKeywords',
    language.value,
    [String(homePage.value.seoKeywords || '')].filter(
      (x): x is string => typeof x === 'string' && x.trim().length > 0,
    ),
  ),
);

const seoRobotsContent = computed(() =>
  homePage.value.robotsNoIndex === true ? 'noindex,nofollow' : 'index,follow',
);

const route = useRoute();
const router = useRouter();

const { siteOrigin, seoPageDescription } = useTenantLProSeoHead({
  activeKey: toRef(props, 'activeKey'),
  language,
  companyName,
  seoBaseTitle,
  localizedSeoDescription,
  localizedSeoKeywords,
  seoRobotsContent,
  siteContent,
  documentTitle: props.documentTitle,
  documentDescription: props.documentDescription,
  tSite,
});

useTenantGeoJsonLd({
  companyName,
  description: seoPageDescription,
  siteOrigin,
  contactEmail: computed(() => contactEmail.value),
  contactPhone: computed(() => contactPhone.value),
  products: localizedCatalogProducts,
});

watch(
  () => tenant.value?.domain,
  (domain) => {
    if (!domain || import.meta.dev) return;
    prefetchLanguages(TIER1_LANGUAGES.map((item) => item.code));
  },
  { immediate: true },
);

async function onLanguageChange(code: string) {
  if (!tenant.value?.domain) return;
  writeStoredTenantLanguage(tenant.value.domain, code);
  void router.replace({
    query: { ...route.query, language: code },
  });
  void fetchVisitorContext({ language: code }, tenant.value.domain, {
    background: true,
    cancelInflight: true,
  });
}

defineExpose({ bootstrap });
</script>
