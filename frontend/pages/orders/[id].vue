<template>
  <div class="order-detail-page">
    <!-- Loading State -->
    <div v-if="loading" class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 py-8 sm:py-12">
      <div class="animate-pulse">
        <div class="h-8 sm:h-10 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div class="h-4 sm:h-5 bg-gray-200 rounded w-1/2 mb-8"></div>
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-8">
          <div class="lg:col-span-2 space-y-4">
            <div class="h-40 bg-gray-200 rounded-2xl"></div>
            <div class="h-60 bg-gray-200 rounded-2xl"></div>
          </div>
          <div class="h-80 bg-gray-200 rounded-2xl"></div>
        </div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 py-8 sm:py-12 text-center">
      <div class="text-red-500 text-lg sm:text-xl font-semibold mb-4">{{ error }}</div>
      <button @click="fetchOrder" class="btn-primary">重试</button>
    </div>

    <!-- Order Detail -->
    <div v-else-if="order" class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 py-8 sm:py-12">
      <!-- Breadcrumb -->
      <nav class="mb-4 sm:mb-6">
        <ol class="flex items-center space-x-2 text-sm text-text-secondary">
          <li><NuxtLink to="/" class="hover:text-primary">首页</NuxtLink></li>
          <li>/</li>
          <li><NuxtLink to="/orders" class="hover:text-primary">订单列表</NuxtLink></li>
          <li>/</li>
          <li class="text-text-primary font-medium">{{ order.order_number }}</li>
        </ol>
      </nav>

      <!-- Order Header -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between mb-6 sm:mb-8">
        <div>
          <h1 class="text-2xl sm:text-3xl font-bold text-text-primary mb-2">
            订单 {{ order.order_number }}
          </h1>
          <p class="text-sm text-text-secondary">
            下单时间: {{ formatDate(order.created_at) }}
          </p>
        </div>
        <div class="mt-2 sm:mt-0">
          <span
            :class="[
              'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium',
              getStatusClass(order.status)
            ]"
          >
            {{ getStatusText(order.status) }}
          </span>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-8">
        <!-- Left Column -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Order Items -->
          <div class="bg-surface rounded-2xl shadow-card p-6 sm:p-8">
            <h2 class="text-lg sm:text-xl font-bold text-text-primary mb-4 sm:mb-6">商品清单</h2>
            <div
              v-for="item in order.items"
              :key="item.id"
              class="flex items-center gap-4 py-4 border-b border-border last:border-b-0"
            >
              <img
                :src="item.product_image || '/images/placeholder.jpg'"
                :alt="item.product_name"
                class="w-16 h-16 sm:w-20 sm:h-20 object-cover rounded-lg flex-shrink-0"
              />
              <div class="flex-1 min-w-0">
                <NuxtLink :to="`/products/${item.product_id}`">
                  <h4 class="text-sm sm:text-base font-medium text-text-primary hover:text-primary transition-colors truncate">
                    {{ item.product_name }}
                  </h4>
                </NuxtLink>
                <p class="text-xs sm:text-sm text-text-secondary mt-1">
                  数量: {{ item.quantity }} {{ item.unit }}
                </p>
                <p v-if="item.specs" class="text-xs text-text-secondary mt-1">
                  {{ item.specs }}
                </p>
              </div>
              <div class="text-sm sm:text-base font-semibold text-text-primary flex-shrink-0">
                ${{ item.price }}
              </div>
            </div>
            <div class="border-t border-border mt-4 pt-4 flex justify-between items-center">
              <span class="font-medium text-text-primary">订单总额</span>
              <span class="text-xl sm:text-2xl font-bold text-primary">${{ order.total_amount }}</span>
            </div>
          </div>

          <!-- Logistics Tracking -->
          <div v-if="order.logistics" class="bg-surface rounded-2xl shadow-card p-6 sm:p-8">
            <h2 class="text-lg sm:text-xl font-bold text-text-primary mb-4 sm:mb-6">物流跟踪</h2>
            <div class="mb-4">
              <p class="text-sm text-text-secondary">
                运单号: <span class="font-medium text-text-primary">{{ order.logistics.tracking_number }}</span>
              </p>
              <p class="text-sm text-text-secondary mt-1">
                物流公司: <span class="font-medium text-text-primary">{{ order.logistics.carrier }}</span>
              </p>
            </div>
            <!-- Logistics Timeline -->
            <div class="relative">
              <div
                v-for="(event, idx) in order.logistics.events"
                :key="idx"
                class="relative pl-8 pb-6 last:pb-0"
              >
                <!-- Timeline line -->
                <div
                  v-if="idx < order.logistics.events.length - 1"
                  class="absolute left-3 top-3 bottom-0 w-0.5 bg-gray-200"
                ></div>
                <!-- Timeline dot -->
                <div
                  :class="[
                    'absolute left-0 top-1 w-6 h-6 rounded-full flex items-center justify-center',
                    idx === 0 ? 'bg-primary text-white' : 'bg-gray-200 text-gray-500'
                  ]"
                >
                  <svg class="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <p class="text-sm font-medium text-text-primary">{{ event.description }}</p>
                  <p class="text-xs text-text-secondary mt-0.5">{{ formatDate(event.timestamp) }}</p>
                  <p v-if="event.location" class="text-xs text-text-secondary">{{ event.location }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Order Status Timeline -->
          <div class="bg-surface rounded-2xl shadow-card p-6 sm:p-8">
            <h2 class="text-lg sm:text-xl font-bold text-text-primary mb-4 sm:mb-6">订单状态</h2>
            <div class="relative">
              <div
                v-for="(status, idx) in orderStatusTimeline"
                :key="idx"
                class="relative pl-8 pb-6 last:pb-0"
              >
                <div
                  v-if="idx < orderStatusTimeline.length - 1"
                  class="absolute left-3 top-3 bottom-0 w-0.5"
                  :class="status.completed ? 'bg-primary' : 'bg-gray-200'"
                ></div>
                <div
                  :class="[
                    'absolute left-0 top-1 w-6 h-6 rounded-full flex items-center justify-center text-xs',
                    status.completed ? 'bg-primary text-white' : 'bg-gray-200 text-gray-500'
                  ]"
                >
                  <svg v-if="status.completed" class="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M5 13l4 4L19 7" />
                  </svg>
                  <span v-else>{{ idx + 1 }}</span>
                </div>
                <div>
                  <p
                    :class="[
                      'text-sm font-medium',
                      status.completed ? 'text-text-primary' : 'text-text-secondary'
                    ]"
                  >
                    {{ status.label }}
                  </p>
                  <p v-if="status.timestamp" class="text-xs text-text-secondary mt-0.5">
                    {{ formatDate(status.timestamp) }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column - Order Summary -->
        <div class="space-y-6">
          <!-- Order Info -->
          <div class="bg-surface rounded-2xl shadow-card p-6 sm:p-8">
            <h2 class="text-lg font-bold text-text-primary mb-4">订单信息</h2>
            <div class="space-y-3">
              <div class="flex justify-between text-sm">
                <span class="text-text-secondary">订单号</span>
                <span class="font-medium text-text-primary">{{ order.order_number }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-text-secondary">下单时间</span>
                <span class="font-medium text-text-primary">{{ formatDate(order.created_at) }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-text-secondary">支付方式</span>
                <span class="font-medium text-text-primary">{{ order.payment_method || '未支付' }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-text-secondary">支付状态</span>
                <span
                  :class="[
                    'font-medium',
                    order.payment_status === 'paid' ? 'text-green-600' : 'text-yellow-600'
                  ]"
                >
                  {{ order.payment_status === 'paid' ? '已支付' : '未支付' }}
                </span>
              </div>
            </div>
          </div>

          <!-- Shipping Address -->
          <div v-if="order.shipping_address" class="bg-surface rounded-2xl shadow-card p-6 sm:p-8">
            <h2 class="text-lg font-bold text-text-primary mb-4">收货地址</h2>
            <div class="text-sm text-text-secondary space-y-1">
              <p class="font-medium text-text-primary">{{ order.shipping_address.recipient_name }}</p>
              <p>{{ order.shipping_address.phone }}</p>
              <p>{{ order.shipping_address.country }} {{ order.shipping_address.province }} {{ order.shipping_address.city }}</p>
              <p>{{ order.shipping_address.street_address }}</p>
              <p v-if="order.shipping_address.postal_code">邮编: {{ order.shipping_address.postal_code }}</p>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="bg-surface rounded-2xl shadow-card p-6 sm:p-8">
            <div class="space-y-3">
              <button
                v-if="order.status === 'pending'"
                @click="payOrder"
                class="w-full btn-primary text-center"
              >
                立即支付
              </button>
              <button
                v-if="order.status === 'pending'"
                @click="cancelOrder"
                class="w-full px-4 py-2.5 border-2 border-red-300 text-red-500 font-medium rounded-lg hover:bg-red-50 transition-all duration-300 text-center"
              >
                取消订单
              </button>
              <button
                v-if="order.status === 'shipped'"
                @click="confirmReceipt"
                class="w-full px-4 py-2.5 bg-green-500 text-white font-medium rounded-lg hover:bg-green-600 transition-all duration-300 text-center"
              >
                确认收货
              </button>
              <NuxtLink
                to="/orders"
                class="block w-full px-4 py-2.5 border-2 border-primary text-primary font-medium rounded-lg hover:bg-primary/10 transition-all duration-300 text-center"
              >
                返回订单列表
              </NuxtLink>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();

const order = ref<any>(null);
const loading = ref(true);
const error = ref<string | null>(null);

// 订单状态时间线
const orderStatusTimeline = computed(() => {
  if (!order.value) return [];
  const statuses = [
    { key: 'pending', label: '待付款', timestamp: order.value.created_at },
    { key: 'paid', label: '已付款', timestamp: order.value.paid_at },
    { key: 'shipped', label: '已发货', timestamp: order.value.shipped_at },
    { key: 'completed', label: '已完成', timestamp: order.value.completed_at },
  ];

  const statusOrder = ['pending', 'paid', 'shipped', 'completed'];
  const currentIdx = statusOrder.indexOf(order.value.status);

  return statuses.map((s, idx) => ({
    ...s,
    completed: idx <= currentIdx || !!s.timestamp,
  }));
});

// 获取订单详情
const fetchOrder = async () => {
  loading.value = true;
  error.value = null;
  try {
    const orderId = route.params.id as string;
    const response = await fetch(`http://localhost:8000/api/v1/orders/${orderId}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    if (!response.ok) throw new Error('获取订单详情失败');
    const data = await response.json();
    order.value = data;
  } catch (err: any) {
    error.value = err.message || '获取订单详情失败';
  } finally {
    loading.value = false;
  }
};

// 支付订单
const payOrder = () => {
  const orderId = route.params.id as string;
  router.push(`/payment/checkout?order_id=${orderId}`);
};

// 取消订单
const cancelOrder = async () => {
  if (!confirm('确定要取消这个订单吗？')) return;
  try {
    const orderId = route.params.id as string;
    const response = await fetch(`http://localhost:8000/api/v1/orders/${orderId}/cancel`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    if (response.ok) {
      await fetchOrder();
    }
  } catch (err) {
    console.error('Failed to cancel order:', err);
  }
};

// 确认收货
const confirmReceipt = async () => {
  if (!confirm('确认已收到货物吗？')) return;
  try {
    const orderId = route.params.id as string;
    const response = await fetch(`http://localhost:8000/api/v1/orders/${orderId}/confirm-receipt`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    if (response.ok) {
      await fetchOrder();
    }
  } catch (err) {
    console.error('Failed to confirm receipt:', err);
  }
};

// 获取状态样式类
const getStatusClass = (status: string) => {
  switch (status) {
    case 'pending': return 'bg-yellow-100 text-yellow-800';
    case 'paid': return 'bg-blue-100 text-blue-800';
    case 'shipped': return 'bg-purple-100 text-purple-800';
    case 'completed': return 'bg-green-100 text-green-800';
    case 'cancelled': return 'bg-red-100 text-red-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

// 获取状态文本
const getStatusText = (status: string) => {
  switch (status) {
    case 'pending': return '待付款';
    case 'paid': return '已付款';
    case 'shipped': return '已发货';
    case 'completed': return '已完成';
    case 'cancelled': return '已取消';
    default: return status;
  }
};

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return '';
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
  title: computed(() => order.value ? `订单 ${order.value.order_number} - 建材B2B外贸平台` : '订单详情 - 建材B2B外贸平台'),
  meta: [
    { name: 'description', content: '查看订单详情、物流信息和订单状态' },
  ],
});

onMounted(() => {
  const orderId = route.params.id as string;
  if (orderId) {
    fetchOrder();
  }
});
</script>

<style scoped>
.btn-primary {
  @apply inline-flex items-center justify-center px-6 py-3 bg-primary text-white font-semibold rounded-xl hover:bg-primary-700 transition-all duration-300;
}
</style>
