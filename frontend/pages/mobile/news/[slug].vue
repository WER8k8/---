/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="min-h-screen bg-gray-50 pb-safe-bottom">
    <!-- Mobile Navbar -->
    <MobileNavbar :title="t('mobile.news.detailTitle')" safe-area-top :blur="true" />

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center min-h-[60vh]">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex items-center justify-center min-h-[60vh] px-4">
      <div class="text-center">
        <div class="text-6xl mb-4">😞</div>
        <h2 class="text-xl font-bold text-gray-900 mb-2">
          {{ t('mobile.news.loadFailed') }}
        </h2>
        <p class="text-gray-600 mb-6">{{ error }}</p>
        <NuxtLink to="/news" class="mobile-btn-primary inline-block px-6 py-3 rounded-full">
          {{ t('mobile.news.backToList') }}
        </NuxtLink>
      </div>
    </div>

    <!-- News Detail -->
    <div v-else-if="newsItem" class="pb-20">
      <!-- Hero Image -->
      <div class="relative h-64 md:h-80 bg-gray-200">
        <img
          v-if="newsItem.cover_image"
          :src="newsItem.cover_image"
          :alt="newsItem.title"
          class="w-full h-full object-cover"
        >
        <div v-else class="w-full h-full flex items-center justify-center bg-gradient-to-br from-blue-500 to-blue-700">
          <span class="text-white text-4xl">📰</span>
        </div>
      </div>

      <!-- News Content -->
      <div class="px-4 py-6">
        <!-- Title & Meta -->
        <div class="bg-white rounded-xl shadow-sm p-4 mb-4">
          <h1 class="text-xl md:text-2xl font-bold text-gray-900 mb-3">
            {{ newsItem.title }}
          </h1>
          <div class="flex items-center gap-3 text-sm text-gray-500">
            <span>{{ formatDate(newsItem.publish_date) }}</span>
            <span class="px-2 py-1 bg-blue-50 text-blue-600 rounded-full text-xs">
              {{ newsItem.category || t('mobile.news.defaultCategory') }}
            </span>
          </div>
        </div>

        <!-- Content -->
        <div class="bg-white rounded-xl shadow-sm p-4 mb-4">
          <div class="prose prose-sm max-w-none text-gray-700 leading-relaxed">
            <div v-html="sanitizedContent" />
          </div>
        </div>

        <!-- Tags -->
        <div v-if="newsItem.tags && newsItem.tags.length > 0" class="bg-white rounded-xl shadow-sm p-4 mb-4">
          <h3 class="text-sm font-semibold text-gray-900 mb-2">
            {{ t('mobile.news.tags') }}
          </h3>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="tag in newsItem.tags"
              :key="tag"
              class="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-xs"
            >
              {{ tag }}
            </span>
          </div>
        </div>

        <!-- Share -->
        <div class="bg-white rounded-xl shadow-sm p-4">
          <h3 class="text-sm font-semibold text-gray-900 mb-3">
            {{ t('mobile.news.share') }}
          </h3>
          <div class="flex gap-3">
            <button class="mobile-btn-secondary flex-1 py-2 rounded-lg text-sm">
              📱 WeChat
            </button>
            <button class="mobile-btn-secondary flex-1 py-2 rounded-lg text-sm">
              🔗 Copy Link
            </button>
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
import { useNewsStore } from '~/stores/news';
import { useSanitize } from '~/composables/useSanitize';

const route = useRoute();
const { t } = useI18n();
const newsStore = useNewsStore();

const { slug } = route.params as { slug: string };

await newsStore.fetchNewsBySlug(slug);

const newsItem = computed(() => newsStore.currentNews);
const loading = computed(() => newsStore.loading);
const error = computed(() => newsStore.error);
const { sanitizeHtml } = useSanitize();
const sanitizedContent = computed(() => sanitizeHtml(newsItem.value?.content || ''));

function formatDate(dateStr: string | null): string {
  if (!dateStr) return t('mobile.news.unknownDate');
  const date = new Date(dateStr);
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' });
}

useHead({
  title: computed(() =>
    newsItem.value ? `${newsItem.value.title} - ${t('mobile.news.seoTitle')}` : t('mobile.news.seoFallbackTitle')
  ),
  meta: [
    { name: 'description', content: computed(() => newsItem.value?.summary || '') },
  ],
});
</script>
