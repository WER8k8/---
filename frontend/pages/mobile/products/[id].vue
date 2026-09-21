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
        <h1 class="ml-2 text-base font-semibold text-gray-900 truncate">
          {{ product?.name || $t('mobile.product.detail') }}
        </h1>
      </div>
    </MobileNavbar>

    <!-- Loading State -->
    <div
      v-if="pending"
      class="px-4 py-6"
    >
      <div class="animate-pulse">
        <div class="w-full h-64 bg-gray-200 rounded-2xl mb-4" />
        <div class="h-6 bg-gray-200 rounded w-3/4 mb-3" />
        <div class="h-4 bg-gray-200 rounded w-1/2 mb-6" />
        <div class="space-y-2">
          <div class="h-4 bg-gray-200 rounded w-full" />
          <div class="h-4 bg-gray-200 rounded w-5/6" />
        </div>
      </div>
    </div>

    <!-- Error State -->
    <div
      v-else-if="error"
      class="px-4 py-20 text-center"
    >
      <div class="text-red-500 text-base font-medium mb-4">
        {{ $t('mobile.product.loadError') }}
      </div>
      <button
        class="mobile-btn-primary px-6 py-3 rounded-full"
        @click="router.back()"
      >
        {{ $t('mobile.common.goBack') }}
      </button>
    </div>

    <!-- Product Detail -->
    <div
      v-else-if="product"
      class="pb-20"
    >
      <!-- Product Image -->
      <div class="relative bg-white">
        <div class="aspect-square bg-gray-100">
          <img
            v-if="product.images && product.images.length > 0"
            :src="product.images[selectedImageIndex]?.url || product.images[0]?.url"
            :alt="product.name"
            class="w-full h-full object-cover"
          >
          <div
            v-else
            class="w-full h-full flex items-center justify-center text-gray-400"
          >
            <svg
              class="w-16 h-16"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          </div>
        </div>
        <!-- Image Indicators -->
        <div
          v-if="product.images && product.images.length > 1"
          class="flex justify-center gap-1.5 py-3"
        >
          <button
            v-for="(img, idx) in product.images"
            :key="idx"
            class="w-2 h-2 rounded-full transition-colors"
            :class="selectedImageIndex === idx ? 'bg-blue-600' : 'bg-gray-300'"
            @click="selectedImageIndex = idx"
          />
        </div>
      </div>

      <!-- Product Info -->
      <div class="px-4 py-5 bg-white mt-2">
        <h1 class="text-xl font-bold text-gray-900 mb-2">
          {{ product.name }}
        </h1>
        <p class="text-sm text-gray-600 mb-4">
          {{ product.description }}
        </p>

        <!-- Price -->
        <div
          v-if="product.price"
          class="mb-4"
        >
          <span class="text-2xl font-bold text-blue-600">${{ product.price }}</span>
          <span class="text-sm text-gray-500 ml-2">{{ $t('mobile.product.perUnit') }}</span>
        </div>

        <!-- Stock Status -->
        <div class="flex items-center gap-2 mb-4">
          <span
            :class="[
              'px-3 py-1 rounded-full text-sm font-medium',
              product.stock > 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            ]"
          >
            {{ product.stock > 0 ? $t('mobile.product.inStock') : $t('mobile.product.outOfStock') }}
          </span>
          <span
            v-if="product.stock > 0"
            class="text-sm text-gray-500"
          >
            {{ $t('mobile.product.stockCount', { count: product.stock }) }}
          </span>
        </div>

        <!-- Specifications (simplified) -->
        <div
          v-if="product.specs"
          class="border-t border-gray-100 pt-4 mt-4"
        >
          <h3 class="text-sm font-semibold text-gray-900 mb-3">
            {{ $t('mobile.product.specs') }}
          </h3>
          <div class="space-y-2">
            <div
              v-for="(value, key) in product.specs"
              :key="key"
              class="flex justify-between text-sm"
            >
              <span class="text-gray-500">{{ key }}</span>
              <span class="text-gray-900 font-medium">{{ value }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4 z-40">
        <div class="flex gap-3">
          <button
            class="flex-1 mobile-btn-primary py-3.5 rounded-xl font-semibold text-base"
            @click="openInquiry"
          >
            {{ $t('mobile.product.requestInquiry') }}
          </button>
          <button
            class="flex-1 mobile-btn-outline py-3.5 rounded-xl font-semibold text-base"
            @click="openQuote"
          >
            {{ $t('mobile.product.requestQuote') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile Tab Bar -->
    <MobileTabBar />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const route = useRoute();
const router = useRouter();
const { $t } = useI18n();

const selectedImageIndex = ref(0);

// Fetch product data
const { data: product, pending, error } = await useFetch(`/api/products/${route.params.id}`, {
  key: `mobile-product-${route.params.id}`,
  lazy: true,
});

// Methods
const openInquiry = () => {
  router.push(`/mobile/contact?product=${route.params.id}`);
};

const openQuote = () => {
  router.push(`/mobile/contact?product=${route.params.id}&type=quote`);
};

// Set page meta
useHead({
  title: computed(() => product.value?.name || 'Product Detail'),
  meta: [
    { name: 'description', content: computed(() => product.value?.description || '') }
  ]
});
</script>
