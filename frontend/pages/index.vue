<template>
  <div class="b2b-home pt-14 sm:pt-16 lg:pt-20">
    <!-- hztyco / tingertech：顶栏联系 -->
    <div class="b2b-topbar">
      <div class="b2b-container b2b-topbar-inner">
        <a :href="'tel:' + SITE_CONFIG.phone">{{ $t('common.phone') }}：{{ SITE_CONFIG.phone }}</a>
        <a :href="'mailto:' + SITE_CONFIG.email">{{ $t('common.email') }}：{{ SITE_CONFIG.email }}</a>
      </div>
    </div>

    <!-- luyang / cattuong：左右分栏 Hero -->
    <section class="b2b-hero">
      <div class="b2b-container b2b-hero-grid">
        <div>
          <p class="b2b-hero-eyebrow">{{ $t('home.heroSince', { year: '2006' }) }}</p>
          <h1 class="b2b-hero-title">
            {{ $t('home.heroHeading1') }}
            <br />
            <span style="color: var(--b2b-primary)">{{ $t('home.heroHeading2') }}</span>
          </h1>
          <p class="b2b-hero-desc">{{ $t('home.heroDesc') }}</p>
          <div class="b2b-trust-badges">
            <span v-for="badge in trustBadges" :key="badge" class="b2b-trust-badge">{{ badge }}</span>
          </div>
          <div class="b2b-hero-actions">
            <NuxtLink to="/products" class="b2b-btn b2b-btn-primary">{{ $t('hero.cta_products') }}</NuxtLink>
            <NuxtLink to="/contact" class="b2b-btn b2b-btn-outline">{{ $t('hero.cta_contact') }}</NuxtLink>
          </div>
          <p class="b2b-inquiry-hook">{{ $t('home.inquiryHook') }}</p>
        </div>
        <div class="b2b-hero-media">
          <div class="b2b-hero-placeholder">
            <svg viewBox="0 0 200 120" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
              <rect x="8" y="52" width="48" height="56" rx="4" stroke="currentColor" stroke-width="2" />
              <rect x="72" y="28" width="56" height="80" rx="4" stroke="currentColor" stroke-width="2" />
              <rect x="144" y="44" width="48" height="64" rx="4" stroke="currentColor" stroke-width="2" />
            </svg>
            <span class="b2b-hero-placeholder-name">{{ $t('common.companyName') }}</span>
            <span class="text-sm text-slate-500 mt-1">{{ $t('home.heroBadge') }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- rsref / luyang / cnabm：深色大数字条 -->
    <section class="b2b-stats">
      <div class="b2b-container">
        <p class="b2b-stats-eyebrow">{{ $t('home.statsEyebrow') }}</p>
        <h2 class="b2b-stats-title">{{ $t('home.statsHeadline') }}</h2>
        <div class="b2b-stats-grid">
          <div v-for="(stat, i) in stats" :key="i" class="b2b-stat-item">
            <div class="b2b-stat-value">{{ stat.value }}</div>
            <div class="b2b-stat-label">{{ stat.label }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- cnabm / shenzhou / rockwool：全领域解决方案 -->
    <section class="b2b-section bg-b2b-muted">
      <div class="b2b-container">
        <h2 class="b2b-section-title">{{ $t('home.solutionsTitle') }}</h2>
        <p class="b2b-section-desc">{{ $t('home.solutionsDesc') }}</p>
        <div class="b2b-solution-grid">
          <article v-for="sol in solutions" :key="sol.segment" class="b2b-solution-card">
            <div class="b2b-solution-segment">{{ sol.segment }}</div>
            <h3>{{ sol.title }}</h3>
            <p>{{ sol.description }}</p>
          </article>
        </div>
      </div>
    </section>

    <!-- hztyco：产品分类 -->
    <section class="b2b-section bg-white">
      <div class="b2b-container">
        <h2 class="b2b-section-title">{{ $t('home.productTitle') }}</h2>
        <p class="b2b-section-desc">{{ $t('home.productDesc') }}</p>
        <div class="b2b-card-grid">
          <article v-for="cat in categories" :key="cat.id" class="b2b-card">
            <div class="b2b-product-thumb">
              <component :is="cat.icon" class="w-10 h-10" />
            </div>
            <h3>{{ cat.name }}</h3>
            <p>{{ cat.desc }}</p>
            <NuxtLink :to="'/products?category=' + cat.id" class="b2b-link">{{ $t('common.learnMore') }} →</NuxtLink>
          </article>
        </div>
      </div>
    </section>

    <!-- tingertech：热销产品列表 -->
    <section class="b2b-section bg-b2b-muted">
      <div class="b2b-container">
        <h2 class="b2b-section-title">{{ $t('home.hotProductsTitle') }}</h2>
        <p class="b2b-section-desc">{{ $t('home.hotProductsDesc') }}</p>
        <div class="b2b-card-grid">
          <article v-for="(item, i) in hotProducts" :key="i" class="b2b-card">
            <div class="b2b-product-thumb">
              <component :is="item.icon" class="w-10 h-10" />
            </div>
            <h3>{{ item.name }}</h3>
            <p>{{ item.summary }}</p>
            <NuxtLink to="/contact" class="b2b-link">{{ $t('home.inquiryLink') }} →</NuxtLink>
          </article>
        </div>
      </div>
    </section>

    <!-- rockwool：应用场景 -->
    <section class="b2b-section bg-white">
      <div class="b2b-container">
        <h2 class="b2b-section-title">{{ $t('home.applicationsTitle') }}</h2>
        <p class="b2b-section-desc">{{ $t('home.applicationsDesc') }}</p>
        <div class="b2b-card-grid">
          <article v-for="(app, i) in applications" :key="i" class="b2b-card">
            <h3>{{ app.name }}</h3>
            <p>{{ app.desc }}</p>
          </article>
        </div>
      </div>
    </section>

    <!-- hztyco：四大优势 -->
    <section class="b2b-section bg-b2b-muted">
      <div class="b2b-container">
        <h2 class="b2b-section-title">{{ $t('home.whyUsTitle') }}</h2>
        <p class="b2b-section-desc">{{ $t('home.whyUsDesc') }}</p>
        <div class="b2b-adv-grid">
          <article v-for="(adv, i) in advantages" :key="i" class="b2b-adv-card">
            <div class="b2b-adv-icon">{{ i + 1 }}</div>
            <h3>{{ adv.title }}</h3>
            <p>{{ adv.desc }}</p>
          </article>
        </div>
      </div>
    </section>

    <!-- cattuong：Mission / Vision -->
    <section class="b2b-section bg-white">
      <div class="b2b-container">
        <h2 class="b2b-section-title">{{ $t('nav.about') }}</h2>
        <div class="b2b-mv-grid">
          <article class="b2b-mv-card">
            <h3 class="b2b-mv-heading">{{ $t('home.missionTitle') }}</h3>
            <p class="b2b-mv-text">{{ $t('home.missionText') }}</p>
          </article>
          <article class="b2b-mv-card">
            <h3 class="b2b-mv-heading">{{ $t('home.visionTitle') }}</h3>
            <p class="b2b-mv-text">{{ $t('home.visionText') }}</p>
          </article>
        </div>
      </div>
    </section>

    <!-- 询盘 CTA -->
    <section class="b2b-section bg-b2b-muted">
      <div class="b2b-container">
        <div class="b2b-cta-band">
          <h2 class="text-xl sm:text-2xl font-bold mb-3">{{ $t('home.ctaConsultTitle') }}</h2>
          <p class="text-sm sm:text-base text-white/85 mb-6 max-w-2xl mx-auto">{{ $t('home.ctaConsultDesc') }}</p>
          <div class="flex flex-col sm:flex-row flex-wrap justify-center gap-3">
            <a :href="'tel:' + SITE_CONFIG.phone" class="b2b-btn bg-white text-[var(--b2b-primary)] hover:bg-gray-50">
              {{ $t('home.ctaPhone') }}
            </a>
            <NuxtLink to="/contact" class="b2b-btn b2b-btn-outline border-white text-white hover:bg-white/10">
              {{ $t('home.ctaMessage') }}
            </NuxtLink>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
/**
 * 优丁建材 B2B 企业官网 — site id: corporate-b2b
 * 勿混入 SaaS 营销或 TenantSite 模板 · 见 frontend/config/public-sites.ts
 */
definePageMeta({ layout: 'default' });

import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { SITE_CONFIG } from '~/config/site';
import FactoryIcon from '~/components/icons/FactoryIcon.vue';
import DropletsIcon from '~/components/icons/DropletsIcon.vue';
import ThermometerIcon from '~/components/icons/ThermometerIcon.vue';
import ShieldIcon from '~/components/icons/ShieldIcon.vue';
import AwardIcon from '~/components/icons/AwardIcon.vue';

const { t } = useI18n();

useHead({
  title: `${t('common.companyName')} - ${t('home.heroBadge')}`,
  meta: [
    { name: 'description', content: t('home.heroDesc') },
    { property: 'og:title', content: `${t('common.companyName')} - ${t('home.heroBadge')}` },
    { property: 'og:description', content: t('home.heroDesc') },
    { property: 'og:type', content: 'website' },
    { property: 'og:url', content: SITE_CONFIG.url },
  ],
  link: [{ rel: 'canonical', href: SITE_CONFIG.url }],
});

const trustBadges = computed(() => [
  t('home.trustIso'),
  t('home.trustFactory'),
  t('home.trustExport'),
  t('home.trustCustom'),
]);

const stats = computed(() => [
  { value: '20+', label: t('home.stats.experience') },
  { value: '500+', label: t('home.stats.customers') },
  { value: '100+', label: t('home.stats.models') },
  { value: '30+', label: t('home.stats.patents') },
]);

const solutions = computed(() => [
  { segment: 'Building', title: t('home.solutionBuilding'), description: t('home.solutionBuildingDesc') },
  { segment: 'Municipal', title: t('home.solutionMunicipal'), description: t('home.solutionMunicipalDesc') },
  { segment: 'Industrial', title: t('home.solutionIndustrial'), description: t('home.solutionIndustrialDesc') },
  { segment: 'Landscape', title: t('home.solutionLandscape'), description: t('home.solutionLandscapeDesc') },
]);

const categories = computed(() => [
  { id: '1', name: t('home.categories.lightweight.name'), desc: t('home.categories.lightweight.desc'), icon: FactoryIcon },
  { id: '2', name: t('home.categories.ceramsite.name'), desc: t('home.categories.ceramsite.desc'), icon: DropletsIcon },
  { id: '3', name: t('home.categories.insulation.name'), desc: t('home.categories.insulation.desc'), icon: ThermometerIcon },
]);

const hotProducts = computed(() => [
  { name: t('home.categories.lightweight.name'), summary: t('home.categories.lightweight.desc'), icon: FactoryIcon },
  { name: t('home.categories.ceramsite.name'), summary: t('home.categories.ceramsite.desc'), icon: DropletsIcon },
  { name: t('home.categories.insulation.name'), summary: t('home.categories.insulation.desc'), icon: ThermometerIcon },
]);

const advantages = computed(() => [
  { title: t('home.features.production.title'), desc: t('home.features.production.desc') },
  { title: t('home.features.quality.title'), desc: t('home.features.quality.desc') },
  { title: t('home.features.rd.title'), desc: t('home.features.rd.desc') },
  { title: t('home.feature4Title'), desc: t('home.feature4Desc') },
]);

const applications = computed(() => [
  { name: t('home.applications.residential'), desc: t('home.applications.residential') },
  { name: t('home.applications.commercial'), desc: t('home.applications.commercial') },
  { name: t('home.applications.bridges'), desc: t('home.applications.bridges') },
  { name: t('home.applications.roads'), desc: t('home.applications.roads') },
  { name: t('home.applications.industrial'), desc: t('home.applications.industrial') },
  { name: t('home.applications.landscape'), desc: t('home.applications.landscape') },
  { name: t('home.applications.water'), desc: t('home.applications.water') },
  { name: t('home.applications.underground'), desc: t('home.applications.underground') },
]);
</script>
