/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
    <!-- Loading State -->
    <div v-if="verifying" class="text-center">
      <div class="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
      <p class="text-base text-gray-600">{{ $t('mobile.payment.verifying') }}</p>
    </div>

    <!-- Success State -->
    <div v-else-if="status === 'success'" class="text-center max-w-sm w-full">
      <div class="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
        <svg class="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <h1 class="text-2xl font-bold text-gray-900 mb-2">{{ $t('mobile.payment.successTitle') }}</h1>
      <p class="text-base text-gray-600 mb-8">{{ $t('mobile.payment.successDesc') }}</p>

      <div class="space-y-3">
        <NuxtLink
          to="/mobile/orders"
          class="mobile-btn-primary w-full py-3.5 rounded-xl font-semibold text-base text-center block"
        >
          {{ $t('mobile.payment.viewOrders') }}
        </NuxtLink>
        <NuxtLink
          to="/mobile"
          class="mobile-btn-outline w-full py-3.5 rounded-xl font-semibold text-base text-center block"
        >
          {{ $t('mobile.payment.backHome') }}
        </NuxtLink>
      </div>
    </div>

    <!-- Failure State -->
    <div v-else-if="status === 'failure'" class="text-center max-w-sm w-full">
      <div class="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
        <svg class="w-10 h-10 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </div>
      <h1 class="text-2xl font-bold text-gray-900 mb-2">{{ $t('mobile.payment.failureTitle') }}</h1>
      <p class="text-base text-gray-600 mb-8">{{ $t('mobile.payment.failureDesc') }}</p>

      <div class="space-y-3">
        <button
          class="mobile-btn-primary w-full py-3.5 rounded-xl font-semibold text-base"
          @click="retryPayment"
        >
          {{ $t('mobile.payment.retry') }}
        </button>
        <NuxtLink
          to="/mobile"
          class="mobile-btn-outline w-full py-3.5 rounded-xl font-semibold text-base text-center block"
        >
          {{ $t('mobile.payment.backHome') }}
        </NuxtLink>
      </div>
    </div>

    <!-- Pending State -->
    <div v-else class="text-center max-w-sm w-full">
      <div class="w-20 h-20 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-6">
        <svg class="w-10 h-10 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <h1 class="text-2xl font-bold text-gray-900 mb-2">{{ $t('mobile.payment.pendingTitle') }}</h1>
      <p class="text-base text-gray-600 mb-8">{{ $t('mobile.payment.pendingDesc') }}</p>

      <NuxtLink
        to="/mobile"
        class="mobile-btn-primary w-full py-3.5 rounded-xl font-semibold text-base text-center block"
      >
        {{ $t('mobile.payment.backHome') }}
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute();
const { $t } = useI18n();

const status = ref<'success' | 'failure' | 'pending'>('pending');
const verifying = ref(true);

// Verify payment status
onMounted(async () => {
  try {
    const result = await $fetch('/api/payment/verify', {
      params: {
        order_id: route.query.order_id,
        payment_id: route.query.payment_id,
      }
    });
    status.value = result.status || 'pending';
  } catch (err) {
    status.value = 'failure';
  } finally {
    verifying.value = false;
  }
});

// Retry payment
const retryPayment = () => {
  window.location.reload();
};

// Page meta
useHead({
  title: $t('mobile.payment.title'),
});
</script>
