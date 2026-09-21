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
          {{ $t('mobile.user.myOrders') }}
        </h1>
      </div>
    </MobileNavbar>

    <!-- Loading State -->
    <div
      v-if="pending"
      class="px-4 py-6 space-y-4"
    >
      <div
        v-for="i in 3"
        :key="i"
        class="animate-pulse bg-white rounded-2xl p-4"
      >
        <div class="h-5 bg-gray-200 rounded w-1/3 mb-3" />
        <div class="h-4 bg-gray-200 rounded w-1/2 mb-2" />
        <div class="h-4 bg-gray-200 rounded w-3/4" />
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-else-if="orders.length === 0"
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
        {{ $t('mobile.orders.noOrders') }}
      </h3>
      <p class="text-sm text-gray-500 mb-6">
        {{ $t('mobile.orders.noOrdersDesc') }}
      </p>
      <NuxtLink
        to="/mobile/products"
        class="mobile-btn-primary px-6 py-3 rounded-full inline-block"
      >
        {{ $t('mobile.orders.browseProducts') }}
      </NuxtLink>
    </div>

    <!-- Orders List -->
    <div
      v-else
      class="px-4 py-4 space-y-4"
    >
      <div
        v-for="order in orders"
        :key="order.id"
        class="bg-white rounded-2xl p-4 shadow-sm"
      >
        <!-- Order Header -->
        <div class="flex items-center justify-between mb-3">
          <span class="text-sm font-semibold text-gray-900">#{{ order.order_number }}</span>
          <span
            :class="[
              'px-2.5 py-1 rounded-full text-xs font-medium',
              order.status === 'completed' ? 'bg-green-100 text-green-800' :
              order.status === 'processing' ? 'bg-blue-100 text-blue-800' :
              order.status === 'cancelled' ? 'bg-red-100 text-red-800' :
              'bg-yellow-100 text-yellow-800'
            ]"
          >
            {{ $t(`mobile.orders.status.${order.status}`) }}
          </span>
        </div>

        <!-- Order Items -->
        <div
          v-if="order.items && order.items.length > 0"
          class="space-y-2 mb-3"
        >
          <div
            v-for="item in order.items.slice(0, 2)"
            :key="item.id"
            class="flex items-center gap-3"
          >
            <img
              :src="item.product_image || '/images/placeholder.jpg'"
              :alt="item.product_name"
              class="w-10 h-10 rounded-lg object-cover flex-shrink-0"
            >
            <div class="flex-1 min-w-0">
              <h4 class="text-sm font-medium text-gray-900 truncate">
                {{ item.product_name }}
              </h4>
              <p class="text-xs text-gray-500">
                Qty: {{ item.quantity }}
              </p>
            </div>
          </div>
          <p
            v-if="order.items.length > 2"
            class="text-xs text-gray-500 pl-13"
          >
            +{{ order.items.length - 2 }} {{ $t('mobile.orders.moreItems') }}
          </p>
        </div>

        <!-- Order Total -->
        <div class="flex items-center justify-between pt-3 border-t border-gray-100">
          <span class="text-sm text-gray-500">{{ $t('mobile.orders.total') }}</span>
          <span class="text-base font-bold text-blue-600">${{ order.total_amount }}</span>
        </div>

        <!-- View Detail -->
        <NuxtLink
          :to="`/mobile/orders/${order.id}`"
          class="mt-3 block text-center mobile-btn-outline py-2.5 rounded-xl text-sm font-medium"
        >
          {{ $t('mobile.orders.viewDetail') }}
        </NuxtLink>
      </div>
    </div>

    <!-- Mobile Tab Bar -->
    <MobileTabBar />
  </div>
</template>

<script setup lang="ts">
const router = useRouter();
const { $t } = useI18n();

// Fetch user orders
const { data: orders, pending, error } = await useFetch('/api/user/orders', {
  key: 'mobile-user-orders',
  lazy: true,
});

// Page meta
useHead({
  title: $t('mobile.user.myOrders'),
});
</script>
