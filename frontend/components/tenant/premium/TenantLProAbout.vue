<template>
  <PremiumB2bShell active-key="about">
    <section class="lpro-hero">
      <div class="lpro-container">
        <h1>{{ tSite('section_about', { name: companyName }) }}</h1>
        <p v-if="aboutText">{{ aboutText.slice(0, 200) }}</p>
      </div>
    </section>
    <section class="lpro-section lpro-section--white">
      <div class="lpro-container max-w-3xl">
        <p v-if="aboutText" class="mb-6 leading-relaxed">{{ aboutText }}</p>
        <div v-if="mission || vision" class="lpro-grid mb-6">
          <article v-if="mission" class="lpro-card">
            <h3 class="font-semibold mb-2">{{ tSite('mission') }}</h3>
            <p>{{ mission }}</p>
          </article>
          <article v-if="vision" class="lpro-card">
            <h3 class="font-semibold mb-2">{{ tSite('vision') }}</h3>
            <p>{{ vision }}</p>
          </article>
        </div>
        <p v-if="capacitySummary" class="text-[var(--lpro-muted)]">{{ capacitySummary }}</p>
        <div v-if="milestones.length" class="mt-8">
          <h2 class="lpro-section-title">{{ tSite('company_history') }}</h2>
          <div class="space-y-4">
            <article v-for="(m, i) in milestones" :key="i" class="lpro-card">
              <div class="font-bold text-[var(--lpro-primary)]">{{ m.year }}</div>
              <h3 class="font-semibold">{{ m.title }}</h3>
              <p>{{ m.description }}</p>
            </article>
          </div>
        </div>
      </div>
    </section>
  </PremiumB2bShell>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import PremiumB2bShell from './PremiumB2bShell.vue';
import { useTenantSiteBootstrap } from '../../../composables/useTenantSiteBootstrap';
import { localizedSiteString } from '../../../utils/tenant-site-i18n';

const {
  aboutPage,
  tenant,
  tSite,
  context: visitorContext,
  siteContent,
  language,
} = useTenantSiteBootstrap();

const overlay = computed(() => visitorContext.value?.site_content_localized || null);
const companyName = computed(
  () =>
    localizedSiteString(
      siteContent.value,
      overlay.value?.brand,
      'brand',
      'name',
      language.value,
      [tenant.value?.brand.company_name, tenant.value?.name].filter((x): x is string => typeof x === 'string'),
    ) || 'Company',
);
const aboutText = computed(() =>
  localizedSiteString(
    siteContent.value,
    overlay.value?.about,
    'about',
    'aboutText',
    language.value,
    [String(aboutPage.value.aboutText || ''), tenant.value?.brand.about_summary || ''],
  ),
);
const mission = computed(() => String(overlay.value?.about?.mission || aboutPage.value.mission || ''));
const vision = computed(() => String(overlay.value?.about?.vision || aboutPage.value.vision || ''));
const capacitySummary = computed(() =>
  String(overlay.value?.about?.capacitySummary || aboutPage.value.capacitySummary || ''),
);
const milestones = computed(() => {
  const raw = overlay.value?.about?.milestones ?? aboutPage.value.milestones;
  if (!Array.isArray(raw)) return [];
  return raw as Array<{ year: string; title: string; description?: string }>;
});
</script>
