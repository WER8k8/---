/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="min-h-screen bg-gray-50 pb-safe-bottom">
    <!-- Mobile Navbar -->
    <MobileNavbar
      safe-area-top
      :blur="true"
    >
      <div class="flex items-center h-14">
        <button
          class="p-2 -ml-2 rounded-lg hover:bg-gray-100 transition-colors"
          @click="router.back()"
        >
          <svg
            class="w-5 h-5 text-gray-700"
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
        </button>
        <h1 class="ml-2 text-base font-semibold text-gray-900">
          {{ $t('mobile.logistics.title') }}
        </h1>
      </div>
    </MobileNavbar>

    <!-- Search Order -->
    <div class="px-4 py-4">
      <div class="bg-white rounded-2xl p-4 shadow-sm">
        <div class="flex gap-3">
          <input
            v-model="trackingNumber"
            type="text"
            :placeholder="$t('mobile.logistics.trackingPlaceholder')"
            class="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            @keyup.enter="trackOrder"
          >
          <button
            class="mobile-btn-primary px-5 py-3 rounded-xl font-medium text-sm"
            :disabled="!trackingNumber"
            @click="trackOrder"
          >
            {{ $t('mobile.logistics.track') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div
      v-if="pending"
      class="px-4 py-6"
    >
      <div class="animate-pulse bg-white rounded-2xl p-4">
        <div class="h-6 bg-gray-200 rounded w-1/3 mb-4" />
        <div class="space-y-3">
          <div class="h-4 bg-gray-200 rounded w-full" />
          <div class="h-4 bg-gray-200 rounded w-3/4" />
        </div>
      </div>
    </div>

    <!-- Tracking Result -->
    <div
      v-else-if="trackingResult"
      class="px-4 pb-4"
    >
      <!-- Order Info -->
      <div class="bg-white rounded-2xl p-4 shadow-sm mb-4">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-sm font-semibold text-gray-900">
            {{ $t('mobile.logistics.orderInfo') }}
          </h2>
          <span
            :class="[
              'px-2.5 py-1 rounded-full text-xs font-medium',
              trackingResult.status === 'delivered' ? 'bg-green-100 text-green-800' :
              trackingResult.status === 'in_transit' ? 'bg-blue-100 text-blue-800' :
              'bg-yellow-100 text-yellow-800'
            ]"
          >
            {{ $t(`mobile.logistics.status.${trackingResult.status}`) }}
          </span>
        </div>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between">
            <span class="text-gray-500">{{ $t('mobile.logistics.orderNo') }}</span>
            <span class="text-gray-900 font-medium">{{ trackingResult.order_number }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-500">{{ $t('mobile.logistics.carrier') }}</span>
            <span class="text-gray-900">{{ trackingResult.carrier }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-500">{{ $t('mobile.logistics.estimatedDelivery') }}</span>
            <span class="text-gray-900">{{ trackingResult.estimated_delivery }}</span>
          </div>
        </div>
      </div>

      <!-- Tracking Timeline -->
      <div class="bg-white rounded-2xl p-4 shadow-sm">
        <h2 class="text-sm font-semibold text-gray-900 mb-4">
          {{ $t('mobile.logistics.timeline') }}
        </h2>
        <div class="space-y-4">
          <div
            v-for="(event, idx) in trackingResult.events"
            :key="idx"
            class="flex gap-3"
          >
            <!-- Timeline Dot -->
            <div class="flex flex-col items-center">
              <div
                :class="[
                  'w-3 h-3 rounded-full flex-shrink-0',
                  idx === 0 ? 'bg-blue-600' : 'bg-gray-300'
                ]"
              />
              <div
                v-if="idx < trackingResult.events.length - 1"
                class="w-0.5 h-full bg-gray-200 mt-1"
              />
            </div>
            <!-- Event Content -->
            <div class="flex-1 pb-4">
              <p class="text-sm font-medium text-gray-900">
                {{ event.description }}
              </p>
              <p class="text-xs text-gray-500 mt-1">
                {{ event.location }}
              </p>
              <p class="text-xs text-gray-400 mt-0.5">
                {{ new Date(event.timestamp).toLocaleString() }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State (no search yet) -->
    <div
      v-else-if="!trackingNumber && !trackingResult"
      class="px-4 py-20 text-center"
    >
      <svg
        class="w-16 h-16 mx-auto text-gray-300 mb-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
        />
      </svg>
      <h3 class="text-base font-medium text-gray-900 mb-2">
        {{ $t('mobile.logistics.noTracking') }}
      </h3>
      <p class="text-sm text-gray-500">
        {{ $t('mobile.logistics.noTrackingDesc') }}
      </p>
    </div>

    <!-- Not Found State -->
    <div
      v-else-if="trackingSearched && !trackingResult"
      class="px-4 py-20 text-center"
    >
      <svg
        class="w-16 h-16 mx-auto text-gray-300 mb-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <h3 class="text-base font-medium text-gray-900 mb-2">
        {{ $t('mobile.logistics.notFound') }}
      </h3>
      <p class="text-sm text-gray-500">
        {{ $t('mobile.logistics.notFoundDesc') }}
      </p>
    </div>

    <!-- Mobile Tab Bar -->
    <MobileTabBar />
  </div>
</template>

<script setup lang="ts">
const router = useRouter();
const { $t } = useI18n();

const trackingNumber = ref('');
const trackingResult = ref(null);
const trackingSearched = ref(false);
const pending = ref(false);

// Track order
const trackOrder = async () => {
  if (!trackingNumber.value) return;

  pending.value = true;
  trackingSearched.value = true;
  try {
    const result = await $fetch('/api/logistics/track', {
      params: { number: trackingNumber.value }
    });
    trackingResult.value = result;
  } catch (err) {
    trackingResult.value = null;
  } finally {
    pending.value = false;
  }
};

// Page meta
useHead({
  title: $t('mobile.logistics.title'),
});
</script>
