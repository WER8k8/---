/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="inquiries-page">
    <!-- Hero Section -->
    <section class="bg-gradient-to-br from-primary/5 via-surface to-accent/5 py-10 sm:py-14 lg:py-20">
      <div class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 text-center">
        <h1 class="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary mb-3 sm:mb-4">
          {{ t('inquiries.title') }}
        </h1>
        <p class="text-xs sm:text-sm md:text-base lg:text-xl text-text-secondary max-w-2xl mx-auto">
          {{ t('inquiries.subtitle') }}
        </p>
      </div>
    </section>

    <!-- Inquiry Form -->
    <section class="py-8 sm:py-10 lg:py-14">
      <div class="max-w-3xl mx-auto px-3 sm:px-4 lg:px-8">
        <div class="bg-surface rounded-2xl shadow-card p-6 sm:p-8">
          <form @submit.prevent="submitInquiry" class="space-y-6">
            <!-- Product Info (if from product page) -->
            <div v-if="product" class="bg-surface-elevated rounded-xl p-4 mb-6">
              <div class="flex items-center gap-4">
                <img :src="product.image || '/images/placeholder.jpg'" :alt="product.name" class="w-16 h-16 object-cover rounded-lg" />
                <div>
                  <h3 class="font-semibold text-text-primary">{{ product.name }}</h3>
                  <p class="text-sm text-text-secondary">{{ product.price ? `$${product.price}` : '' }}</p>
                </div>
              </div>
            </div>

            <!-- Contact Info -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
              <div>
                <label class="block text-sm font-medium text-text-primary mb-2">{{ $t('inquiry.yourName') }} *</label>
                <input
                  v-model="form.name"
                  type="text"
                  required
                  class="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                  :placeholder="$t('inquiry.namePlaceholder')"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-text-primary mb-2">{{ $t('inquiry.email') }} *</label>
                <input
                  v-model="form.email"
                  type="email"
                  required
                  class="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                  :placeholder="$t('inquiry.emailPlaceholder')"
                />
              </div>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
              <div>
                <label class="block text-sm font-medium text-text-primary mb-2">{{ $t('inquiry.phone') }}</label>
                <input
                  v-model="form.phone"
                  type="tel"
                  class="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                  :placeholder="$t('inquiry.phonePlaceholder')"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-text-primary mb-2">{{ $t('inquiry.company') }}</label>
                <input
                  v-model="form.company"
                  type="text"
                  class="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                  :placeholder="$t('inquiry.companyPlaceholder')"
                />
              </div>
            </div>

            <!-- Inquiry Details -->
            <div>
              <label class="block text-sm font-medium text-text-primary mb-2">{{ $t('inquiry.message') }} *</label>
              <textarea
                v-model="form.message"
                required
                rows="6"
                class="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-none"
                :placeholder="$t('inquiry.messagePlaceholder')"
              ></textarea>
            </div>

            <!-- Quantity & Unit -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
              <div>
                <label class="block text-sm font-medium text-text-primary mb-2">{{ $t('inquiry.quantity') }}</label>
                <input
                  v-model="form.quantity"
                  type="number"
                  min="1"
                  class="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                  :placeholder="$t('inquiry.quantityPlaceholder')"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-text-primary mb-2">{{ $t('inquiry.unit') }}</label>
                <select
                  v-model="form.unit"
                  class="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                >
                  <option value="piece">{{ $t('inquiry.unitPiece') }}</option>
                  <option value="sqm">{{ $t('inquiry.unitSqm') }}</option>
                  <option value="ton">{{ $t('inquiry.unitTon') }}</option>
                  <option value="pallet">{{ $t('inquiry.unitPallet') }}</option>
                </select>
              </div>
            </div>

            <!-- Submit Button -->
            <div class="flex justify-end gap-4">
              <NuxtLink to="/products" class="btn-outline">
                {{ $t('common.cancel') }}
              </NuxtLink>
              <button
                type="submit"
                :disabled="submitting"
                class="btn-primary"
              >
                <svg v-if="submitting" class="animate-spin w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {{ submitting ? $t('common.submitting') : $t('inquiry.submit') }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute, useRouter } from 'vue-router';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

const product = ref(null);
const submitting = ref(false);

const form = ref({
  name: '',
  email: '',
  phone: '',
  company: '',
  message: '',
  quantity: 1,
  unit: 'piece',
  product_id: '',
});

// 获取产品信息（如果来自产品页）
const fetchProduct = async (productId: string) => {
  try {
    const response = await fetch(`/api/v1/products/${productId}`);
    if (response.ok) {
      const data = await response.json();
      product.value = data;
      form.value.product_id = productId;
    }
  } catch (err) {
    console.error('Failed to fetch product:', err);
  }
};

// 提交询盘
const submitInquiry = async () => {
  try {
    submitting.value = true;
    
    const payload = {
      ...form.value,
      created_at: new Date().toISOString(),
    };
    
    const response = await fetch('/api/v1/inquiries/public', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    
    if (!response.ok) throw new Error('Failed to submit inquiry');
    
    const result = await response.json();
    
    // 跳转到成功页
    router.push(`/inquiries/success?id=${result.id}`);
  } catch (err: any) {
    alert(err.message || 'Failed to submit inquiry');
  } finally {
    submitting.value = false;
  }
};

// SEO元数据
useHead({
  title: computed(() => `${t('inquiries.title')} - ${t('common.companyName')}`),
  meta: [
    { name: 'description', content: t('inquiries.subtitle') },
  ],
});

onMounted(() => {
  const productId = route.query.product_id as string;
  if (productId) {
    fetchProduct(productId);
  }
});
</script>

<style scoped>
.btn-primary {
  @apply inline-flex items-center justify-center px-6 py-3 bg-primary text-white font-semibold rounded-xl hover:bg-primary-700 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed;
}

.btn-outline {
  @apply inline-flex items-center justify-center px-6 py-3 border-2 border-primary text-primary font-semibold rounded-xl hover:bg-primary/10 transition-all duration-300;
}
</style>
