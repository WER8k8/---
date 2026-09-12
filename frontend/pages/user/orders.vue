<template>
  <div class="user-orders-page">
    <!-- Hero Section -->
    <section class="bg-gradient-to-br from-primary/5 via-surface to-accent/5 py-10 sm:py-14 lg:py-20">
      <div class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 text-center">
        <h1 class="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary mb-3 sm:mb-4">
          我的订单
        </h1>
        <p class="text-xs sm:text-sm md:text-base lg:text-xl text-text-secondary max-w-2xl mx-auto">
          查看和管理您的所有订单
        </p>
      </div>
    </section>

    <!-- Orders List -->
    <section class="py-8 sm:py-10 lg:py-14">
      <div class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8">
        <!-- Filter Tabs -->
        <div class="flex items-center gap-2 mb-6 sm:mb-8 overflow-x-auto">
          <button
            v-for="filter in statusFilters"
            :key="filter.key"
            @click="activeStatus = filter.key; fetchOrders()"
            :class="[
              'px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all duration-200',
              activeStatus === filter.key
                ? 'bg-primary text-white'
                : 'bg-surface text-text-secondary hover:bg-surface-elevated hover:text-text-primary'
            ]"
          >
            {{ filter.label }}
          </button>
        </div>

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
          <h3 class="text-lg sm:text-xl font-semibold text-text-primary mb-2">暂无订单</h3>
          <p class="text-sm text-text-secondary mb-6">您还没有任何订单，快去挑选商品吧</p>
          <NuxtLink to="/products" class="btn-primary">
            去购物
          </NuxtLink>
        </div>

        <!-- Orders List -->
        <div v-else class="space-y-6">
          <div
            v-for="order in orders"
            :key="order.id"
            @click="goToOrderDetail(order.id)"
            class="bg-surface rounded-2xl shadow-card p-6 sm:p-8 hover:shadow-card-hover transition-all duration-300 cursor-pointer"
          >
            <div class="flex flex-col sm:flex-row sm:items-center justify-between mb-4 sm:mb-6">
              <div>
                <h3 class="text-lg sm:text-xl font-semibold text-text-primary mb-1">
                  订单号: {{ order.order_number }}
                </h3>
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
                    数量: {{ item.quantity }} {{ item.unit }}
                  </p>
                </div>
                <div class="text-sm sm:text-base font-semibold text-text-primary">
                  ${{ item.price }}
                </div>
              </div>
            </div>

            <!-- Order Total -->
            <div class="border-t border-border mt-4 sm:mt-6 pt-4 sm:pt-6 flex justify-between items-center">
              <span class="text-sm sm:text-base font-medium text-text-primary">订单总额</span>
              <span class="text-lg sm:text-xl font-bold text-primary">${{ order.total_amount }}</span>
            </div>
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="orders.length > 0 && totalPages > 1" class="flex justify-center mt-8 sm:mt-10">
          <nav class="flex items-center gap-2">
            <button
              @click="changePage(currentPage - 1)"
              :disabled="currentPage === 1"
              :class="[
                'px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                currentPage === 1
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-surface text-text-secondary hover:bg-primary hover:text-white'
              ]"
            >
              上一页
            </button>
            <button
              v-for="page in displayedPages"
              :key="page"
              @click="changePage(page)"
              :class="[
                'px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                currentPage === page
                  ? 'bg-primary text-white'
                  : 'bg-surface text-text-secondary hover:bg-primary hover:text-white'
              ]"
            >
              {{ page }}
            </button>
            <button
              @click="changePage(currentPage + 1)"
              :disabled="currentPage === totalPages"
              :class="[
                'px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                currentPage === totalPages
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-surface text-text-secondary hover:bg-primary hover:text-white'
              ]"
            >
              下一页
            </button>
          </nav>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const orders = ref<any[]>([]);
const loading = ref(true);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);
const activeStatus = ref('all');

const statusFilters = [
  { key: 'all', label: '全部' },
  { key: 'pending', label: '待付款' },
  { key: 'paid', label: '已付款' },
  { key: 'shipped', label: '已发货' },
  { key: 'completed', label: '已完成' },
  { key: 'cancelled', label: '已取消' },
];

const totalPages = computed(() => Math.ceil(total.value / pageSize.value));

const displayedPages = computed(() => {
  const pages: number[] = [];
  const maxVisible = 5;
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2));
  let end = Math.min(totalPages.value, start + maxVisible - 1);

  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1);
  }

  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  return pages;
});

// 获取订单列表
const fetchOrders = async () => {
  loading.value = true;
  try {
    const params = new URLSearchParams({
      page: currentPage.value.toString(),
      page_size: pageSize.value.toString(),
    });

    if (activeStatus.value !== 'all') {
      params.append('status', activeStatus.value);
    }

    const response = await fetch(`${useApiV1Url('/orders')}?${params}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });

    if (response.ok) {
      const data = await response.json();
      orders.value = data.items || data || [];
      total.value = data.total || orders.value.length || 0;
    }
  } catch (err) {
    console.error('Failed to fetch orders:', err);
  } finally {
    loading.value = false;
  }
};

// 跳转到订单详情
const goToOrderDetail = (orderId: string) => {
  router.push(`/orders/${orderId}`);
};

// 切换页码
const changePage = (page: number) => {
  if (page < 1 || page > totalPages.value) return;
  currentPage.value = page;
  fetchOrders();
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
  title: '我的订单 - 建材B2B外贸平台',
  meta: [
    { name: 'description', content: '查看和管理您的所有订单' },
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
</style>
