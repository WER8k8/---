/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>

  <PremiumB2bShell active-key="home">

    <section class="lpro-hero">

      <div class="lpro-container">

        <p v-if="primaryPromise" class="text-sm font-semibold tracking-wide mb-2 lpro-hero-kicker">

          {{ primaryPromise }}

        </p>

        <p v-else-if="establishedYear" class="text-sm uppercase tracking-wide opacity-80 mb-2">

          {{ tSite('hero_since', { year: establishedYear }) }}

        </p>

        <h1>{{ heroTitle }}</h1>

        <p>{{ heroDescription }}</p>

        <div class="lpro-hero-actions">

          <NuxtLink to="/tenant/contact" class="lpro-btn lpro-btn-primary">{{ ctaPrimary }}</NuxtLink>

          <NuxtLink to="/tenant/products" class="lpro-btn lpro-btn-outline">{{ tSite('nav_products') }}</NuxtLink>

        </div>

      </div>

    </section>



    <section v-if="stats.length" class="lpro-section lpro-section--white">

      <div class="lpro-container">

        <p class="lpro-section-eyebrow">{{ tSite('stats_eyebrow') }}</p>

        <h2 class="lpro-section-title">{{ tSite('stats_title') }}</h2>

        <div class="lpro-grid">

          <div v-for="(stat, i) in stats" :key="i" class="lpro-card">

            <div class="text-2xl font-bold" style="color: var(--lpro-primary)">{{ stat.value }}</div>

            <p>{{ stat.label }}</p>

          </div>

        </div>

      </div>

    </section>



    <section v-if="serviceStages.length" class="lpro-section">

      <div class="lpro-container">

        <p class="lpro-section-eyebrow">{{ tSite('section_stages_eyebrow') }}</p>

        <h2 class="lpro-section-title">{{ tSite('section_stages_title') }}</h2>

        <p class="lpro-section-desc">{{ tSite('section_stages_desc') }}</p>

        <div class="lpro-stages">

          <article v-for="(stage, i) in serviceStages" :key="i" class="lpro-stage-card">

            <div class="lpro-stage-num">{{ stage.stage || String(i + 1).padStart(2, '0') }}</div>

            <h3>{{ stage.title }}</h3>

            <p v-if="stage.description">{{ stage.description }}</p>

          </article>

        </div>

      </div>

    </section>



    <section v-if="solutions.length" class="lpro-section lpro-section--white">

      <div class="lpro-container">

        <h2 class="lpro-section-title">{{ tSite('section_solutions') }}</h2>

        <p class="lpro-section-desc">{{ tSite('section_solutions_desc') }}</p>

        <div class="lpro-grid">

          <article v-for="(sol, i) in solutions.slice(0, 4)" :key="i" class="lpro-card">

            <div class="text-xs font-semibold uppercase text-[var(--lpro-muted)]">{{ sol.segment }}</div>

            <h3>{{ sol.title }}</h3>

            <p v-if="sol.description">{{ sol.description }}</p>

          </article>

        </div>

        <NuxtLink v-if="solutions.length > 4" to="/tenant/solutions" class="lpro-link mt-4 inline-block">

          {{ tSite('nav_solutions') }} →

        </NuxtLink>

      </div>

    </section>



    <section v-if="advantages.length" class="lpro-section">

      <div class="lpro-container">

        <h2 class="lpro-section-title">{{ sectionTitle }}</h2>

        <p v-if="sectionDesc" class="lpro-section-desc">{{ sectionDesc }}</p>

        <div class="lpro-grid">

          <article v-for="(adv, i) in advantages" :key="i" class="lpro-card">

            <h3>{{ adv.title }}</h3>

            <p>{{ adv.description }}</p>

          </article>

        </div>

      </div>

    </section>



    <section v-if="featuredProducts.length" class="lpro-section lpro-section--white">

      <div class="lpro-container">

        <h2 class="lpro-section-title">{{ productsTitle }}</h2>

        <p class="lpro-section-desc">{{ productsDescription || tSite('section_products_desc') }}</p>

        <div class="lpro-grid">

          <article v-for="item in featuredProducts" :key="item.slug" class="lpro-card">

            <div class="lpro-thumb">

              <img v-if="item.image" :src="resolveMediaUrl(item.image)" :alt="item.name" />

            </div>

            <h3>{{ item.name }}</h3>

            <p>{{ item.summary }}</p>

            <NuxtLink :to="tenantProductDetailPath(item.slug!)" class="lpro-link">

              {{ tSite('inquiry_link') }}

            </NuxtLink>

          </article>

        </div>

        <div class="mt-6">

          <NuxtLink to="/tenant/products" class="lpro-btn lpro-btn-primary">{{ tSite('nav_products') }}</NuxtLink>

        </div>

      </div>

    </section>



    <section v-if="knowledgeTopics.length" class="lpro-section">

      <div class="lpro-container">

        <p class="lpro-section-eyebrow">{{ tSite('section_knowledge_eyebrow') }}</p>

        <h2 class="lpro-section-title">{{ tSite('section_knowledge_title') }}</h2>

        <p class="lpro-section-desc">{{ tSite('section_knowledge_desc') }}</p>

        <div class="lpro-grid">

          <article v-for="(topic, i) in knowledgeTopics.slice(0, 6)" :key="i" class="lpro-card lpro-knowledge-card">

            <h3>{{ topic.title }}</h3>

            <p v-if="topic.hook">{{ topic.hook }}</p>

            <NuxtLink to="/tenant/contact" class="lpro-link">{{ tSite('inquiry_link') }}</NuxtLink>

          </article>

        </div>

      </div>

    </section>



    <section class="lpro-section lpro-cta-band">

      <div class="lpro-container lpro-cta-band-inner">

        <h2>{{ tSite('section_cta_title') }}</h2>

        <p>{{ inquiryHook }}</p>

        <NuxtLink to="/tenant/contact" class="lpro-btn lpro-btn-primary">{{ ctaPrimary }}</NuxtLink>

      </div>

    </section>

  </PremiumB2bShell>

</template>



<script setup lang="ts">

import { computed } from 'vue';

import PremiumB2bShell from './PremiumB2bShell.vue';

import { useTenantSiteBootstrap } from '../../../composables/useTenantSiteBootstrap';

import { tenantProductDetailPath } from '../../../composables/useTenantLProNav';

import { productSlug } from '../../../utils/tenant-product-slug';

import { localizedSiteString } from '../../../utils/tenant-site-i18n';

import { useTenantMediaUrl } from '../../../composables/useTenantMediaUrl';



const { resolveMediaUrl } = useTenantMediaUrl();

const {

  homePage,

  productsPage,

  localizedCatalogProducts,

  tSite,

  tenant,

  context: visitorContext,

  siteContent,

  language,

} = useTenantSiteBootstrap();



const overlay = computed(() => visitorContext.value?.site_content_localized || null);



const establishedYear = computed(() => String(homePage.value.establishedYear || ''));

const primaryPromise = computed(() =>

  String(overlay.value?.home?.primary_promise || homePage.value.primary_promise || '').trim(),

);

const heroTitle = computed(() =>

  localizedSiteString(

    siteContent.value,

    overlay.value?.home,

    'home',

    'title',

    language.value,

    [

      String(homePage.value.title || ''),

      tenant.value?.brand.site_title,

      tenant.value?.brand.company_name,

      tenant.value?.name,

    ],

  ),

);

const heroDescription = computed(() =>

  localizedSiteString(

    siteContent.value,

    overlay.value?.home,

    'home',

    'description',

    language.value,

    [String(homePage.value.description || ''), tenant.value?.brand.about_summary || ''],

  ),

);

const ctaPrimary = computed(() =>

  String(overlay.value?.home?.ctaPrimary || homePage.value.ctaPrimary || tSite('cta_primary')),

);

const inquiryHook = computed(() =>

  String(

    overlay.value?.home?.inquiryHook ||

      homePage.value.inquiryHook ||

      primaryPromise.value ||

      tSite('section_cta_desc'),

  ),

);

const productsTitle = computed(() =>

  String(overlay.value?.products?.title || productsPage.value.title || tSite('section_products_default')),

);

const productsDescription = computed(() =>

  String(overlay.value?.products?.description || productsPage.value.description || ''),

);

const sectionTitle = computed(() =>

  String(overlay.value?.home?.sectionTitle || homePage.value.sectionTitle || tSite('why_choose_us')),

);

const sectionDesc = computed(() =>

  String(overlay.value?.home?.sectionDesc || homePage.value.sectionDesc || ''),

);



const stats = computed(() => {

  const raw = overlay.value?.home?.stats ?? homePage.value.stats;

  if (!Array.isArray(raw)) return [];

  return raw.filter((s) => s && typeof s === 'object' && 'value' in s) as Array<{ value: string; label: string }>;

});



const serviceStages = computed(() => {

  const raw = overlay.value?.home?.serviceStages ?? homePage.value.serviceStages;

  if (!Array.isArray(raw)) return [];

  return raw.filter((s) => s && typeof s === 'object' && 'title' in s) as Array<{

    stage?: string;

    title: string;

    description?: string;

  }>;

});



const solutions = computed(() => {

  const raw = overlay.value?.home?.solutions ?? homePage.value.solutions;

  if (!Array.isArray(raw)) return [];

  return raw as Array<{ segment: string; title: string; description?: string }>;

});



const advantages = computed(() => {

  const raw = overlay.value?.home?.advantages ?? homePage.value.advantages;

  if (!Array.isArray(raw)) return [];

  return raw.filter((a) => a && typeof a === 'object' && 'title' in a) as Array<{

    title: string;

    description?: string;

  }>;

});



const knowledgeTopics = computed(() => {

  const raw = overlay.value?.home?.knowledgeTopics ?? homePage.value.knowledgeTopics;

  if (!Array.isArray(raw)) return [];

  return raw.filter((k) => k && typeof k === 'object' && 'title' in k) as Array<{

    title: string;

    hook?: string;

  }>;

});



const featuredProducts = computed(() =>

  localizedCatalogProducts.value.slice(0, 6).map((p, i) => ({ ...p, slug: productSlug(p, i) })),

);

</script>



<style scoped>

.lpro-hero-kicker {

  color: var(--lpro-primary);

  max-width: 42rem;

}

.lpro-section-eyebrow {

  margin: 0 0 0.35rem;

  font-size: 0.7rem;

  font-weight: 700;

  letter-spacing: 0.12em;

  text-transform: uppercase;

  color: var(--lpro-primary);

}

.lpro-stages {

  display: grid;

  grid-template-columns: repeat(4, minmax(0, 1fr));

  gap: 1rem;

}

.lpro-stage-card {

  text-align: center;

  padding: 1rem 0.75rem;

  border: 1px solid rgb(226 232 240);

  border-radius: 0.875rem;

  background: #fff;

}

.lpro-stage-num {

  width: 2.25rem;

  height: 2.25rem;

  margin: 0 auto 0.65rem;

  border-radius: 9999px;

  background: var(--lpro-primary);

  color: #fff;

  font-weight: 800;

  font-size: 0.8rem;

  display: flex;

  align-items: center;

  justify-content: center;

}

.lpro-stage-card h3 {

  margin: 0 0 0.35rem;

  font-size: 0.95rem;

  font-weight: 700;

}

.lpro-stage-card p {

  margin: 0;

  font-size: 0.8rem;

  color: rgb(100 116 139);

  line-height: 1.45;

}

.lpro-cta-band {

  background: linear-gradient(135deg, rgb(15 23 42), rgb(30 41 59));

  color: #fff;

  text-align: center;

}

.lpro-cta-band-inner h2 {

  margin: 0 0 0.5rem;

  font-size: clamp(1.35rem, 2.5vw, 1.85rem);

  font-weight: 800;

}

.lpro-cta-band-inner p {

  margin: 0 auto 1.25rem;

  max-width: 36rem;

  opacity: 0.9;

  line-height: 1.55;

}

.lpro-knowledge-card {

  display: flex;

  flex-direction: column;

  gap: 0.5rem;

  min-height: 100%;

}

@media (max-width: 960px) {

  .lpro-stages {

    grid-template-columns: 1fr 1fr;

  }

}

@media (max-width: 640px) {

  .lpro-stages {

    grid-template-columns: 1fr;

  }

}

</style>

