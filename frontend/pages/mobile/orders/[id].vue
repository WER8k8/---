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
      <template #default>
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
          <h1 class="ml-2 text-base font-semibold text-gray-900 truncate">
            {{ t('mobile.orders.detail') }}
          </h1>
        </div>
      </template>
    </MobileNavbar>

    <!-- Loading State -->
    <div
      v-if="pending"
      class="px-4 py-4 space-y-3"
    >
      <div class="bg-white rounded-2xl p-4 animate-pulse">
        <div class="h-6 bg-gray-200 rounded w-1/3 mb-3" />
        <div class="h-4 bg-gray-200 rounded w-1/2 mb-4" />
        <div class="space-y-2">
          <div class="h-16 bg-gray-200 rounded-lg" />
        </div>
      </div>
    </div>

    <!-- Error State -->
    <div
      v-else-if="error"
      class="px-4 py-20 text-center"
    >
      <div class="text-red-500 text-base font-medium mb-4">
        {{ t('mobile.orders.loadError') }}
      </div>
      <button
        class="mobile-btn-primary px-6 py-3 rounded-full"
        @click="router.back()"
      >
        {{ t('mobile.common.goBack') }}
      </button>
    </div>

    <!-- Order Detail -->
    <div
      v-else-if="order"
      class="pb-24"
    >
      <!-- Order Header -->
      <div class="px-4 py-4 bg-white">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-semibold text-gray-900">#{{ order.order_number }}</span>
          <span
            :class="[
              'px-2.5 py-1 rounded-full text-xs font-medium',
              order.status === 'completed' ? 'bg-green-100 text-green-800' :
              order.status === 'paid' ? 'bg-blue-100 text-blue-800' :
              order.status === 'shipped' ? 'bg-purple-100 text-purple-800' :
              order.status === 'cancelled' ? 'bg-red-100 text-red-800' :
              'bg-yellow-100 text-yellow-800'
            ]"
          >
            {{ getStatusText(order.status) }}
          </span>
        </div>
        <p class="text-xs text-gray-500">
          {{ formatDate(order.created_at) }}
        </p>
      </div>

      <!-- Order Items -->
      <div class="px-4 py-3 bg-white mt-2">
        <h3 class="text-sm font-semibold text-gray-900 mb-3">
          {{ t('mobile.orders.items') }}
        </h3>
        <div
          v-for="item in order.items"
          :key="item.id"
          class="flex items-center gap-3 py-3 border-b border-gray-100 last:border-b-0"
        >
          <img
            :src="item.product_image || '/images/placeholder.jpg'"
            :alt="item.product_name"
            class="w-12 h-12 rounded-lg object-cover flex-shrink-0"
          >
          <div class="flex-1 min-w-0">
            <h4 class="text-sm font-medium text-gray-900 truncate">
              {{ item.product_name }}
            </h4>
            <p class="text-xs text-gray-500">
              Qty: {{ item.quantity }} {{ item.unit }}
            </p>
          </div>
          <div class="text-sm font-semibold text-gray-900 flex-shrink-0">
            ${{ item.price }}
          </div>
        </div>
        <div class="flex items-center justify-between pt-3 border-t border-gray-100 mt-2">
          <span class="text-sm text-gray-500">{{ t('mobile.orders.total') }}</span>
          <span class="text-lg font-bold text-blue-600">${{ order.total_amount }}</span>
        </div>
      </div>

      <!-- Shipping Address -->
      <div
        v-if="order.shipping_address"
        class="px-4 py-3 bg-white mt-2"
      >
        <h3 class="text-sm font-semibold text-gray-900 mb-2">
          {{ t('mobile.orders.shippingAddress') }}
        </h3>
        <p class="text-sm text-gray-700 font-medium">
          {{ order.shipping_address.recipient_name }}
        </p>
        <p class="text-sm text-gray-500">
          {{ order.shipping_address.phone }}
        </p>
        <p class="text-sm text-gray-500">
          {{ order.shipping_address.country }} {{ order.shipping_address.province }} {{ order.shipping_address.city }}
        </p>
        <p class="text-sm text-gray-500">
          {{ order.shipping_address.street_address }}
        </p>
      </div>

      <!-- Order Status Timeline -->
      <div class="px-4 py-3 bg-white mt-2">
        <h3 class="text-sm font-semibold text-gray-900 mb-3">
          {{ t('mobile.orders.statusTimeline') }}
        </h3>
        <div class="relative">
          <div
            v-for="(status, idx) in orderStatusTimeline"
            :key="idx"
            class="relative pl-8 pb-4 last:pb-0"
          >
            <div
              v-if="idx < orderStatusTimeline.length - 1"
              class="absolute left-3 top-3 bottom-0 w-0.5"
              :class="status.completed ? 'bg-blue-500' : 'bg-gray-200'"
            />
            <div
              :class="[
                'absolute left-0 top-1 w-6 h-6 rounded-full flex items-center justify-center text-xs',
                status.completed ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-500'
              ]"
            >
              <svg
                v-if="status.completed"
                class="w-3 h-3"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M5 13l4 4L19 7" />
              </svg>
              <span v-else>{{ idx + 1 }}</span>
            </div>
            <div>
              <p
                class="text-sm font-medium"
                :class="status.completed ? 'text-gray-900' : 'text-gray-500'"
              >
                {{ status.label }}
              </p>
              <p
                v-if="status.timestamp"
                class="text-xs text-gray-400"
              >
                {{ formatDate(status.timestamp) }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Logistics (if available) -->
      <div
        v-if="order.logistics"
        class="px-4 py-3 bg-white mt-2"
      >
        <h3 class="text-sm font-semibold text-gray-900 mb-3">
          {{ t('mobile.orders.logistics') }}
        </h3>
        <p class="text-sm text-gray-600">
          {{ t('mobile.orders.trackingNumber') }}: {{ order.logistics.tracking_number }}
        </p>
        <p class="text-sm text-gray-600">
          {{ t('mobile.orders.carrier') }}: {{ order.logistics.carrier }}
        </p>
      </div>

      <!-- Action Buttons -->
      <div class="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4 z-40 space-y-2">
        <button
          v-if="order.status === 'pending'"
          class="w-full mobile-btn-primary py-3.5 rounded-xl font-semibold text-base"
          @click="payOrder"
        >
          {{ t('mobile.orders.payNow') }}
        </button>
        <button
          v-if="order.status === 'pending'"
          class="w-full py-3 rounded-xl font-semibold text-base border-2 border-red-300 text-red-500"
          @click="cancelOrder"
        >
          {{ t('mobile.orders.cancel') }}
        </button>
        <button
          v-if="order.status === 'shipped'"
          class="w-full mobile-btn-primary py-3.5 rounded-xl font-semibold text-base"
          @click="confirmReceipt"
        >
          {{ t('mobile.orders.confirmReceipt') }}
        </button>
      </div>
    </div>

    <!-- Mobile Tab Bar -->
    <MobileTabBar />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';

const route = useRoute();
const router = useRouter();
const { t } = useI18n();

// Fetch order data
const { data: order, pending, error } = await useFetch(() => `/api/v1/orders/${route.params.id}`, {
  key: () => `mobile-order-${route.params.id}`,
  lazy: true,
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`,
  },
  onResponse: (ctx) => {
    if (ctx.response?.status === 404) {
      throw new Error(t('mobile.orders.notFound'));
    }
  },
  onRequestError: (ctx) => {
    throw new Error(ctx.error?.message || t('mobile.orders.loadError'));
  }
});

// Order status timeline
const orderStatusTimeline = computed(() => {
  if (!order.value) return [];
  const statuses = [
    { key: 'pending', label: t('mobile.orders.status.pending'), timestamp: order.value.created_at },
    { key: 'paid', label: t('mobile.orders.status.paid'), timestamp: order.value.paid_at },
    { key: 'shipped', label: t('mobile.orders.status.shipped'), timestamp: order.value.shipped_at },
    { key: 'completed', label: t('mobile.orders.status.completed'), timestamp: order.value.completed_at },
  ];
  const statusOrder = ['pending', 'paid', 'shipped', 'completed'];
  const currentIdx = statusOrder.indexOf(order.value.status);
  return statuses.map((s, idx) => ({
    ...s,
    completed: idx <= currentIdx || !!s.timestamp,
  }));
});

// Get status text
const getStatusText = (status: string): string => {
  const map: Record<string, string> = {
    pending: t('mobile.orders.status.pending'),
    paid: t('mobile.orders.status.paid'),
    shipped: t('mobile.orders.status.shipped'),
    completed: t('mobile.orders.status.completed'),
    cancelled: t('mobile.orders.status.cancelled'),
  };
  return map[status] || status;
};

// Format date
const formatDate = (dateStr: string): string => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
};

// Pay order
const payOrder = () => {
  router.push(`/mobile/payment/checkout?order_id=${route.params.id}`);
};

// Cancel order
const cancelOrder = async () => {
  if (!confirm(t('mobile.orders.confirmCancel'))) return;
  try {
    await fetch(`/api/v1/orders/${route.params.id}/cancel`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    window.location.reload();
  } catch (err) {
    console.error('Failed to cancel order:', err);
    alert(t('mobile.orders.cancelFailed'));
  }
};

// Confirm receipt
const confirmReceipt = async () => {
  if (!confirm(t('mobile.orders.confirmReceiptConfirm'))) return;
  try {
    await fetch(`/api/v1/orders/${route.params.id}/confirm-receipt`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    window.location.reload();
  } catch (err) {
    console.error('Failed to confirm receipt:', err);
    alert(t('mobile.orders.confirmFailed'));
  }
};

// Page meta
useHead({
  title: computed(() => order.value ? `#${order.value.order_number}` : t('mobile.orders.detail')),
});
</script>
