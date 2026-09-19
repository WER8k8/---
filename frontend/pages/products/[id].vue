/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="product-detail-page">
    <!-- Loading State -->
    <div
      v-if="loading"
      class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 py-8 sm:py-12"
    >
      <div class="animate-pulse">
        <div class="h-8 sm:h-10 bg-gray-200 rounded w-3/4 mb-4" />
        <div class="h-4 sm:h-5 bg-gray-200 rounded w-1/2 mb-8" />
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8">
          <div class="h-64 sm:h-80 lg:h-96 bg-gray-200 rounded-2xl" />
          <div class="space-y-4">
            <div class="h-6 bg-gray-200 rounded w-full" />
            <div class="h-6 bg-gray-200 rounded w-5/6" />
            <div class="h-6 bg-gray-200 rounded w-4/6" />
          </div>
        </div>
      </div>
    </div>

    <!-- Error State -->
    <div
      v-else-if="error"
      class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 py-8 sm:py-12 text-center"
    >
      <div class="text-red-500 text-lg sm:text-xl font-semibold mb-4">
        {{ error }}
      </div>
      <NuxtLink
        to="/products"
        class="btn-primary"
      >
        {{ $t('common.backToProducts') }}
      </NuxtLink>
    </div>

    <!-- Product Detail -->
    <div
      v-else-if="product"
      class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 py-8 sm:py-12"
    >
      <!-- Breadcrumb -->
      <nav class="mb-4 sm:mb-6">
        <ol class="flex items-center space-x-2 text-sm text-text-secondary">
          <li>
            <NuxtLink
              to="/"
              class="hover:text-primary"
            >
              {{ $t('common.home') }}
            </NuxtLink>
          </li>
          <li>/</li>
          <li>
            <NuxtLink
              to="/products"
              class="hover:text-primary"
            >
              {{ $t('common.products') }}
            </NuxtLink>
          </li>
          <li>/</li>
          <li class="text-text-primary font-medium">
            {{ product.name }}
          </li>
        </ol>
      </nav>

      <!-- Product Header -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8 mb-8 sm:mb-12">
        <!-- Product Images -->
        <div class="relative">
          <div class="aspect-w-4 aspect-h-3 rounded-2xl overflow-hidden bg-surface-elevated">
            <img
              v-if="product.images && product.images.length > 0"
              :src="product.images[selectedImageIndex].url"
              :alt="product.name"
              class="w-full h-full object-cover"
            >
            <div
              v-else
              class="w-full h-full flex items-center justify-center text-text-secondary"
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
          <!-- Thumbnail Images -->
          <div
            v-if="product.images && product.images.length > 1"
            class="flex gap-2 mt-4"
          >
            <button
              v-for="(img, idx) in product.images"
              :key="idx"
              @click="selectedImageIndex = idx"
              :class="[
                'w-16 h-16 sm:w-20 sm:h-20 rounded-lg overflow-hidden border-2 transition-all',
                selectedImageIndex === idx ? 'border-primary' : 'border-transparent hover:border-primary/50'
              ]"
            >
              <img
                :src="img.url"
                :alt="img.alt || product.name"
                class="w-full h-full object-cover"
              >
            </button>
          </div>
        </div>

        <!-- Product Info -->
        <div>
          <h1 class="text-2xl sm:text-3xl lg:text-4xl font-bold text-text-primary mb-3 sm:mb-4">
            {{ product.name }}
          </h1>
          <p class="text-sm sm:text-base text-text-secondary mb-4 sm:mb-6">
            {{ product.description }}
          </p>

          <!-- Price -->
          <div
            v-if="product.price"
            class="mb-4 sm:mb-6"
          >
            <span class="text-2xl sm:text-3xl font-bold text-primary">${{ product.price }}</span>
            <span class="text-sm text-text-secondary ml-2">{{ $t('product.perUnit') }}</span>
          </div>

          <!-- Stock Status -->
          <div class="mb-4 sm:mb-6">
            <span
              :class="[
                'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium',
                product.stock > 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              ]"
            >
              {{ product.stock > 0 ? $t('product.inStock') : $t('product.outOfStock') }}
            </span>
            <span
              v-if="product.stock > 0"
              class="text-sm text-text-secondary ml-2"
            >{{ $t('product.stockCount', { count: product.stock }) }}</span>
          </div>

          <!-- Action Buttons -->
          <div class="flex flex-col sm:flex-row gap-3 sm:gap-4 mb-6 sm:mb-8">
            <button
              @click="openInquiryDialog"
              class="btn-primary btn-primary-lg flex-1"
            >
              {{ $t('product.requestInquiry') }}
            </button>
            <button
              @click="openQuoteDialog"
              class="btn-outline flex-1"
            >
              {{ $t('product.requestQuote') }}
            </button>
          </div>

          <!-- IM Contact Buttons -->
          <div
            v-if="merchantIM"
            class="border-t border-border pt-4 sm:pt-6"
          >
            <h3 class="text-sm font-semibold text-text-primary mb-3">
              {{ $t('product.contactSupplier') }}
            </h3>
            <div class="flex flex-wrap gap-2">
              <a
                v-if="merchantIM.whatsapp"
                :href="`https://wa.me/${merchantIM.whatsapp}`"
                target="_blank"
                rel="noopener"
                class="inline-flex items-center px-3 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors text-sm"
              >
                <svg
                  class="w-4 h-4 mr-2"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.669.15-.197.297-.767.966-.94 1.164-.173.198-.347.223-.644.075-.297-.149-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.297-.497.099-.198.051-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.007-.371-.009-.57-.009-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.095 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.288.173-1.413-.074-.124-.272-.198-.57-.347z" />
                </svg>
                WhatsApp
              </a>
              <a
                v-if="merchantIM.wechat"
                :href="`weixin://dl/chat?${merchantIM.wechat}`"
                class="inline-flex items-center px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
              >
                <svg
                  class="w-4 h-4 mr-2"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 01.213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.295.295a.326.326 0 00.167-.054l1.933-1.12a.59.59 0 01.595-.693c.627-.114 1.275-.178 1.934-.178.294 0 .578.024.862.053a5.37 5.37 0 01-.051-.216l-.381-1.445a.59.59 0 01.216-.665C13.596 10.408 16 8.152 16 5.28c0-3.181-3.537-5.748-7.86-5.748l.213.656zM5.785 5.584c.433 0 .784.38.784.849 0 .469-.351.848-.784.848s-.784-.379-.784-.848c0-.469.351-.849.784-.849zm5.217 0c.433 0 .784.38.784.849 0 .469-.351.848-.784.848s-.784-.379-.784-.848c0-.469.351-.849.784-.849zm5.661 2.118c-.433 0-.784-.379-.784-.848 0-.47.351-.849.784-.849.433 0 .784.379.784.849 0 .469-.351.848-.784.848zm3.283 1.445c-.867 2.12-3.307 3.723-5.773 3.723-.826 0-1.623-.137-2.367-.388a.59.59 0 01-.333-.532l.27-1.023a.59.59 0 00-.216-.665c-1.143-1.009-2.168-2.259-2.168-3.635 0-2.348 2.595-4.323 5.734-4.323 2.938 0 5.674 1.686 5.674 4.323 0 1.058-.419 2.147-1.221 2.52z" />
                </svg>
                微信
              </a>
              <a
                v-if="merchantIM.email"
                :href="`mailto:${merchantIM.email}`"
                class="inline-flex items-center px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm"
              >
                <svg
                  class="w-4 h-4 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
                Email
              </a>
            </div>
          </div>
        </div>
      </div>

      <!-- Product Specifications -->
      <div
        v-if="product.specs"
        class="mb-8 sm:mb-12"
      >
        <h2 class="text-xl sm:text-2xl font-bold text-text-primary mb-4 sm:mb-6">
          {{ $t('product.specifications') }}
        </h2>
        <div class="bg-surface rounded-2xl overflow-hidden">
          <table class="w-full">
            <tbody>
              <tr
                v-for="(value, key) in product.specs"
                :key="key"
                class="border-b border-border last:border-b-0"
              >
                <td class="px-4 py-3 sm:px-6 sm:py-4 bg-surface-elevated font-medium text-text-primary w-1/3 sm:w-1/4">
                  {{ key }}
                </td>
                <td class="px-4 py-3 sm:px-6 sm:py-4 text-text-secondary">
                  {{ value }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Related Products -->
      <div
        v-if="relatedProducts && relatedProducts.length > 0"
        class="mb-8 sm:mb-12"
      >
        <h2 class="text-xl sm:text-2xl font-bold text-text-primary mb-4 sm:mb-6">
          {{ $t('product.relatedProducts') }}
        </h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          <NuxtLink
            v-for="related in relatedProducts"
            :key="related.id"
            :to="`/products/${related.id}`"
            class="card group p-4 sm:p-5"
          >
            <img
              :src="related.image || '/images/placeholder.jpg'"
              :alt="related.name"
              class="w-full h-32 sm:h-40 object-cover rounded-lg mb-3 sm:mb-4"
            >
            <h3 class="text-base sm:text-lg font-semibold text-text-primary group-hover:text-primary transition-colors">
              {{ related.name }}
            </h3>
            <p class="text-sm text-text-secondary mt-1">
              {{ related.price ? `$${related.price}` : '' }}
            </p>
          </NuxtLink>
        </div>
      </div>
    </div>

    <!-- Inquiry Dialog -->
    <div
      v-if="showInquiryModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
    >
      <div class="bg-white rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div class="p-6">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-2xl font-bold text-text-primary">
              {{ $t('product.requestInquiry') }}
            </h2>
            <button
              @click="showInquiryModal = false"
              class="text-text-secondary hover:text-text-primary"
            >
              <svg
                class="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
          <form
            @submit.prevent="submitInquiry"
            class="space-y-4"
          >
            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">{{ $t('common.name') }}</label>
              <input
                v-model="inquiryForm.name"
                type="text"
                required
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              >
            </div>
            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">{{ $t('common.email') }}</label>
              <input
                v-model="inquiryForm.email"
                type="email"
                required
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              >
            </div>
            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">{{ $t('common.phone') }}</label>
              <input
                v-model="inquiryForm.phone"
                type="tel"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              >
            </div>
            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">{{ $t('common.company') }}</label>
              <input
                v-model="inquiryForm.company"
                type="text"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              >
            </div>
            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">{{ $t('common.quantity') }}</label>
              <input
                v-model.number="inquiryForm.quantity"
                type="number"
                min="1"
                required
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              >
            </div>
            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">{{ $t('common.message') }}</label>
              <textarea
                v-model="inquiryForm.message"
                rows="4"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                :placeholder="$t('product.inquiryPlaceholder')"
              />
            </div>
            <div class="flex gap-4">
              <button
                type="submit"
                class="btn-primary flex-1"
                :disabled="submittingInquiry"
              >
                {{ submittingInquiry ? $t('common.submitting') : $t('common.submit') }}
              </button>
              <button
                type="button"
                @click="showInquiryModal = false"
                class="btn-outline"
              >
                {{ $t('common.cancel') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Quote Dialog -->
    <div
      v-if="showQuoteModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
    >
      <div class="bg-white rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div class="p-6">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-2xl font-bold text-text-primary">
              {{ $t('product.requestQuote') }}
            </h2>
            <button
              @click="showQuoteModal = false"
              class="text-text-secondary hover:text-text-primary"
            >
              <svg
                class="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
          <form
            @submit.prevent="submitQuote"
            class="space-y-4"
          >
            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">{{ $t('common.name') }}</label>
              <input
                v-model="quoteForm.name"
                type="text"
                required
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              >
            </div>
            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">{{ $t('common.email') }}</label>
              <input
                v-model="quoteForm.email"
                type="email"
                required
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              >
            </div>
            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">{{ $t('common.phone') }}</label>
              <input
                v-model="quoteForm.phone"
                type="tel"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              >
            </div>
            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">{{ $t('common.company') }}</label>
              <input
                v-model="quoteForm.company"
                type="text"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              >
            </div>
            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">{{ $t('product.specifications') }}</label>
              <textarea
                v-model="quoteForm.productSpecs"
                rows="3"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                :placeholder="$t('product.specsPlaceholder')"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">{{ $t('product.targetPrice') }}</label>
              <input
                v-model="quoteForm.targetPrice"
                type="text"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                placeholder="$"
              >
            </div>
            <div>
              <label class="block text-sm font-medium text-text-primary mb-1">{{ $t('common.quantity') }}</label>
              <input
                v-model.number="quoteForm.quantity"
                type="number"
                min="1"
                required
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              >
            </div>
            <div class="flex gap-4">
              <button
                type="submit"
                class="btn-primary flex-1"
                :disabled="submittingQuote"
              >
                {{ submittingQuote ? $t('common.submitting') : $t('common.submit') }}
              </button>
              <button
                type="button"
                @click="showQuoteModal = false"
                class="btn-outline"
              >
                {{ $t('common.cancel') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute, useRouter } from 'vue-router';
import { useApi } from '~/composables/useApi';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

const product = ref(null);
const relatedProducts = ref([]);
const merchantIM = ref(null);
const loading = ref(true);
const error = ref(null);
const selectedImageIndex = ref(0);

// Inquiry dialog
const showInquiryModal = ref(false);
const inquiryForm = ref({
  name: '',
  email: '',
  phone: '',
  company: '',
  message: '',
  quantity: 1,
});
const submittingInquiry = ref(false);

// Quote dialog
const showQuoteModal = ref(false);
const quoteForm = ref({
  name: '',
  email: '',
  phone: '',
  company: '',
  productSpecs: '',
  targetPrice: '',
  quantity: 1,
});
const submittingQuote = ref(false);

// 获取产品详情
const fetchProduct = async (id: string) => {
  try {
    loading.value = true;
    error.value = null;
    const response = await fetch(`/api/v1/products/${id}`);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();
    product.value = data;
    
    // 获取商家IM路由配置
    if (data.merchant_id) {
      fetchMerchantIM(data.merchant_id);
    }
    
    // 获取相关产品
    if (data.category_id) {
      fetchRelatedProducts(data.category_id, id);
    }
  } catch (err: any) {
    error.value = err.message || 'Failed to load product';
  } finally {
    loading.value = false;
  }
};

// 获取商家IM配置
const fetchMerchantIM = async (merchantId: string) => {
  try {
    const response = await fetch(`/api/v1/im-routing/merchant/${merchantId}`);
    if (response.ok) {
      const data = await response.json();
      merchantIM.value = data;
    }
  } catch (err) {
    console.error('Failed to fetch merchant IM:', err);
  }
};

// 获取相关产品
const fetchRelatedProducts = async (categoryId: string, excludeId: string) => {
  try {
    const response = await fetch(`/api/v1/products?category_id=${categoryId}&limit=4`);
    if (response.ok) {
      const data = await response.json();
      relatedProducts.value = data.filter((p: any) => p.id !== excludeId).slice(0, 4);
    }
  } catch (err) {
    console.error('Failed to fetch related products:', err);
  }
};

// 打开询盘对话框
const openInquiryDialog = () => {
  showInquiryModal.value = true;
};

// 提交询盘
const submitInquiry = async () => {
  try {
    submittingInquiry.value = true;
    const { post } = useApi();
    await post('/inquiries', {
      product_id: route.params.id,
      name: inquiryForm.value.name,
      email: inquiryForm.value.email,
      phone: inquiryForm.value.phone,
      company: inquiryForm.value.company,
      message: inquiryForm.value.message,
      quantity: inquiryForm.value.quantity,
    });
    showInquiryModal.value = false;
    inquiryForm.value = { name: '', email: '', phone: '', company: '', message: '', quantity: 1 };
    alert('询盘已提交成功');
  } catch (err: any) {
    alert(err.message || '提交询盘失败');
  } finally {
    submittingInquiry.value = false;
  }
};

// 打开报价对话框
const openQuoteDialog = () => {
  showQuoteModal.value = true;
};

// 提交报价请求
const submitQuote = async () => {
  try {
    submittingQuote.value = true;
    const { post } = useApi();
    await post('/quotes', {
      product_id: route.params.id,
      name: quoteForm.value.name,
      email: quoteForm.value.email,
      phone: quoteForm.value.phone,
      company: quoteForm.value.company,
      product_specs: quoteForm.value.productSpecs,
      target_price: quoteForm.value.targetPrice,
      quantity: quoteForm.value.quantity,
    });
    showQuoteModal.value = false;
    quoteForm.value = { name: '', email: '', phone: '', company: '', productSpecs: '', targetPrice: '', quantity: 1 };
    alert('报价请求已提交成功');
  } catch (err: any) {
    alert(err.message || '提交报价请求失败');
  } finally {
    submittingQuote.value = false;
  }
};

// SEO元数据
useHead({
  title: computed(() => product.value ? `${product.value.name} - ${t('common.companyName')}` : t('common.companyName')),
  meta: [
    { name: 'description', content: computed(() => product.value ? product.value.description : '') },
    { property: 'og:title', content: computed(() => product.value ? product.value.name : '') },
    { property: 'og:description', content: computed(() => product.value ? product.value.description : '') },
    { property: 'og:image', content: computed(() => product.value && product.value.images && product.value.images.length > 0 ? product.value.images[0].url : '') },
  ],
});

onMounted(() => {
  const productId = route.params.id as string;
  if (productId) {
    fetchProduct(productId);
  }
});
</script>

<style scoped>
.product-detail-page {
  min-height: 100vh;
}

.btn-primary {
  @apply inline-flex items-center justify-center px-6 py-3 bg-primary text-white font-semibold rounded-xl hover:bg-primary-700 transition-all duration-300;
}

.btn-primary-lg {
  @apply px-8 py-4 text-base;
}

.btn-outline {
  @apply inline-flex items-center justify-center px-6 py-3 border-2 border-primary text-primary font-semibold rounded-xl hover:bg-primary/10 transition-all duration-300;
}
</style>
