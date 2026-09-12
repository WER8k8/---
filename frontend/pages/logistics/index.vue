<template>
  <div class="logistics-page">
    <!-- Hero Section -->
    <section class="bg-gradient-to-br from-primary/5 via-surface to-accent/5 py-10 sm:py-14 lg:py-20">
      <div class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 text-center">
        <h1 class="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary mb-3 sm:mb-4">
          物流跟踪
        </h1>
        <p class="text-xs sm:text-sm md:text-base lg:text-xl text-text-secondary max-w-2xl mx-auto">
          输入运单号查询物流信息
        </p>
      </div>
    </section>

    <!-- Search Section -->
    <section class="py-8 sm:py-10 lg:py-14">
      <div class="max-w-3xl mx-auto px-3 sm:px-4 lg:px-8">
        <!-- Search Form -->
        <div class="bg-surface rounded-2xl shadow-card p-6 sm:p-8 mb-6 sm:mb-8">
          <form @submit.prevent="trackLogistics" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-text-primary mb-2">运单号</label>
              <div class="flex gap-3">
                <input
                  v-model="trackingNumber"
                  type="text"
                  required
                  class="flex-1 px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                  placeholder="请输入运单号，如：SF1234567890"
                />
                <button type="submit" :disabled="trackingLoading" class="btn-primary whitespace-nowrap">
                  {{ trackingLoading ? '查询中...' : '查询' }}
                </button>
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-text-primary mb-2">物流公司（可选）</label>
              <select
                v-model="carrier"
                class="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all bg-white"
              >
                <option value="">自动识别</option>
                <option value="sf-express">顺丰速运</option>
                <option value="zto">中通快递</option>
                <option value="sto">申通快递</option>
                <option value="yto">圆通速递</option>
                <option value="yd">韵达快递</option>
                <option value="ems">EMS</option>
                <option value="dhl">DHL</option>
                <option value="fedex">FedEx</option>
                <option value="ups">UPS</option>
              </select>
            </div>
          </form>
        </div>

        <!-- Loading State -->
        <div v-if="trackingLoading" class="bg-surface rounded-2xl shadow-card p-6 sm:p-8">
          <div class="animate-pulse space-y-4">
            <div class="h-6 bg-gray-200 rounded w-1/3"></div>
            <div class="h-4 bg-gray-200 rounded w-1/2"></div>
            <div v-for="i in 4" :key="i" class="flex gap-4">
              <div class="w-6 h-6 bg-gray-200 rounded-full"></div>
              <div class="flex-1 h-16 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>

        <!-- Error State -->
        <div v-else-if="trackingError" class="bg-surface rounded-2xl shadow-card p-6 sm:p-8 text-center">
          <svg class="w-16 h-16 mx-auto text-red-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 class="text-lg font-semibold text-text-primary mb-2">查询失败</h3>
          <p class="text-sm text-text-secondary mb-4">{{ trackingError }}</p>
          <button @click="trackLogistics" class="btn-primary">
            重试
          </button>
        </div>

        <!-- Tracking Result -->
        <div v-else-if="trackingResult" class="bg-surface rounded-2xl shadow-card p-6 sm:p-8">
          <!-- Tracking Header -->
          <div class="mb-6 sm:mb-8 pb-6 border-b border-border">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between mb-4">
              <div>
                <h2 class="text-lg sm:text-xl font-bold text-text-primary mb-1">
                  运单号: {{ trackingResult.tracking_number }}
                </h2>
                <p class="text-sm text-text-secondary">
                  物流公司: {{ trackingResult.carrier }}
                </p>
              </div>
              <div class="mt-2 sm:mt-0">
                <span
                  :class="[
                    'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium',
                    getStatusClass(trackingResult.status)
                  ]"
                >
                  {{ getStatusText(trackingResult.status) }}
                </span>
              </div>
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
              <div>
                <p class="text-text-secondary">发货地</p>
                <p class="font-medium text-text-primary">{{ trackingResult.origin || '-' }}</p>
              </div>
              <div>
                <p class="text-text-secondary">目的地</p>
                <p class="font-medium text-text-primary">{{ trackingResult.destination || '-' }}</p>
              </div>
              <div>
                <p class="text-text-secondary">预计到达</p>
                <p class="font-medium text-text-primary">{{ trackingResult.estimated_delivery || '-' }}</p>
              </div>
              <div>
                <p class="text-text-secondary">最新更新</p>
                <p class="font-medium text-text-primary">{{ formatDate(trackingResult.last_update) }}</p>
              </div>
            </div>
          </div>

          <!-- Tracking Timeline -->
          <div>
            <h3 class="text-base sm:text-lg font-bold text-text-primary mb-4">物流轨迹</h3>
            <div class="relative">
              <div
                v-for="(event, idx) in trackingResult.events"
                :key="idx"
                class="relative pl-8 pb-8 last:pb-0"
              >
                <!-- Timeline line -->
                <div
                  v-if="idx < trackingResult.events.length - 1"
                  class="absolute left-3 top-3 bottom-0 w-0.5"
                  :class="idx === 0 ? 'bg-primary' : 'bg-gray-200'"
                ></div>
                <!-- Timeline dot -->
                <div
                  :class="[
                    'absolute left-0 top-1 w-6 h-6 rounded-full flex items-center justify-center',
                    idx === 0 ? 'bg-primary text-white' : 'bg-gray-200 text-gray-500'
                  ]"
                >
                  <svg v-if="idx === 0" class="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span v-else class="text-xs">{{ idx + 1 }}</span>
                </div>
                <!-- Event Content -->
                <div
                  :class="[
                    'p-3 rounded-lg',
                    idx === 0 ? 'bg-primary/5 border border-primary/20' : 'bg-surface-elevated'
                  ]"
                >
                  <p
                    :class="[
                      'text-sm font-medium',
                      idx === 0 ? 'text-primary' : 'text-text-primary'
                    ]"
                  >
                    {{ event.description }}
                  </p>
                  <p class="text-xs text-text-secondary mt-1">{{ formatDate(event.timestamp) }}</p>
                  <p v-if="event.location" class="text-xs text-text-secondary mt-0.5">
                    {{ event.location }}
                  </p>
                  <p v-if="event.operator" class="text-xs text-text-secondary mt-0.5">
                    操作人: {{ event.operator }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State (Initial) -->
        <div v-else class="text-center py-10 sm:py-16">
          <svg class="w-16 h-16 sm:w-20 sm:h-20 mx-auto text-text-secondary mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
          <h3 class="text-lg sm:text-xl font-semibold text-text-primary mb-2">输入运单号查询</h3>
          <p class="text-sm text-text-secondary">请输入运单号进行物流跟踪查询</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const trackingNumber = ref('');
const carrier = ref('');
const trackingResult = ref<any>(null);
const trackingLoading = ref(false);
const trackingError = ref<string | null>(null);

// 查询物流
const trackLogistics = async () => {
  if (!trackingNumber.value.trim()) return;

  trackingLoading.value = true;
  trackingError.value = null;
  trackingResult.value = null;

  try {
    const params = new URLSearchParams({
      tracking_number: trackingNumber.value.trim(),
    });
    if (carrier.value) {
      params.append('carrier', carrier.value);
    }

    const url = `${useApiV1Url('/logistics/track')}?${params}`;
    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token') || ''}`,
      },
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.message || payload.detail || '查询失败');
    }

    trackingResult.value = payload.data ?? payload;
  } catch (err: any) {
    trackingError.value = err.message || '查询失败，请稍后重试';
  } finally {
    trackingLoading.value = false;
  }
};

// 获取状态样式类
const getStatusClass = (status: string) => {
  switch (status) {
    case 'delivered': return 'bg-green-100 text-green-800';
    case 'in_transit': return 'bg-blue-100 text-blue-800';
    case 'picked_up': return 'bg-purple-100 text-purple-800';
    case 'exception': return 'bg-red-100 text-red-800';
    case 'pending': return 'bg-yellow-100 text-yellow-800';
    default: return 'bg-gray-100 text-gray-800';
  }
};

// 获取状态文本
const getStatusText = (status: string) => {
  switch (status) {
    case 'delivered': return '已签收';
    case 'in_transit': return '运输中';
    case 'picked_up': return '已揽收';
    case 'exception': return '异常';
    case 'pending': return '待揽收';
    default: return status;
  }
};

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

// SEO元数据
useHead({
  title: '物流跟踪 - 建材B2B外贸平台',
  meta: [
    { name: 'description', content: '输入运单号查询物流信息，跟踪包裹配送状态' },
  ],
});
</script>

<style scoped>
.btn-primary {
  @apply inline-flex items-center justify-center px-6 py-3 bg-primary text-white font-semibold rounded-xl hover:bg-primary-700 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed;
}
</style>
