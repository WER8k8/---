<template>
  <div class="min-h-screen bg-gray-50 pb-safe-bottom">
    <!-- Mobile Navbar -->
    <MobileNavbar safe-area-top :blur="true">
      <template #default>
        <h1 class="text-base font-semibold text-gray-900">{{ t('mobile.user.favorites') }}</h1>
      </template>
    </MobileNavbar>

    <!-- Loading State -->
    <div v-if="loading" class="px-4 py-4 grid grid-cols-2 gap-3">
      <div v-for="i in 4" :key="i" class="bg-white rounded-2xl p-3 animate-pulse">
        <div class="w-full aspect-square bg-gray-200 rounded-lg mb-2"></div>
        <div class="h-4 bg-gray-200 rounded w-3/4 mb-1"></div>
        <div class="h-3 bg-gray-200 rounded w-1/2"></div>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex items-center justify-center min-h-[60vh] px-4">
      <div class="text-center">
        <div class="text-6xl mb-4">😞</div>
        <h2 class="text-xl font-bold text-gray-900 mb-2">
          {{ t('mobile.favorites.loadFailed') }}
        </h2>
        <p class="text-gray-600 mb-6">{{ error }}</p>
        <button class="mobile-btn-primary inline-block px-6 py-3 rounded-full" @click="fetchFavorites">
          {{ t('mobile.favorites.retry') }}
        </button>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="favorites.length === 0" class="px-4 py-20 text-center">
      <svg class="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
      </svg>
      <h3 class="text-base font-medium text-gray-900 mb-2">{{ t('mobile.favorites.noFavorites') }}</h3>
      <p class="text-sm text-gray-500 mb-6">{{ t('mobile.favorites.noFavoritesDesc') }}</p>
      <NuxtLink to="/mobile/products" class="mobile-btn-primary px-6 py-3 rounded-full inline-block">
        {{ t('mobile.favorites.browse') }}
      </NuxtLink>
    </div>

    <!-- Favorites Grid -->
    <div v-else class="px-4 py-2 grid grid-cols-2 gap-3 pb-20">
      <div
        v-for="item in favorites"
        :key="item.id"
        class="bg-white rounded-2xl overflow-hidden relative"
      >
        <!-- Product Image -->
        <div class="relative aspect-square bg-gray-100">
          <img
            :src="item.product?.images?.[0]?.url || item.product_image || '/images/placeholder.jpg'"
            :alt="item.product?.name || item.product_name"
            class="w-full h-full object-cover"
          />
          <!-- Remove Button -->
          <button
            @click="removeFavorite(item.id)"
            class="absolute top-2 right-2 p-1.5 bg-white/80 backdrop-blur-sm rounded-full hover:bg-white hover:text-red-500 transition-all shadow-sm"
          >
            <svg class="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 24 24">
              <path d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" />
            </svg>
          </button>
        </div>

        <!-- Product Info -->
        <div class="p-3">
          <NuxtLink :to="`/mobile/products/${item.product?.id || item.product_id}`">
            <h3 class="text-sm font-medium text-gray-900 line-clamp-2 mb-1">
              {{ item.product?.name || item.product_name }}
            </h3>
          </NuxtLink>
          <div class="flex items-center justify-between">
            <span v-if="item.product?.price" class="text-base font-bold text-blue-600">
              ${{ item.product?.price }}
            </span>
            <span class="text-xs text-gray-400">
              {{ formatDate(item.created_at) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Mobile Tab Bar -->
    <MobileTabBar />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';

const router = useRouter();
const { t } = useI18n();

const favorites = ref<any[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

// Fetch favorites
const fetchFavorites = async () => {
  loading.value = true;
  error.value = null;
  try {
    const response = await fetch('/api/v1/favorites?page=1&page_size=50', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    if (response.ok) {
      const data = await response.json();
      favorites.value = data.items || data || [];
    } else {
      throw new Error(`Failed to fetch: ${response.status}`);
    }
  } catch (err: any) {
    error.value = err.message || t('mobile.favorites.loadFailed');
    console.error('Failed to fetch favorites:', err);
  } finally {
    loading.value = false;
  }
};

// Remove favorite
const removeFavorite = async (id: string) => {
  if (!confirm(t('mobile.favorites.confirmRemove'))) return;
  try {
    await fetch(`/api/v1/favorites/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
    });
    await fetchFavorites();
  } catch (err) {
    console.error('Failed to remove favorite:', err);
  }
};

// Format date
const formatDate = (dateStr: string): string => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return `${date.getMonth() + 1}/${date.getDate()}`;
};

// Page meta
useHead({
  title: t('mobile.user.favorites'),
});

onMounted(() => {
  fetchFavorites();
});
</script>
