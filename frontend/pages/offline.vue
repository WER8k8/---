/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 px-4">
    <div class="max-w-md w-full text-center">
      <!-- Offline Icon -->
      <div class="mb-8">
        <div class="mx-auto w-24 h-24 bg-yellow-100 rounded-full flex items-center justify-center">
          <svg
            class="w-12 h-12 text-yellow-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
      </div>

      <!-- Title -->
      <h1 class="text-3xl font-bold text-gray-900 mb-4">
        {{ $t('offline.title', '您已离线') }}
      </h1>

      <!-- Description -->
      <p class="text-gray-600 mb-8">
        {{ $t('offline.description', '请检查您的网络连接，然后重试') }}
      </p>

      <!-- Actions -->
      <div class="space-y-4">
        <button
          @click="retry"
          class="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          {{ $t('offline.retry', '重试') }}
        </button>

        <button
          @click="goHome"
          class="w-full bg-gray-200 text-gray-800 py-3 px-6 rounded-lg font-medium hover:bg-gray-300 transition-colors"
        >
          {{ $t('offline.goHome', '返回首页') }}
        </button>
      </div>

      <!-- Features available offline -->
      <div class="mt-12 pt-8 border-t border-gray-200">
        <p class="text-sm text-gray-500 mb-4">
          {{ $t('offline.availableFeatures', '离线时仍可使用以下功能：') }}
        </p>
        <div class="grid grid-cols-2 gap-4 text-sm text-gray-600">
          <div class="flex items-center justify-center space-x-2">
            <svg
              class="w-4 h-4 text-green-500"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fill-rule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clip-rule="evenodd"
              />
            </svg>
            <span>{{ $t('offline.feature1', '查看缓存产品') }}</span>
          </div>
          <div class="flex items-center justify-center space-x-2">
            <svg
              class="w-4 h-4 text-green-500"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fill-rule="evenodd"
                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                clip-rule="evenodd"
              />
            </svg>
            <span>{{ $t('offline.feature2', '阅读已加载文章') }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { SITE_CONFIG } from '~/config/site';

// Page meta
useHead({
  title: `离线模式 - ${SITE_CONFIG.name}`,
  meta: [
    { name: 'description', content: '您当前处于离线状态，请检查网络连接' },
    { name: 'robots', content: 'noindex, nofollow' },
  ],
});

// Retry connection
const retry = () => {
  window.location.reload();
};

// Go to home page
const goHome = () => {
  navigateTo('/');
};

// Check online status on mount
onMounted(() => {
  window.addEventListener('online', () => {
    // Auto reload when back online
    window.location.reload();
  });
});
</script>

<style scoped>
/* Ensure full height */
.min-h-screen {
  min-height: 100vh;
}
</style>
