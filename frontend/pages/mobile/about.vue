/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="min-h-screen bg-gray-50 pb-safe-bottom">
    <!-- Mobile Header with Back Button -->
    <MobileNavbar>
      <div class="flex items-center h-14 gap-3">
        <NuxtLink
          to="/mobile"
          class="p-2 -ml-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <svg
            class="w-5 h-5 text-gray-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 19l-7-7 7-7"
            />
          </svg>
        </NuxtLink>
        <span class="text-lg font-bold text-gray-900">{{ $t('mobile.about.pageTitle') }}</span>
      </div>
    </MobileNavbar>

    <div class="pt-16">
      <!-- Banner -->
      <div class="bg-gradient-to-br from-blue-600 to-blue-700 px-4 py-8 text-white">
        <div class="text-center">
          <div class="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center mx-auto mb-3">
            <span class="text-white font-bold text-2xl">{{ $t('mobile.brandChar') }}</span>
          </div>
          <h1 class="text-2xl font-bold mb-2">
            {{ $t('mobile.about.bannerTitle') }}
          </h1>
          <p class="text-sm text-blue-100">
            {{ $t('mobile.about.bannerSubtitle') }}
          </p>
        </div>
      </div>

      <!-- Company Introduction -->
      <section class="px-4 py-6">
        <h2 class="text-lg font-bold text-gray-900 mb-3">
          {{ $t('mobile.about.companyIntro') }}
        </h2>
        <MobileExpandable
          collapsed-height="80px"
          max-height="400px"
        >
          <div class="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 space-y-3">
            <p class="text-sm text-gray-600 leading-relaxed">
              {{ $t('mobile.about.intro1') }}
            </p>
            <p class="text-sm text-gray-600 leading-relaxed">
              {{ $t('mobile.about.intro2') }}
            </p>
            <p class="text-sm text-gray-600 leading-relaxed">
              {{ $t('mobile.about.intro3') }}
            </p>
            <p class="text-sm text-gray-600 leading-relaxed">
              {{ $t('mobile.about.intro4') }}
            </p>
          </div>
        </MobileExpandable>
      </section>

      <!-- Core Advantages -->
      <section class="px-4 pb-4">
        <h2 class="text-lg font-bold text-gray-900 mb-3">
          {{ $t('mobile.about.coreAdvantages') }}
        </h2>
        <div class="grid grid-cols-2 gap-3">
          <div
            v-for="item in advantages"
            :key="item.title"
            class="bg-white rounded-2xl p-4 shadow-sm border border-gray-100"
          >
            <div
              class="w-10 h-10 rounded-xl flex items-center justify-center mb-3"
              :class="item.bgClass"
            >
              <svg
                class="w-5 h-5"
                :class="item.iconClass"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  :d="item.iconPath"
                />
              </svg>
            </div>
            <h3 class="text-sm font-bold text-gray-900 mb-1">
              {{ item.title }}
            </h3>
            <p class="text-xs text-gray-500 leading-relaxed">
              {{ item.desc }}
            </p>
          </div>
        </div>
      </section>

      <!-- Contact Info Card -->
      <section class="px-4 pb-6">
        <h2 class="text-lg font-bold text-gray-900 mb-3">
          {{ $t('mobile.about.contactInfo') }}
        </h2>
        <div class="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 space-y-4">
          <template
            v-for="item in contactItems"
            :key="item.label"
          >
            <a
              v-if="item.href !== '#no-link'"
              :href="item.href"
              class="flex items-center gap-3 active:scale-[0.98] transition-transform cursor-pointer"
            >
              <div class="w-10 h-10 bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl flex items-center justify-center flex-shrink-0">
                <svg
                  class="w-5 h-5 text-blue-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    :d="item.iconPath"
                  />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-xs text-gray-500">{{ item.label }}</p>
                <p class="text-sm font-semibold text-gray-900">{{ item.value }}</p>
              </div>
              <svg
                class="w-4 h-4 text-gray-400 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </a>
            <div
              v-else
              class="flex items-center gap-3"
            >
              <div class="w-10 h-10 bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl flex items-center justify-center flex-shrink-0">
                <svg
                  class="w-5 h-5 text-blue-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    :d="item.iconPath"
                  />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-xs text-gray-500">
                  {{ item.label }}
                </p>
                <p class="text-sm font-semibold text-gray-900">
                  {{ item.value }}
                </p>
              </div>
            </div>
          </template>
        </div>
      </section>

      <!-- Bottom CTA -->
      <section class="px-4 pb-6">
        <NuxtLink
          to="/mobile/contact"
          class="flex items-center justify-center gap-2 w-full py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-2xl font-bold text-sm shadow-lg active:scale-[0.98] transition-transform"
        >
          <svg
            class="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
          {{ $t('mobile.about.onlineConsult') }}
        </NuxtLink>
      </section>
    </div>

    <!-- Mobile Bottom Tab Bar -->
    <MobileTabBar />
  </div>
</template>

<script setup lang="ts">
const { t } = useI18n();

const advantages = computed(() => [
  {
    title: t('mobile.about.advantage1Title'),
    desc: t('mobile.about.advantage1Desc'),
    bgClass: 'bg-blue-50',
    iconClass: 'text-blue-600',
    iconPath: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
  },
  {
    title: t('mobile.about.advantage2Title'),
    desc: t('mobile.about.advantage2Desc'),
    bgClass: 'bg-purple-50',
    iconClass: 'text-purple-600',
    iconPath: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z',
  },
  {
    title: t('mobile.about.advantage3Title'),
    desc: t('mobile.about.advantage3Desc'),
    bgClass: 'bg-green-50',
    iconClass: 'text-green-600',
    iconPath: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z',
  },
  {
    title: t('mobile.about.advantage4Title'),
    desc: t('mobile.about.advantage4Desc'),
    bgClass: 'bg-orange-50',
    iconClass: 'text-orange-600',
    iconPath: 'M13 10V3L4 14h7v7l9-11h-7z',
  },
]);

const contactItems = computed(() => [
  {
    label: t('mobile.about.hotline'),
    value: SITE_CONFIG.phone,
    href: 'tel:' + SITE_CONFIG.phone,
    iconPath: 'M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z',
  },
  {
    label: t('mobile.about.companyEmail'),
    value: SITE_CONFIG.email,
    href: 'mailto:' + SITE_CONFIG.email,
    iconPath: 'M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z',
  },
  {
    label: t('mobile.about.companyAddress'),
    value: t('mobile.about.addressValue'),
    href: '#no-link',
    iconPath: 'M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z M15 11a3 3 0 11-6 0 3 3 0 016 0z',
    noLink: true,
  },
]);

useHead({
  title: t('mobile.about.seoTitle'),
  meta: [
    { name: 'description', content: t('mobile.about.seoDesc') },
  ],
});
</script>
