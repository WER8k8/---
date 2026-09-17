/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="min-h-screen bg-gray-50 pb-safe-bottom">
    <!-- Mobile Navbar -->
    <MobileNavbar :title="t('mobile.cases.detailTitle')" safe-area-top :blur="true" />

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center min-h-[60vh]">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex items-center justify-center min-h-[60vh] px-4">
      <div class="text-center">
        <div class="text-6xl mb-4">😞</div>
        <h2 class="text-xl font-bold text-gray-900 mb-2">
          {{ t('mobile.cases.loadFailed') }}
        </h2>
        <p class="text-gray-600 mb-6">{{ error }}</p>
        <NuxtLink to="/cases" class="mobile-btn-primary inline-block px-6 py-3 rounded-full">
          {{ t('mobile.cases.backToList') }}
        </NuxtLink>
      </div>
    </div>

    <!-- Case Detail -->
    <div v-else-if="caseItem" class="pb-20">
      <!-- Hero Image -->
      <div class="relative h-64 md:h-80 bg-gray-200">
        <img
          v-if="caseItem.cover_image"
          :src="caseItem.cover_image"
          :alt="caseItem.project_name"
          class="w-full h-full object-cover"
        >
        <div v-else class="w-full h-full flex items-center justify-center bg-gradient-to-br from-blue-500 to-blue-700">
          <span class="text-white text-4xl">🏗️</span>
        </div>
        <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-black/30 to-transparent" />
        <div class="absolute bottom-0 left-0 right-0 p-4 md:p-6">
          <div class="flex flex-wrap gap-2 mb-2">
            <span class="px-2 py-1 bg-blue-600/90 text-white text-xs font-medium rounded-full">
              {{ caseItem.location || t('mobile.cases.nationWide') }}
            </span>
            <span class="px-2 py-1 bg-white/20 text-white text-xs font-medium rounded-full">
              {{ caseItem.project_date || t('mobile.cases.unknownDate') }}
            </span>
          </div>
          <h1 class="text-2xl md:text-3xl font-bold text-white mb-2">
            {{ caseItem.project_name }}
          </h1>
        </div>
      </div>

      <!-- Case Info -->
      <div class="px-4 py-6">
        <!-- Description -->
        <div class="bg-white rounded-xl shadow-sm p-4 mb-4">
          <h2 class="text-lg font-semibold text-gray-900 mb-3">
            {{ t('mobile.cases.projectOverview') }}
          </h2>
          <p class="text-sm text-gray-600 leading-relaxed">
            {{ caseItem.description || t('mobile.cases.noDesc') }}
          </p>
        </div>

        <!-- Project Details -->
        <div class="bg-white rounded-xl shadow-sm p-4 mb-4">
          <h2 class="text-lg font-semibold text-gray-900 mb-3">
            {{ t('mobile.cases.projectInfo') }}
          </h2>
          <div class="space-y-3">
            <div v-if="caseItem.client_name" class="flex justify-between items-center">
              <span class="text-sm text-gray-500">{{ t('mobile.cases.clientName') }}</span>
              <span class="text-sm font-medium text-gray-900">{{ caseItem.client_name }}</span>
            </div>
            <div v-if="caseItem.location" class="flex justify-between items-center">
              <span class="text-sm text-gray-500">{{ t('mobile.cases.projectLocation') }}</span>
              <span class="text-sm font-medium text-gray-900">{{ caseItem.location }}</span>
            </div>
            <div v-if="caseItem.construction_area" class="flex justify-between items-center">
              <span class="text-sm text-gray-500">{{ t('mobile.cases.constructionArea') }}</span>
              <span class="text-sm font-medium text-gray-900">{{ caseItem.construction_area }}</span>
            </div>
            <div v-if="caseItem.project_date" class="flex justify-between items-center">
              <span class="text-sm text-gray-500">{{ t('mobile.cases.projectDate') }}</span>
              <span class="text-sm font-medium text-gray-900">{{ caseItem.project_date }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-sm text-gray-500">{{ t('mobile.cases.viewCount') }}</span>
              <span class="text-sm font-medium text-gray-900">{{ caseItem.view_count || 0 }}</span>
            </div>
          </div>
        </div>

        <!-- Materials Used -->
        <div v-if="caseItem.materials_used" class="bg-white rounded-xl shadow-sm p-4 mb-4">
          <h2 class="text-lg font-semibold text-gray-900 mb-3">
            {{ t('mobile.cases.materialsUsed') }}
          </h2>
          <p class="text-sm text-gray-600 leading-relaxed">
            {{ caseItem.materials_used }}
          </p>
        </div>

        <!-- Contact CTA -->
        <div class="bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl p-4 text-white">
          <h3 class="text-lg font-semibold mb-2">
            {{ t('mobile.cases.interestedContact') }}
          </h3>
          <p class="text-sm text-blue-100 mb-4">
            {{ t('mobile.cases.contactDesc') }}
          </p>
          <div class="flex flex-col gap-2">
            <NuxtLink to="/contact" class="mobile-btn bg-white text-blue-600 justify-center">
              {{ t('mobile.cases.consultNow') }}
            </NuxtLink>
            <a :href="`tel:${contactPhone}`" class="mobile-btn border-2 border-white text-white justify-center">
              {{ t('mobile.cases.phoneConsult') }}
            </a>
          </div>
        </div>
      </div>
    </div>

    <!-- Mobile Tab Bar -->
    <MobileTabBar />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useCaseStore } from '~/stores/case';
import { SITE_CONFIG } from '~/config/site';

const route = useRoute();
const { t } = useI18n();
const caseStore = useCaseStore();
const contactPhone = SITE_CONFIG.phone;

const { slug } = route.params as { slug: string };

await caseStore.fetchCaseBySlug(slug);

const caseItem = computed(() => caseStore.currentCase);
const loading = computed(() => caseStore.loading);
const error = computed(() => caseStore.error);

useHead({
  title: computed(() =>
    caseItem.value ? `${caseItem.value.project_name} - ${t('mobile.cases.seoTitle')}` : t('mobile.cases.seoFallbackTitle')
  ),
  meta: [
    { name: 'description', content: computed(() => caseItem.value?.description || '') },
  ],
});
</script>
