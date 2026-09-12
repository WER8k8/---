<template>
  <div class="user-favorites-page">
    <!-- Hero Section -->
    <section class="bg-gradient-to-br from-primary/5 via-surface to-accent/5 py-10 sm:py-14 lg:py-20">
      <div class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 text-center">
        <h1 class="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary mb-3 sm:mb-4">
          我的收藏
        </h1>
        <p class="text-xs sm:text-sm md:text-base lg:text-xl text-text-secondary max-w-2xl mx-auto">
          您收藏的建材产品都在这里
        </p>
      </div>
    </section>

    <!-- Favorites List -->
    <section class="py-8 sm:py-10 lg:py-14">
      <div class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8">
        <!-- Loading State -->
        <div v-if="loading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
          <div v-for="i in 8" :key="i" class="animate-pulse">
            <div class="bg-surface rounded-2xl p-4 sm:p-5">
              <div class="aspect-w-4 aspect-h-3 bg-gray-200 rounded-lg mb-3"></div>
              <div class="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div class="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else-if="favorites.length === 0" class="text-center py-10 sm:py-16">
          <svg class="w-16 h-16 sm:w-20 sm:h-20 mx-auto text-text-secondary mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
          </svg>
          <h3 class="text-lg sm:text-xl font-semibold text-text-primary mb-2">暂无收藏</h3>
          <p class="text-sm text-text-secondary mb-6">您还没有收藏任何产品，快去挑选喜欢的商品吧</p>
          <NuxtLink to="/products" class="btn-primary">
            去逛逛
          </NuxtLink>
        </div>

        <!-- Favorites Grid -->
        <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
          <div
            v-for="item in favorites"
            :key="item.id"
            class="bg-surface rounded-2xl shadow-card overflow-hidden hover:shadow-card-hover transition-all duration-300 group"
          >
            <!-- Product Image -->
            <div class="relative aspect-w-4 aspect-h-3 bg-surface-elevated">
              <img
                :src="item.product?.images?.[0]?.url || item.product_image || '/images/placeholder.jpg'"
                :alt="item.product?.name || item.product_name"
                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              />
              <!-- Remove Favorite Button -->
              <button
                @click.stop="removeFavorite(item.id)"
                class="absolute top-2 right-2 p-2 bg-white/80 backdrop-blur-sm rounded-full hover:bg-white hover:text-red-500 transition-all duration-200 shadow-sm"
                title="取消收藏"
              >
                <svg class="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" />
                </svg>
              </button>
            </div>

            <!-- Product Info -->
            <div class="p-4 sm:p-5">
              <NuxtLink :to="`/products/${item.product?.id || item.product_id}`">
                <h3 class="text-sm sm:text-base font-semibold text-text-primary group-hover:text-primary transition-colors line-clamp-2 mb-2">
                  {{ item.product?.name || item.product_name }}
                </h3>
              </NuxtLink>
              <div class="flex items-center justify-between">
                <span v-if="item.product?.price" class="text-lg font-bold text-primary">
                  ${{ item.product?.price }}
                </span>
                <span class="text-xs text-text-secondary">
                  {{ formatDate(item.created_at) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Pagination -->
        <div v-if="favorites.length > 0 && totalPages > 1" class="flex justify-center mt-8 sm:mt-10">
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

const favorites = ref<any[]>([]);
const loading = ref(true);
const currentPage = ref(1);
const pageSize = ref(12);
const total = ref(0);

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

// 获取收藏列表
const fetchFavorites = async () => {
  loading.value = true;
  try {
    const params = new URLSearchParams({
      page: currentPage.value.toString(),
      page_size: pageSize.value.toString(),
    });

    const response = await fetch(`${useApiV1Url('/favorites')}?${params}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });

    if (response.ok) {
      const data = await response.json();
      favorites.value = data.items || data || [];
      total.value = data.total || favorites.value.length || 0;
    }
  } catch (err) {
    console.error('Failed to fetch favorites:', err);
  } finally {
    loading.value = false;
  }
};

// 取消收藏
const removeFavorite = async (favoriteId: string) => {
  if (!confirm('确定要取消收藏吗？')) return;

  try {
    const response = await fetch(useApiV1Url(`/favorites/${favoriteId}`), {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });

    if (response.ok) {
      await fetchFavorites();
    }
  } catch (err) {
    console.error('Failed to remove favorite:', err);
  }
};

// 切换页码
const changePage = (page: number) => {
  if (page < 1 || page > totalPages.value) return;
  currentPage.value = page;
  fetchFavorites();
};

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
  });
};

// SEO元数据
useHead({
  title: '我的收藏 - 建材B2B外贸平台',
  meta: [
    { name: 'description', content: '查看您收藏的建材产品' },
  ],
});

onMounted(() => {
  fetchFavorites();
});
</script>

<style scoped>
.btn-primary {
  @apply inline-flex items-center justify-center px-6 py-3 bg-primary text-white font-semibold rounded-xl hover:bg-primary-700 transition-all duration-300;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
