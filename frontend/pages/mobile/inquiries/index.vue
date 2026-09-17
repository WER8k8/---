/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="min-h-screen bg-gray-50 pb-safe-bottom">
    <!-- Mobile Navbar -->
    <MobileNavbar safe-area-top :blur="true">
      <div class="flex items-center justify-between h-14">
        <h1 class="text-base font-semibold text-gray-900">{{ $t('mobile.inquiries.title') }}</h1>
        <NuxtLink
          to="/mobile/contact"
          class="mobile-btn-primary px-4 py-2 rounded-lg text-sm font-medium"
        >
          {{ $t('mobile.inquiries.new') }}
        </NuxtLink>
      </div>
    </MobileNavbar>

    <!-- Loading State -->
    <div v-if="pending" class="px-4 py-6 space-y-4">
      <div v-for="i in 3" :key="i" class="animate-pulse bg-white rounded-2xl p-4">
        <div class="h-5 bg-gray-200 rounded w-1/3 mb-3"></div>
        <div class="h-4 bg-gray-200 rounded w-1/2"></div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="inquiries.length === 0" class="px-4 py-20 text-center">
      <svg class="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
      </svg>
      <h3 class="text-base font-medium text-gray-900 mb-2">{{ $t('mobile.inquiries.noInquiries') }}</h3>
      <p class="text-sm text-gray-500 mb-6">{{ $t('mobile.inquiries.noInquiriesDesc') }}</p>
      <NuxtLink to="/mobile/contact" class="mobile-btn-primary px-6 py-3 rounded-full inline-block">
        {{ $t('mobile.inquiries.contactNow') }}
      </NuxtLink>
    </div>

    <!-- Inquiries List -->
    <div v-else class="px-4 py-4 space-y-4">
      <div
        v-for="inquiry in inquiries"
        :key="inquiry.id"
        class="bg-white rounded-2xl p-4 shadow-sm"
      >
        <!-- Inquiry Header -->
        <div class="flex items-center justify-between mb-3">
          <span class="text-sm font-semibold text-gray-900">#{{ inquiry.inquiry_number }}</span>
          <span
            :class="[
              'px-2.5 py-1 rounded-full text-xs font-medium',
              inquiry.status === 'replied' ? 'bg-green-100 text-green-800' :
              inquiry.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
              'bg-gray-100 text-gray-800'
            ]"
          >
            {{ $t(`mobile.inquiries.status.${inquiry.status}`) }}
          </span>
        </div>

        <!-- Inquiry Product -->
        <div v-if="inquiry.product_name" class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0">
            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
          </div>
          <div class="flex-1 min-w-0">
            <h4 class="text-sm font-medium text-gray-900 truncate">{{ inquiry.product_name }}</h4>
            <p class="text-xs text-gray-500">{{ $t('mobile.inquiries.quantity') }}: {{ inquiry.quantity }}</p>
          </div>
        </div>

        <!-- Inquiry Message Preview -->
        <p v-if="inquiry.message" class="text-sm text-gray-600 mb-3 line-clamp-2">{{ inquiry.message }}</p>

        <!-- Date -->
        <div class="flex items-center justify-between pt-3 border-t border-gray-100">
          <span class="text-xs text-gray-500">{{ new Date(inquiry.created_at).toLocaleDateString() }}</span>
          <NuxtLink
            :to="`/mobile/inquiries/${inquiry.id}`"
            class="text-sm text-blue-600 font-medium"
          >
            {{ $t('mobile.inquiries.viewDetail') }}
          </NuxtLink>
        </div>
      </div>
    </div>

    <!-- Mobile Tab Bar -->
    <MobileTabBar />
  </div>
</template>

<script setup lang="ts">
const { $t } = useI18n();

// Fetch inquiries
const { data: inquiries, pending, error } = await useFetch('/api/inquiries', {
  key: 'mobile-inquiries',
  lazy: true,
});

// Page meta
useHead({
  title: $t('mobile.inquiries.title'),
});
</script>
