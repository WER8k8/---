/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="orders-page">
    <!-- Hero Section -->
    <section class="bg-gradient-to-br from-primary/5 via-surface to-accent/5 py-10 sm:py-14 lg:py-20">
      <div class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 text-center">
        <h1 class="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary mb-3 sm:mb-4">
          {{ t('orders.title') }}
        </h1>
        <p class="text-xs sm:text-sm md:text-base lg:text-xl text-text-secondary max-w-2xl mx-auto">
          {{ t('orders.subtitle') }}
        </p>
      </div>
    </section>

    <!-- Orders List -->
    <section class="py-8 sm:py-10 lg:py-14">
      <div class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8">
        <!-- Loading State -->
        <div v-if="loading" class="space-y-4">
          <div v-for="i in 3" :key="i" class="animate-pulse bg-surface rounded-2xl p-6">
            <div class="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div class="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
            <div class="h-4 bg-gray-200 rounded w-3/4"></div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else-if="orders.length === 0" class="text-center py-10 sm:py-16">
          <svg class="w-16 h-16 sm:w-20 sm:h-20 mx-auto text-text-secondary mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
          <h3 class="text-lg sm:text-xl font-semibold text-text-primary mb-2">{{ t('orders.noOrders') }}</h3>
          <p class="text-sm text-text-secondary mb-6">{{ t('orders.noOrdersDesc') }}</p>
          <NuxtLink to="/products" class="btn-primary">
            {{ t('orders.browseProducts') }}
          </NuxtLink>
        </div>

        <!-- Orders Grid -->
        <div v-else class="space-y-6">
          <div
            v-for="order in orders"
            :key="order.id"
            class="bg-surface rounded-2xl shadow-card p-6 sm:p-8 hover:shadow-card-hover transition-all duration-300"
          >
            <div class="flex flex-col sm:flex-row sm:items-center justify-between mb-4 sm:mb-6">
              <div>
                <h3 class="text-lg sm:text-xl font-semibold text-text-primary mb-1">
                  {{ t('orders.orderNumber') }}: {{ order.order_number }}
                </h3>
                <p class="text-sm text-text-secondary">
                  {{ t('orders.createdAt') }}: {{ new Date(order.created_at).toLocaleDateString() }}
                </p>
              </div>
              <div class="mt-2 sm:mt-0">
                <span
                  :class="[
                    'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium',
                    order.status === 'completed' ? 'bg-green-100 text-green-800' :
                    order.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                    order.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                  ]"
                >
                  {{ t(`orders.status.${order.status}`) }}
                </span>
              </div>
            </div>

            <!-- Order Items -->
            <div class="border-t border-border pt-4 sm:pt-6">
              <div
                v-for="item in order.items"
                :key="item.id"
                class="flex items-center gap-4 py-3 sm:py-4 border-b border-border last:border-b-0"
              >
                <img
                  :src="item.product_image || '/images/placeholder.jpg'"
                  :alt="item.product_name"
                  class="w-12 h-12 sm:w-16 sm:h-16 object-cover rounded-lg"
                />
                <div class="flex-1 min-w-0">
                  <h4 class="text-sm sm:text-base font-medium text-text-primary truncate">{{ item.product_name }}</h4>
                  <p class="text-xs sm:text-sm text-text-secondary">
                    {{ t('orders.quantity') }}: {{ item.quantity }} {{ item.unit }}
                  </p>
                </div>
                <div class="text-sm sm:text-base font-semibold text-text-primary">
                  ${{ item.price }}
                </div>
              </div>
            </div>

            <!-- Order Total -->
            <div class="border-t border-border mt-4 sm:mt-6 pt-4 sm:pt-6 flex justify-between items-center">
              <span class="text-sm sm:text-base font-medium text-text-primary">{{ t('orders.total') }}</span>
              <span class="text-lg sm:text-xl font-bold text-primary">${{ order.total_amount }}</span>
            </div>

            <!-- Action Buttons -->
            <div class="mt-4 sm:mt-6 flex flex-wrap gap-3 sm:gap-4">
              <NuxtLink
                :to="`/orders/${order.id}`"
                class="btn-outline text-sm sm:text-base"
              >
                {{ t('orders.viewDetails') }}
              </NuxtLink>
              <button
                v-if="order.status === 'pending'"
                @click="cancelOrder(order.id)"
                class="text-sm sm:text-base text-red-500 hover:text-red-700 transition-colors"
              >
                {{ t('orders.cancelOrder') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

const { t } = useI18n();
const router = useRouter();

const orders = ref([]);
const loading = ref(true);

// 获取订单列表
const fetchOrders = async () => {
  try {
    loading.value = true;
    const response = await fetch('/api/v1/orders/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`, // 假设用JWT认证
      },
    });
    
    if (!response.ok) throw new Error('Failed to fetch orders');
    
    const data = await response.json();
    orders.value = data;
  } catch (err: any) {
    console.error('Failed to fetch orders:', err);
  } finally {
    loading.value = false;
  }
};

// 取消订单
const cancelOrder = async (orderId: string) => {
  if (!confirm(t('orders.confirmCancel'))) return;
  
  try {
    const response = await fetch(`/api/v1/orders/${orderId}/cancel`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    
    if (!response.ok) throw new Error('Failed to cancel order');
    
    // 刷新订单列表
    fetchOrders();
  } catch (err: any) {
    alert(err.message || 'Failed to cancel order');
  }
};

// SEO元数据
useHead({
  title: computed(() => `${t('orders.title')} - ${t('common.companyName')}`),
  meta: [
    { name: 'description', content: t('orders.subtitle') },
  ],
});

onMounted(() => {
  fetchOrders();
});
</script>

<style scoped>
.btn-primary {
  @apply inline-flex items-center justify-center px-6 py-3 bg-primary text-white font-semibold rounded-xl hover:bg-primary-700 transition-all duration-300;
}

.btn-outline {
  @apply inline-flex items-center justify-center px-4 py-2 border-2 border-primary text-primary font-medium rounded-lg hover:bg-primary/10 transition-all duration-300;
}
</style>
