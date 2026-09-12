<template>
  <div class="min-h-screen bg-gray-50 pb-safe-bottom">
    <!-- Mobile Header with Back Button -->
    <MobileNavbar>
      <div class="flex items-center h-14 gap-3">
        <NuxtLink to="/mobile" class="p-2 -ml-2 rounded-lg hover:bg-gray-100 transition-colors">
          <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </NuxtLink>
        <span class="text-lg font-bold text-gray-900">{{ $t('mobile.news.pageTitle') }}</span>
      </div>
    </MobileNavbar>

    <div class="pt-16">
      <!-- Header Banner -->
      <div class="bg-gradient-to-br from-blue-600 to-blue-700 px-4 py-6 text-white">
        <h1 class="text-xl font-bold mb-1">{{ $t('mobile.news.pageTitle') }}</h1>
        <p class="text-sm text-blue-100">{{ $t('mobile.news.bannerSubtitle') }}</p>
      </div>

      <!-- Category Tabs -->
      <div class="sticky top-14 z-40 bg-white border-b border-gray-100">
        <div class="flex gap-2 px-4 py-3 overflow-x-auto no-scrollbar touch-pan-x snap-x">
          <button
            v-for="cat in categories"
            :key="cat.id"
            @click="selectedCategory = cat.id"
            class="flex-shrink-0 px-4 py-1.5 rounded-full text-sm font-medium transition-all snap-center whitespace-nowrap"
            :class="selectedCategory === cat.id ? 'bg-blue-600 text-white shadow-md' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
          >
            {{ cat.name }}
          </button>
        </div>
      </div>

      <!-- News List -->
      <div class="px-4 py-5 space-y-3">
        <NuxtLink
          v-for="item in filteredNews"
          :key="item.id"
          :to="`/news/${item.slug}`"
          class="block bg-white rounded-2xl p-4 shadow-sm border border-gray-100 active:scale-[0.98] transition-transform"
        >
          <!-- Date Badge -->
          <div class="flex items-start gap-3">
            <div class="flex-shrink-0 w-12 h-12 bg-gradient-to-b from-blue-50 to-blue-100 rounded-xl flex flex-col items-center justify-center">
              <span class="text-xs font-bold text-blue-600 leading-none">{{ item.day }}</span>
              <span class="text-[10px] text-blue-500 mt-0.5">{{ item.month }}</span>
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <span
                  class="px-2 py-0.5 rounded-full text-[10px] font-medium"
                  :class="tagClass(item.tag)"
                >
                  {{ item.tag }}
                </span>
              </div>
              <h3 class="text-sm font-semibold text-gray-900 line-clamp-2 mb-1">{{ item.title }}</h3>
              <p class="text-xs text-gray-500 line-clamp-2 leading-relaxed">{{ item.summary }}</p>
              <div class="flex items-center gap-2 mt-2 text-[10px] text-gray-400">
                <span>{{ $t('mobile.news.readFull') }}</span>
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </div>
          </div>
        </NuxtLink>
      </div>

      <!-- Empty State -->
      <div v-if="filteredNews.length === 0" class="text-center py-16">
        <svg class="w-14 h-14 mx-auto text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
        </svg>
        <h3 class="text-base font-semibold text-gray-700 mb-1">{{ $t('mobile.news.noNews') }}</h3>
        <p class="text-sm text-gray-400">{{ $t('mobile.news.noNewsDesc') }}</p>
      </div>

      <!-- View More Link -->
      <div class="px-4 pb-6">
        <NuxtLink
          to="/news"
          class="flex items-center justify-center gap-2 w-full py-3 bg-white border border-gray-200 text-gray-600 rounded-2xl font-medium text-sm active:scale-[0.98] transition-transform"
        >
          {{ $t('mobile.news.viewAllNews') }}
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
          </svg>
        </NuxtLink>
      </div>
    </div>

    <!-- Mobile Bottom Tab Bar -->
    <MobileTabBar />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

const { t } = useI18n();

const selectedCategory = ref('all');

const categories = computed(() => [
  { id: 'all', name: t('mobile.news.all') },
  { id: 'company', name: t('mobile.news.companyNews') },
  { id: 'industry', name: t('mobile.news.industryNews') },
  { id: 'product', name: t('mobile.news.productNews') },
]);

const newsList = computed(() => [
  {
    id: 1,
    slug: 'new-product-launch-2026',
    title: t('mobile.news.news1.title'),
    summary: t('mobile.news.news1.summary'),
    tag: t('mobile.news.tagProductNews'),
    day: '15',
    month: '05',
    category: 'product',
  },
  {
    id: 2,
    slug: 'green-building-expo',
    title: t('mobile.news.news2.title'),
    summary: t('mobile.news.news2.summary'),
    tag: t('mobile.news.tagCompanyNews'),
    day: '10',
    month: '05',
    category: 'company',
  },
  {
    id: 3,
    slug: 'industry-standard-2026',
    title: t('mobile.news.news3.title'),
    summary: t('mobile.news.news3.summary'),
    tag: t('mobile.news.tagIndustryNews'),
    day: '28',
    month: '04',
    category: 'industry',
  },
  {
    id: 4,
    slug: 'company-anniversary',
    title: t('mobile.news.news4.title'),
    summary: t('mobile.news.news4.summary'),
    tag: t('mobile.news.tagCompanyNews'),
    day: '20',
    month: '04',
    category: 'company',
  },
  {
    id: 5,
    slug: 'new-workshop',
    title: t('mobile.news.news5.title'),
    summary: t('mobile.news.news5.summary'),
    tag: t('mobile.news.tagCompanyNews'),
    day: '08',
    month: '04',
    category: 'company',
  },
  {
    id: 6,
    slug: 'thermal-insulation-tech',
    title: t('mobile.news.news6.title'),
    summary: t('mobile.news.news6.summary'),
    tag: t('mobile.news.tagIndustryNews'),
    day: '25',
    month: '03',
    category: 'industry',
  },
  {
    id: 7,
    slug: 'quality-certification',
    title: t('mobile.news.news7.title'),
    summary: t('mobile.news.news7.summary'),
    tag: t('mobile.news.tagCompanyNews'),
    day: '12',
    month: '03',
    category: 'company',
  },
  {
    id: 8,
    slug: 'winter-construction-guide',
    title: t('mobile.news.news8.title'),
    summary: t('mobile.news.news8.summary'),
    tag: t('mobile.news.tagProductNews'),
    day: '05',
    month: '02',
    category: 'product',
  },
]);

const filteredNews = computed(() => {
  if (selectedCategory.value === 'all') return newsList.value;
  return newsList.value.filter((item) => item.category === selectedCategory.value);
});

function tagClass(tag: string): string {
  const map: Record<string, string> = {
    [t('mobile.news.tagCompanyNews')]: 'bg-blue-50 text-blue-600',
    [t('mobile.news.tagIndustryNews')]: 'bg-green-50 text-green-600',
    [t('mobile.news.tagProductNews')]: 'bg-purple-50 text-purple-600',
  };
  return map[tag] || 'bg-gray-100 text-gray-600';
}

useHead({
  title: t('mobile.news.seoTitle'),
  meta: [
    { name: 'description', content: t('mobile.news.seoDesc') },
  ],
});
</script>
