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
        <span class="text-lg font-bold text-gray-900">{{ $t('mobile.cases.pageTitle') }}</span>
      </div>
    </MobileNavbar>

    <div class="pt-16">
      <!-- Header Banner -->
      <div class="bg-gradient-to-br from-blue-600 to-blue-700 px-4 py-6 text-white">
        <h1 class="text-xl font-bold mb-1">{{ $t('mobile.cases.pageTitle') }}</h1>
        <p class="text-sm text-blue-100">{{ $t('mobile.cases.bannerSubtitle') }}</p>
      </div>

      <!-- Cases List -->
      <div class="px-4 py-5 space-y-4">
        <NuxtLink
          v-for="item in caseList"
          :key="item.id"
          :to="`/cases/${item.slug}`"
          class="block bg-white rounded-2xl overflow-hidden shadow-sm border border-gray-100 active:scale-[0.98] transition-transform"
        >
          <!-- Image Placeholder -->
          <div class="aspect-video bg-gradient-to-br from-gray-200 to-gray-300 relative flex items-center justify-center">
            <svg class="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <div class="absolute top-3 left-3">
              <span
                class="px-2.5 py-1 bg-blue-600/80 backdrop-blur-sm text-white text-[10px] font-medium rounded-full"
              >
                {{ item.tag }}
              </span>
            </div>
          </div>
          <!-- Content -->
          <div class="p-4">
            <h3 class="text-base font-bold text-gray-900 mb-1.5">{{ item.title }}</h3>
            <p class="text-sm text-gray-500 leading-relaxed line-clamp-2">{{ item.desc }}</p>
            <div class="flex items-center gap-3 mt-3 text-xs text-gray-400">
              <span class="flex items-center gap-1">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                </svg>
                {{ item.location }}
              </span>
              <span class="flex items-center gap-1">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                {{ item.volume }}
              </span>
            </div>
          </div>
        </NuxtLink>
      </div>

      <!-- View More Link -->
      <div class="px-4 pb-6">
        <NuxtLink
          to="/cases"
          class="flex items-center justify-center gap-2 w-full py-3 bg-white border border-gray-200 text-gray-600 rounded-2xl font-medium text-sm active:scale-[0.98] transition-transform"
        >
          {{ $t('mobile.cases.viewAllCases') }}
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
const { t } = useI18n();

const caseList = computed(() => [
  {
    id: 1,
    slug: 'daxing-airport',
    title: t('mobile.cases.case1.title'),
    desc: t('mobile.cases.case1.desc'),
    tag: t('mobile.cases.case1.tag'),
    location: t('mobile.cases.case1.location'),
    volume: '2,000m³',
  },
  {
    id: 2,
    slug: 'shanghai-center',
    title: t('mobile.cases.case2.title'),
    desc: t('mobile.cases.case2.desc'),
    tag: t('mobile.cases.case2.tag'),
    location: t('mobile.cases.case2.location'),
    volume: '3,500m³',
  },
  {
    id: 3,
    slug: 'shenzhen-convention',
    title: t('mobile.cases.case3.title'),
    desc: t('mobile.cases.case3.desc'),
    tag: t('mobile.cases.case3.tag'),
    location: t('mobile.cases.case3.location'),
    volume: '5,000m³',
  },
  {
    id: 4,
    slug: 'hangzhou-asian',
    title: t('mobile.cases.case4.title'),
    desc: t('mobile.cases.case4.desc'),
    tag: t('mobile.cases.case4.tag'),
    location: t('mobile.cases.case4.location'),
    volume: '4,200m³',
  },
  {
    id: 5,
    slug: 'chengdu-tianfu',
    title: t('mobile.cases.case5.title'),
    desc: t('mobile.cases.case5.desc'),
    tag: t('mobile.cases.case5.tag'),
    location: t('mobile.cases.case5.location'),
    volume: '2,800m³',
  },
  {
    id: 6,
    slug: 'xiong-an',
    title: t('mobile.cases.case6.title'),
    desc: t('mobile.cases.case6.desc'),
    tag: t('mobile.cases.case6.tag'),
    location: t('mobile.cases.case6.location'),
    volume: '6,000m³',
  },
]);

useHead({
  title: t('mobile.cases.seoTitle'),
  meta: [
    { name: 'description', content: t('mobile.cases.seoDesc') },
  ],
});
</script>
