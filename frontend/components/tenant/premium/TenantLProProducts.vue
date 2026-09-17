/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <PremiumB2bShell active-key="products">
    <section class="lpro-hero">
      <div class="lpro-container">
        <h1>{{ productsTitle }}</h1>
        <p>{{ productsDescription || tSite('section_products_desc') }}</p>
      </div>
    </section>

    <section class="lpro-section lpro-section--white">
      <div class="lpro-container">
        <div class="lpro-products-toolbar">
          <label class="lpro-search">
            <span class="sr-only">{{ tSite('products_search_label') }}</span>
            <input
              v-model="searchQuery"
              type="search"
              class="lpro-search-input"
              :placeholder="tSite('products_search_placeholder')"
              autocomplete="off"
            />
          </label>
          <select v-model="sortBy" class="lpro-sort-select" :aria-label="tSite('products_sort_label')">
            <option value="default">{{ tSite('products_sort_default') }}</option>
            <option value="name-asc">{{ tSite('products_sort_name_asc') }}</option>
            <option value="name-desc">{{ tSite('products_sort_name_desc') }}</option>
          </select>
          <button
            v-if="searchQuery.trim() || specFilter"
            type="button"
            class="lpro-search-clear"
            @click="resetFilters"
          >
            {{ tSite('products_clear_filters') }}
          </button>
        </div>

        <div v-if="categoryFilters.length" class="lpro-chip-row">
          <NuxtLink
            to="/tenant/products"
            class="lpro-chip"
            :class="{ 'is-active': !activeCategory }"
          >
            {{ tSite('section_products_default') }}
          </NuxtLink>
          <NuxtLink
            v-for="cat in categoryFilters"
            :key="cat.slug"
            :to="tenantProductsCategoryQuery(cat.slug)"
            class="lpro-chip"
            :class="{ 'is-active': activeCategory === cat.slug }"
          >
            {{ cat.name }}
          </NuxtLink>
        </div>

        <div v-if="specFilterOptions.length" class="lpro-chip-row lpro-chip-row--spec">
          <span class="lpro-chip-label">{{ tSite('products_spec_filter') }}</span>
          <button
            type="button"
            class="lpro-chip lpro-chip--button"
            :class="{ 'is-active': !specFilter }"
            @click="specFilter = ''"
          >
            {{ tSite('products_spec_all') }}
          </button>
          <button
            v-for="opt in specFilterOptions"
            :key="opt.slug"
            type="button"
            class="lpro-chip lpro-chip--button"
            :class="{ 'is-active': specFilter === opt.slug }"
            @click="specFilter = opt.slug"
          >
            {{ opt.label }}
          </button>
        </div>

        <div v-if="filteredProducts.length" class="lpro-grid">
          <article v-for="item in filteredProducts" :key="item.slug" class="lpro-card">
            <div class="lpro-thumb">
              <img v-if="item.image" :src="resolveMediaUrl(item.image)" :alt="item.imageAlt || item.name" />
            </div>
            <h3>{{ item.name }}</h3>
            <p>{{ item.summary }}</p>
            <p v-if="item.category" class="text-xs mt-2 opacity-70">{{ item.category }}</p>
            <ul v-if="item.specs?.length" class="lpro-spec-tags">
              <li v-for="(spec, i) in item.specs.slice(0, 3)" :key="i">
                {{ spec.label }}: {{ spec.value }}
              </li>
            </ul>
            <NuxtLink :to="tenantProductDetailPath(item.slug!)" class="lpro-link">
              {{ tSite('view_product') }} →
            </NuxtLink>
          </article>
        </div>
        <p v-else class="text-[var(--lpro-muted)]">
          {{ hasActiveFilters ? tSite('products_no_match') : tSite('products_empty') }}
        </p>
      </div>
    </section>
  </PremiumB2bShell>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import PremiumB2bShell from './PremiumB2bShell.vue';
import { useTenantSiteBootstrap } from '../../../composables/useTenantSiteBootstrap';
import { useTenantProductFilter } from '../../../composables/useTenantProductFilter';
import {
  tenantProductDetailPath,
  tenantProductsCategoryQuery,
} from '../../../composables/useTenantLProNav';
import { categorySlug } from '../../../utils/tenant-product-slug';
import { useTenantMediaUrl } from '../../../composables/useTenantMediaUrl';

const route = useRoute();
const { resolveMediaUrl } = useTenantMediaUrl();
const {
  productsPage,
  localizedCatalogProducts,
  categoryFilters,
  tSite,
  context: visitorContext,
} = useTenantSiteBootstrap();

const overlay = computed(() => visitorContext.value?.site_content_localized || null);
const productsTitle = computed(() =>
  String(overlay.value?.products?.title || productsPage.value.title || tSite('section_products_default')),
);
const productsDescription = computed(() =>
  String(overlay.value?.products?.description || productsPage.value.description || ''),
);

const activeCategory = computed(() => {
  const q = route.query.category;
  return q ? categorySlug(String(q)) : '';
});

const {
  searchQuery,
  sortBy,
  specFilter,
  specFilterOptions,
  filteredProducts,
  hasActiveFilters,
  resetFilters,
} = useTenantProductFilter(localizedCatalogProducts, activeCategory);
</script>
