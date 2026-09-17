/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <PremiumB2bShell active-key="downloads">
    <section class="lpro-hero">
      <div class="lpro-container">
        <h1>{{ tSite('section_downloads') }}</h1>
        <p>{{ tSite('section_downloads_desc') }}</p>
      </div>
    </section>
    <section class="lpro-section lpro-section--white">
      <div class="lpro-container">
        <div v-if="items.length" class="space-y-3">
          <a
            v-for="(item, i) in items"
            :key="i"
            :href="resolveMediaUrl(item.url)"
            class="lpro-card block"
            target="_blank"
            rel="noopener noreferrer"
          >
            <div class="font-semibold">{{ item.title }}</div>
            <div v-if="item.type" class="text-sm text-[var(--lpro-muted)]">{{ item.type }}</div>
          </a>
        </div>
        <p v-else class="text-[var(--lpro-muted)]">{{ tSite('downloads_empty') }}</p>
      </div>
    </section>
  </PremiumB2bShell>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import PremiumB2bShell from './PremiumB2bShell.vue';
import { useTenantSiteBootstrap } from '../../../composables/useTenantSiteBootstrap';
import { useTenantMediaUrl } from '../../../composables/useTenantMediaUrl';

const { downloadsPage, tSite } = useTenantSiteBootstrap();
const { resolveMediaUrl } = useTenantMediaUrl();

const items = computed(() => {
  const raw = downloadsPage.value.items;
  if (!Array.isArray(raw)) return [];
  return raw
    .map((row) => {
      if (!row || typeof row !== 'object') return null;
      const o = row as Record<string, unknown>;
      const title = String(o.title || '').trim();
      const url = String(o.url || '').trim();
      if (!title || !url) return null;
      return { title, url, type: o.type ? String(o.type) : '' };
    })
    .filter((x): x is { title: string; url: string; type: string } => x !== null);
});
</script>
