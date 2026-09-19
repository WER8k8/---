/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <PremiumB2bShell active-key="solutions">
    <section class="lpro-hero">
      <div class="lpro-container">
        <h1>{{ tSite('section_solutions') }}</h1>
        <p>{{ tSite('section_solutions_desc') }}</p>
      </div>
    </section>
    <section class="lpro-section lpro-section--white">
      <div class="lpro-container">
        <div class="lpro-grid">
          <article
            v-for="(sol, i) in solutions"
            :key="i"
            class="lpro-card"
          >
            <div class="text-xs font-semibold uppercase text-[var(--lpro-muted)]">
              {{ sol.segment }}
            </div>
            <h3>{{ sol.title }}</h3>
            <p>{{ sol.description }}</p>
            <NuxtLink
              to="/tenant/contact"
              class="lpro-link"
            >
              {{ tSite('inquiry_link') }}
            </NuxtLink>
          </article>
        </div>
      </div>
    </section>
  </PremiumB2bShell>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import PremiumB2bShell from './PremiumB2bShell.vue';
import { useTenantSiteBootstrap } from '../../../composables/useTenantSiteBootstrap';

const { homePage, tSite, context: visitorContext } = useTenantSiteBootstrap();

const overlay = computed(() => visitorContext.value?.site_content_localized || null);

const solutions = computed(() => {
  const raw = overlay.value?.home?.solutions ?? homePage.value.solutions;
  if (!Array.isArray(raw)) return [];
  return raw as Array<{ segment: string; title: string; description?: string }>;
});
</script>
