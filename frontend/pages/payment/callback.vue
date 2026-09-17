/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="payment-callback-page">
    <!-- Loading State -->
    <div v-if="verifying" class="min-h-screen flex items-center justify-center bg-gray-50">
      <div class="text-center">
        <div class="animate-spin rounded-full h-16 w-16 border-b-2 border-primary mx-auto mb-4"></div>
        <p class="text-lg text-text-secondary">正在验证支付结果...</p>
      </div>
    </div>

    <!-- Payment Success -->
    <div v-else-if="paymentStatus === 'success'" class="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div class="max-w-md w-full bg-white rounded-2xl shadow-card p-8 sm:p-10 text-center">
        <!-- Success Icon -->
        <div class="w-20 h-20 mx-auto mb-6 rounded-full bg-green-100 flex items-center justify-center">
          <svg class="w-10 h-10 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>

        <h1 class="text-2xl sm:text-3xl font-bold text-text-primary mb-2">支付成功！</h1>
        <p class="text-text-secondary mb-6">您的订单已支付成功，我们将尽快为您处理</p>

        <!-- Order Summary -->
        <div v-if="order" class="bg-gray-50 rounded-xl p-4 sm:p-6 mb-6 text-left">
          <h2 class="text-base font-semibold text-text-primary mb-3">订单摘要</h2>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-text-secondary">订单号</span>
              <span class="font-medium text-text-primary">{{ order.order_number }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-text-secondary">商品数量</span>
              <span class="font-medium text-text-primary">{{ order.items?.length || 0 }} 件</span>
            </div>
            <div class="flex justify-between">
              <span class="text-text-secondary">支付金额</span>
              <span class="font-bold text-primary">${{ order.total_amount }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-text-secondary">支付方式</span>
              <span class="font-medium text-text-primary">{{ getPaymentMethodText(order.payment_method) }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-text-secondary">支付时间</span>
              <span class="font-medium text-text-primary">{{ formatDate(paymentTime) }}</span>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="space-y-3">
          <NuxtLink
            v-if="order"
            :to="`/orders/${order.id}`"
            class="block w-full btn-primary text-center"
          >
            查看订单详情
          </NuxtLink>
          <NuxtLink
            to="/products"
            class="block w-full px-4 py-3 border-2 border-primary text-primary font-semibold rounded-xl hover:bg-primary/10 transition-all duration-300 text-center"
          >
            继续购物
          </NuxtLink>
        </div>
      </div>
    </div>

    <!-- Payment Failed -->
    <div v-else-if="paymentStatus === 'failed'" class="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div class="max-w-md w-full bg-white rounded-2xl shadow-card p-8 sm:p-10 text-center">
        <!-- Failed Icon -->
        <div class="w-20 h-20 mx-auto mb-6 rounded-full bg-red-100 flex items-center justify-center">
          <svg class="w-10 h-10 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>

        <h1 class="text-2xl sm:text-3xl font-bold text-text-primary mb-2">支付失败</h1>
        <p class="text-text-secondary mb-2">{{ errorMessage || '支付过程中出现问题，请重试' }}</p>
        <p v-if="errorCode" class="text-xs text-text-secondary mb-6">错误代码: {{ errorCode }}</p>

        <!-- Action Buttons -->
        <div class="space-y-3">
          <button
            v-if="orderId"
            @click="retryPayment"
            class="w-full btn-primary text-center"
          >
            重新支付
          </button>
          <NuxtLink
            to="/orders"
            class="block w-full px-4 py-3 border-2 border-primary text-primary font-semibold rounded-xl hover:bg-primary/10 transition-all duration-300 text-center"
          >
            返回订单列表
          </NuxtLink>
        </div>
      </div>
    </div>

    <!-- Payment Pending -->
    <div v-else-if="paymentStatus === 'pending'" class="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div class="max-w-md w-full bg-white rounded-2xl shadow-card p-8 sm:p-10 text-center">
        <!-- Pending Icon -->
        <div class="w-20 h-20 mx-auto mb-6 rounded-full bg-yellow-100 flex items-center justify-center">
          <svg class="w-10 h-10 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>

        <h1 class="text-2xl sm:text-3xl font-bold text-text-primary mb-2">支付处理中</h1>
        <p class="text-text-secondary mb-6">您的支付正在处理中，请稍后查看订单状态</p>

        <!-- Action Buttons -->
        <div class="space-y-3">
          <NuxtLink
            v-if="orderId"
            :to="`/orders/${orderId}`"
            class="block w-full btn-primary text-center"
          >
            查看订单状态
          </NuxtLink>
          <NuxtLink
            to="/orders"
            class="block w-full px-4 py-3 border-2 border-primary text-primary font-semibold rounded-xl hover:bg-primary/10 transition-all duration-300 text-center"
          >
            返回订单列表
          </NuxtLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();

const verifying = ref(true);
const paymentStatus = ref<'success' | 'failed' | 'pending' | null>(null);
const order = ref<any>(null);
const orderId = ref<string | null>(null);
const paymentTime = ref<string | null>(null);
const errorMessage = ref<string | null>(null);
const errorCode = ref<string | null>(null);

// 验证支付结果
const verifyPayment = async () => {
  verifying.value = true;
  try {
    const query = route.query;
    const paymentId = query.payment_id as string;
    const orderIdParam = query.order_id as string;
    const status = query.status as string; // success, failed, pending

    // 如果有 status 参数，直接使用（模拟支付回调）
    if (status) {
      paymentStatus.value = status as 'success' | 'failed' | 'pending';
      if (orderIdParam) {
        orderId.value = orderIdParam;
        await fetchOrder(orderIdParam);
      }
      verifying.value = false;
      return;
    }

    // 否则调用后端验证支付结果
    const params = new URLSearchParams();
    if (paymentId) params.append('payment_id', paymentId);
    if (orderIdParam) params.append('order_id', orderIdParam);

    const response = await fetch(`http://localhost:8000/api/v1/payments/callback?${params}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });

    if (response.ok) {
      const data = await response.json();
      paymentStatus.value = data.status; // success, failed, pending
      paymentTime.value = data.payment_time;
      errorMessage.value = data.error_message;
      errorCode.value = data.error_code;

      if (data.order_id) {
        orderId.value = data.order_id;
        await fetchOrder(data.order_id);
      }
    } else {
      paymentStatus.value = 'failed';
      errorMessage.value = '验证支付结果失败';
    }
  } catch (err: any) {
    paymentStatus.value = 'failed';
    errorMessage.value = err.message || '验证支付结果失败';
  } finally {
    verifying.value = false;
  }
};

// 获取订单信息
const fetchOrder = async (id: string) => {
  try {
    const response = await fetch(`http://localhost:8000/api/v1/orders/${id}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    if (response.ok) {
      const data = await response.json();
      order.value = data;
    }
  } catch (err) {
    console.error('Failed to fetch order:', err);
  }
};

// 重新支付
const retryPayment = () => {
  if (orderId.value) {
    router.push(`/payment/checkout?order_id=${orderId.value}`);
  }
};

// 获取支付方式文本
const getPaymentMethodText = (method: string) => {
  switch (method) {
    case 'alipay': return '支付宝';
    case 'wechat_pay': return '微信支付';
    case 'credit_card': return '信用卡';
    case 'bank_transfer': return '银行转账';
    case 'paypal': return 'PayPal';
    default: return method || '未知';
  }
};

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return '-';
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

// SEO元数据
useHead({
  title: computed(() => {
    if (paymentStatus.value === 'success') return '支付成功 - 建材B2B外贸平台';
    if (paymentStatus.value === 'failed') return '支付失败 - 建材B2B外贸平台';
    return '支付结果 - 建材B2B外贸平台';
  }),
  meta: [
    { name: 'description', content: '查看支付结果和订单信息' },
  ],
});

onMounted(() => {
  verifyPayment();
});
</script>

<style scoped>
.btn-primary {
  @apply inline-flex items-center justify-center px-6 py-3 bg-primary text-white font-semibold rounded-xl hover:bg-primary-700 transition-all duration-300;
}
</style>
