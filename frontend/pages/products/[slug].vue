<template>
  <div class="product-detail-page">
    <div
      v-if="loading"
      class="loading-container"
    >
      <div class="loading-spinner" />
      <p>{{ t('products.detail.loading') }}</p>
    </div>

    <div
      v-else-if="error"
      class="error-container"
    >
      <h2>{{ t('products.detail.loadFailed') }}</h2>
      <p>{{ error }}</p>
      <NuxtLink
        to="/products"
        class="btn-primary"
      >
        {{ t('products.detail.backToList') }}
      </NuxtLink>
    </div>

    <template v-else-if="product">
      <!-- Breadcrumb -->
      <AnimatedSection
        animation="fade-in"
        :delay="0"
      >
        <nav class="breadcrumb max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <ol class="flex items-center space-x-2 text-sm text-text-secondary">
            <li>
              <NuxtLink
                to="/"
                class="hover:text-primary transition-colors"
              >
                {{ t('products.detail.breadcrumbHome') }}
              </NuxtLink>
            </li>
            <li><span class="mx-2">/</span></li>
            <li>
              <NuxtLink
                to="/products"
                class="hover:text-primary transition-colors"
              >
                {{ t('products.detail.breadcrumbProducts') }}
              </NuxtLink>
            </li>
            <li><span class="mx-2">/</span></li>
            <li class="text-text-primary font-medium">
              {{ product.name }}
            </li>
          </ol>
        </nav>
      </AnimatedSection>

      <!-- Hero Section -->
      <section
        class="product-hero bg-gradient-to-br from-primary/5 via-surface to-accent/5 py-12 md:py-20"
      >
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
            <!-- Product Image -->
            <AnimatedSection
              animation="slide-right"
              :delay="100"
            >
              <div
                class="product-image-container rounded-2xl overflow-hidden shadow-card bg-surface-elevated"
              >
                <img
                  :src="product.image_url || '/images/product-default.jpg'"
                  :alt="product.name"
                  class="w-full h-64 md:h-96 object-cover"
                  loading="lazy"
                >
              </div>
            </AnimatedSection>

            <!-- Product Info -->
            <AnimatedSection
              animation="slide-left"
              :delay="200"
            >
              <div class="product-info">
                <h1 class="text-3xl md:text-4xl font-bold text-text-primary mb-4">
                  {{ product.name }}
                </h1>
                <p
                  v-if="product.subtitle"
                  class="text-xl text-primary font-medium mb-6"
                >
                  {{ product.subtitle }}
                </p>
                <p class="text-text-secondary leading-relaxed mb-8">
                  {{ product.description }}
                </p>

                <!-- Quick Specs -->
                <div class="grid grid-cols-2 gap-4 mb-8">
                  <div
                    v-if="product.density"
                    class="spec-item p-4 bg-surface-elevated rounded-xl"
                  >
                    <div class="text-sm text-text-secondary mb-1">
                      {{ t('products.detail.density') }}
                    </div>
                    <div class="text-lg font-semibold text-text-primary">
                      {{ product.density }}
                    </div>
                  </div>
                  <div
                    v-if="product.strength"
                    class="spec-item p-4 bg-surface-elevated rounded-xl"
                  >
                    <div class="text-sm text-text-secondary mb-1">
                      {{ t('products.detail.strength') }}
                    </div>
                    <div class="text-lg font-semibold text-text-primary">
                      {{ product.strength }}
                    </div>
                  </div>
                  <div
                    v-if="product.thermal_conductivity"
                    class="spec-item p-4 bg-surface-elevated rounded-xl"
                  >
                    <div class="text-sm text-text-secondary mb-1">
                      {{ t('products.detail.thermalConductivity') }}
                    </div>
                    <div class="text-lg font-semibold text-text-primary">
                      {{ product.thermal_conductivity }}
                    </div>
                  </div>
                  <div
                    v-if="product.fire_rating"
                    class="spec-item p-4 bg-surface-elevated rounded-xl"
                  >
                    <div class="text-sm text-text-secondary mb-1">
                      {{ t('products.detail.fireRating') }}
                    </div>
                    <div class="text-lg font-semibold text-text-primary">
                      {{ product.fire_rating }}
                    </div>
                  </div>
                </div>

                <!-- CTA Buttons -->
                <div class="flex flex-wrap gap-4">
                  <NuxtLink
                    to="/contact"
                    class="btn-primary btn-primary-lg group"
                  >
                    <svg
                      class="w-5 h-5 mr-2 group-hover:scale-110 transition-transform"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                      />
                    </svg>
                    {{ t('products.detail.consultNow') }}
                  </NuxtLink>
                  <a
                    :href="`tel:${contactPhone}`"
                    class="btn-outline group"
                  >
                    <svg
                      class="w-5 h-5 mr-2 group-hover:animate-pulse"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                      />
                    </svg>
                    {{ t('products.detail.phoneConsult') }}
                  </a>
                </div>
              </div>
            </AnimatedSection>
          </div>
        </div>
      </section>

      <!-- Technical Parameters -->
      <section
        class="py-16 bg-surface-elevated"
        v-if="product.technical_params"
      >
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <AnimatedSection
            animation="fade-in-up"
            :delay="0"
          >
            <h2 class="section-title text-center mb-12">
              {{ t('products.detail.technicalParams') }}
            </h2>
          </AnimatedSection>
          <AnimatedSection
            animation="fade-in-up"
            :delay="100"
          >
            <div class="bg-surface rounded-2xl shadow-card p-6 md:p-8">
              <pre class="whitespace-pre-wrap text-text-secondary leading-relaxed font-sans">{{
                product.technical_params
              }}</pre>
            </div>
          </AnimatedSection>
        </div>
      </section>

      <!-- Application Scenarios -->
      <section
        class="py-16"
        v-if="product.application_scenarios"
      >
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <AnimatedSection
            animation="fade-in-up"
            :delay="0"
          >
            <h2 class="section-title text-center mb-12">
              {{ t('products.detail.applicationScenarios') }}
            </h2>
          </AnimatedSection>
          <AnimatedSection
            animation="fade-in-up"
            :delay="100"
          >
            <div class="bg-surface-elevated rounded-2xl shadow-card p-6 md:p-8">
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div
                  v-for="(scenario, index) in parseScenarios(product.application_scenarios)"
                  :key="index"
                  class="scenario-item p-4 bg-surface rounded-xl flex items-center space-x-3 hover:shadow-soft transition-all duration-300"
                >
                  <svg
                    class="w-5 h-5 text-primary flex-shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <span class="text-text-primary">{{ scenario }}</span>
                </div>
              </div>
            </div>
          </AnimatedSection>
        </div>
      </section>

      <!-- Advantages -->
      <section
        class="py-16 bg-gradient-to-br from-primary/5 via-surface-elevated to-accent/5"
        v-if="product.advantages"
      >
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <AnimatedSection
            animation="fade-in-up"
            :delay="0"
          >
            <h2 class="section-title text-center mb-12">
              {{ t('products.detail.advantages') }}
            </h2>
          </AnimatedSection>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <AnimatedSection
              v-for="(advantage, index) in parseAdvantages(product.advantages)"
              :key="index"
              animation="fade-in-up"
              :delay="index * 100"
            >
              <div
                class="advantage-card p-6 bg-surface rounded-2xl shadow-card text-center hover:shadow-card-hover hover:-translate-y-2 transition-all duration-300"
              >
                <div
                  class="w-12 h-12 mx-auto mb-4 bg-gradient-to-br from-primary/10 to-accent/10 rounded-xl flex items-center justify-center"
                >
                  <svg
                    class="w-6 h-6 text-primary"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"
                    />
                  </svg>
                </div>
                <h3 class="text-lg font-semibold text-text-primary">
                  {{ advantage }}
                </h3>
              </div>
            </AnimatedSection>
          </div>
        </div>
      </section>

      <!-- CTA Section -->
      <section class="py-16">
        <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <AnimatedSection
            animation="fade-in-up"
            :delay="0"
          >
            <div
              class="bg-gradient-to-r from-primary to-primary-dark rounded-3xl p-8 md:p-12 text-center text-white relative overflow-hidden"
            >
              <div
                class="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 animate-float"
              />
              <div
                class="absolute bottom-0 left-0 w-48 h-48 bg-white/10 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2 animate-float-delayed"
              />
              <div class="relative">
                <h2 class="text-2xl md:text-3xl font-bold mb-4">
                  {{ t('products.detail.needMoreInfo') }}
                </h2>
                <p class="text-lg text-white/80 mb-8">
                  {{ t('products.detail.infoDesc') }}
                </p>
                <div class="flex flex-wrap justify-center gap-4">
                  <NuxtLink
                    to="/contact"
                    class="inline-flex items-center px-8 py-4 bg-white text-primary font-semibold rounded-xl hover:bg-gray-100 transition-all duration-300"
                  >
                    {{ t('products.detail.onlineMessage') }}
                  </NuxtLink>
                  <a
                    :href="`tel:${contactPhone}`"
                    class="inline-flex items-center px-8 py-4 border-2 border-white text-white font-semibold rounded-xl hover:bg-white/10 transition-all duration-300"
                  >
                    {{ t('products.detail.phonePrefix') }}{{ contactPhone }}
                  </a>
                </div>
              </div>
            </div>
          </AnimatedSection>
        </div>
      </section>

      <!-- FAQ Section (GEO Optimized) -->
      <section v-if="faqs.length" class="py-12 bg-surface-elevated">
        <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <AnimatedSection animation="fade-in-up" :delay="0">
            <h2 class="section-title text-center mb-8">{{ t('products.detail.faqTitle', '常见问题') }}</h2>
          </AnimatedSection>
          <div class="space-y-4">
            <div
              v-for="(faq, idx) in faqs"
              :key="faq.id"
              class="bg-surface border border-border rounded-xl p-5 sm:p-6"
            >
              <h3 class="text-base font-semibold text-text-primary mb-2">
                {{ currentLocale === 'en' && faq.question_en ? faq.question_en : faq.question_zh }}
              </h3>
              <p class="text-sm text-text-secondary leading-relaxed">
                {{ currentLocale === 'en' && faq.answer_en ? faq.answer_en : faq.answer_zh }}
              </p>
            </div>
          </div>
        </div>
      </section>

      <!-- Case Studies Section -->
      <section v-if="caseStudies.length" class="py-12">
        <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <AnimatedSection animation="fade-in-up" :delay="0">
            <h2 class="section-title text-center mb-8">{{ t('products.detail.casesTitle', '工程案例') }}</h2>
          </AnimatedSection>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div
              v-for="cs in caseStudies"
              :key="cs.id"
              class="bg-surface border border-border rounded-xl overflow-hidden hover:shadow-card-hover transition-all"
            >
              <img
                v-if="cs.image_url"
                :src="cs.image_url"
                :alt="cs.title"
                class="w-full h-48 object-cover"
              >
              <div class="p-5">
                <h3 class="font-semibold text-text-primary mb-2">{{ currentLocale === 'en' && cs.title_en ? cs.title_en : cs.title }}</h3>
                <p class="text-sm text-text-secondary line-clamp-3">
                  {{ currentLocale === 'en' && cs.summary_en ? cs.summary_en : cs.summary }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Test Reports Section -->
      <section v-if="documents.length" class="py-12 bg-surface-elevated">
        <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <AnimatedSection animation="fade-in-up" :delay="0">
            <h2 class="section-title text-center mb-8">{{ t('products.detail.docsTitle', '检测报告与资料') }}</h2>
          </AnimatedSection>
          <div class="space-y-3">
            <div
              v-for="doc in documents"
              :key="doc.id"
              class="flex items-center gap-4 bg-surface border border-border rounded-xl p-4 hover:border-primary/30 transition-colors"
            >
              <div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                <svg class="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-text-primary truncate">{{ doc.file_name }}</p>
                <p v-if="doc.description" class="text-xs text-text-muted">{{ doc.description }}</p>
              </div>
              <a
                :href="doc.file_path"
                target="_blank"
                class="text-sm font-medium text-primary hover:text-primary-hover flex-shrink-0"
              >
                {{ t('products.detail.download', '下载') }}
              </a>
            </div>
          </div>
        </div>
      </section>

      <!-- Get Quote Section -->
      <section class="py-16 bg-gradient-to-br from-primary/5 via-surface-elevated to-accent/5">
        <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <AnimatedSection animation="fade-in-up" :delay="0">
            <h2 class="section-title text-center mb-4">{{ t('products.detail.getQuoteTitle') }}</h2>
            <p class="text-center text-text-secondary mb-8 sm:mb-10">
              {{ t('products.detail.getQuoteDesc') }}
            </p>
          </AnimatedSection>
          <AnimatedSection animation="fade-in-up" :delay="100">
            <form
              class="bg-surface rounded-2xl p-6 sm:p-8 md:p-10 border border-border shadow-card"
              @submit.prevent="handleQuoteSubmit"
            >
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-5">
                <div>
                  <label class="block text-xs sm:text-sm font-semibold text-text-primary mb-1.5">{{ t('products.detail.quoteNameLabel') }} <span class="text-danger">{{ t('products.detail.required') }}</span></label>
                  <input
                    v-model="quoteForm.name"
                    required
                    class="w-full px-3 py-2.5 sm:px-4 sm:py-3 bg-surface-elevated border border-border rounded-lg sm:rounded-xl text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-sm"
                    :placeholder="t('products.detail.quoteNamePlaceholder')"
                  >
                </div>
                <div>
                  <label class="block text-xs sm:text-sm font-semibold text-text-primary mb-1.5">{{ t('products.detail.quotePhoneLabel') }} <span class="text-danger">{{ t('products.detail.required') }}</span></label>
                  <input
                    v-model="quoteForm.phone"
                    required
                    type="tel"
                    class="w-full px-3 py-2.5 sm:px-4 sm:py-3 bg-surface-elevated border border-border rounded-lg sm:rounded-xl text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-sm"
                    :placeholder="t('products.detail.quotePhonePlaceholder')"
                  >
                </div>
                <div>
                  <label class="block text-xs sm:text-sm font-semibold text-text-primary mb-1.5">{{ t('products.detail.quoteWechatLabel') }}</label>
                  <input
                    v-model="quoteForm.wechat"
                    class="w-full px-3 py-2.5 sm:px-4 sm:py-3 bg-surface-elevated border border-border rounded-lg sm:rounded-xl text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-sm"
                    :placeholder="t('products.detail.quoteWechatPlaceholder')"
                  >
                </div>
                <div>
                  <label class="block text-xs sm:text-sm font-semibold text-text-primary mb-1.5">{{ t('products.detail.quoteQuantityLabel') }}</label>
                  <input
                    v-model="quoteForm.quantity"
                    class="w-full px-3 py-2.5 sm:px-4 sm:py-3 bg-surface-elevated border border-border rounded-lg sm:rounded-xl text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-sm"
                    :placeholder="t('products.detail.quoteQuantityPlaceholder')"
                  >
                </div>
              </div>
              <button
                type="submit"
                :disabled="quoteSubmitting"
                class="w-full mt-6 sm:mt-8 px-6 py-3.5 sm:py-4 bg-gradient-to-r from-primary to-primary-dark text-white font-bold text-base sm:text-lg rounded-xl hover:shadow-lg hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 shadow-md"
              >
                <svg
                  v-if="!quoteSubmitting"
                  class="w-5 h-5 inline-block mr-2 -mt-0.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                  />
                </svg>
                <span v-if="quoteSubmitting">{{ t('products.detail.quoteSubmitting') }}</span>
                <span v-else>{{ t('products.detail.quoteSubmit') }}</span>
              </button>
              <p
                v-if="quoteSuccess"
                class="text-green-600 text-center font-medium mt-4 text-sm sm:text-base flex items-center justify-center"
              >
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                {{ t('products.detail.quoteSuccess') }}
              </p>
              <p
                v-if="quoteError"
                class="text-danger text-center font-medium mt-4 text-sm"
              >
                {{ quoteError }}
              </p>
            </form>
          </AnimatedSection>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, reactive } from 'vue';
import { useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useProductStore } from '~/stores/product';
import { SITE_CONFIG } from '~/config/site';
import { useApi } from '~/composables/useApi';

const route = useRoute();
const { t } = useI18n();
const productStore = useProductStore();

const { slug } = route.params as { slug: string };

await productStore.fetchProductBySlug(slug);

const product = computed(() => productStore.currentProduct);
const loading = computed(() => productStore.loading);
const error = computed(() => productStore.error);

const contactPhone = SITE_CONFIG.phone;

const { request } = useApi();
const { locale } = useI18n();
const currentLocale = computed(() => locale.value);

// FAQ, Case Studies, Documents
const faqs = ref<any[]>([]);
const caseStudies = ref<any[]>([]);
const documents = ref<any[]>([]);

async function loadProductExtras() {
  const pid = product.value?.id;
  if (!pid) return;
  try {
    const [faqRes, csRes] = await Promise.all([
      request(`/api/v1/product-faqs/product/${pid}`).catch(() => ({ data: [] })),
      request(`/api/v1/case-studies?product_id=${pid}`).catch(() => ({ data: [] })),
    ]);
    faqs.value = faqRes.data || [];
    caseStudies.value = (csRes.data || []).slice(0, 3);
    documents.value = (product.value?.documents || []).filter((d: any) => d.is_active);
  } catch { /* ignore */ }
}

watch(product, () => { if (product.value) loadProductExtras(); }, { immediate: true });

const quoteForm = reactive({
  name: '',
  phone: '',
  wechat: '',
  quantity: '',
});

const quoteSubmitting = ref(false);
const quoteSuccess = ref(false);
const quoteError = ref('');

async function handleQuoteSubmit() {
  quoteSuccess.value = false;
  quoteError.value = '';

  if (!quoteForm.name.trim()) {
    quoteError.value = t('products.detail.quoteErrorRequired');
    return;
  }
  if (!quoteForm.phone.trim()) {
    quoteError.value = t('products.detail.quoteErrorPhoneRequired');
    return;
  }
  if (!/^1[3-9]\d{9}$/.test(quoteForm.phone)) {
    quoteError.value = t('products.detail.quoteErrorPhoneInvalid');
    return;
  }

  quoteSubmitting.value = true;
  try {
    await request('/inquiries', {
      method: 'POST',
      body: {
        name: quoteForm.name,
        phone: quoteForm.phone,
        wechat: quoteForm.wechat,
        message: `产品: ${product.value?.name || ''} | 需求量: ${quoteForm.quantity || '未填写'}`,
      },
    });
    quoteSuccess.value = true;
    quoteForm.name = '';
    quoteForm.phone = '';
    quoteForm.wechat = '';
    quoteForm.quantity = '';
  } catch (e: any) {
    quoteError.value = e.message || t('products.detail.quoteErrorFailed');
  } finally {
    quoteSubmitting.value = false;
  }
}

useHead({
  title: computed(() =>
    product.value
      ? `${product.value.name} - ${product.value.subtitle || ''} | ${t('products.seo.detailTitle')}`
      : t('products.seo.detailTitle')
  ),
  meta: [
    {
      name: 'description',
      content: computed(() => product.value?.meta_description || product.value?.description || ''),
    },
    { property: 'og:title', content: computed(() => product.value?.name || '') },
    { property: 'og:description', content: computed(() => product.value?.description || '') },
    { property: 'og:type', content: 'product' },
    {
      property: 'og:url',
      content: computed(() => `${SITE_CONFIG.url}/products/${slug}`),
    },
    {
      property: 'og:image',
      content: computed(
        () => product.value?.image_url || `${SITE_CONFIG.url}${SITE_CONFIG.ogImage}`
      ),
    },
    { name: 'twitter:card', content: 'summary_large_image' },
    { name: 'twitter:title', content: computed(() => product.value?.name || '') },
    { name: 'twitter:description', content: computed(() => product.value?.description || '') },
  ],
  link: [{ rel: 'canonical', href: `${SITE_CONFIG.url}/products/${slug}` }],
  script: computed(() => {
    if (!product.value) return [];
    const scripts: any[] = [];

    // Product Schema.org (bilingual)
    scripts.push({
      type: 'application/ld+json',
      children: JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'Product',
        name: product.value.name_en || product.value.name,
        description: product.value.description_en || product.value.description || '',
        image: product.value.image_url || `${SITE_CONFIG.url}${SITE_CONFIG.productDefaultImage}`,
        brand: { '@type': 'Brand', name: SITE_CONFIG.name },
        manufacturer: {
          '@type': 'Organization',
          name: SITE_CONFIG.fullName,
          address: {
            '@type': 'PostalAddress',
            addressCountry: 'CN',
          },
        },
        offers: {
          '@type': 'Offer',
          url: `${SITE_CONFIG.url}/products/${slug}`,
          priceCurrency: 'CNY',
          availability: 'https://schema.org/InStock',
          seller: { '@type': 'Organization', name: SITE_CONFIG.fullName },
        },
        additionalProperty: [
          product.value.density && { '@type': 'PropertyValue', name: 'density', value: product.value.density },
          product.value.strength && { '@type': 'PropertyValue', name: 'compressive_strength', value: product.value.strength },
          product.value.thermal_conductivity && { '@type': 'PropertyValue', name: 'thermal_conductivity', value: product.value.thermal_conductivity },
          product.value.fire_rating && { '@type': 'PropertyValue', name: 'fire_rating', value: product.value.fire_rating },
        ].filter(Boolean),
      }),
    });

    // FAQPage Schema.org (GEO key signal)
    if (faqs.value.length > 0) {
      scripts.push({
        type: 'application/ld+json',
        children: JSON.stringify({
          '@context': 'https://schema.org',
          '@type': 'FAQPage',
          mainEntity: faqs.value.map((faq: any) => ({
            '@type': 'Question',
            name: faq.question_en || faq.question_zh,
            acceptedAnswer: {
              '@type': 'Answer',
              text: faq.answer_en || faq.answer_zh,
            },
          })),
        }),
      });
    }

    return scripts;
  }),
});

const parseScenarios = (text: string | null): string[] => {
  if (!text) return [];
  return text
    .split('\n')
    .filter((s) => s.trim())
    .map((s) => s.replace(/^[-•]\s*/, '').trim());
};

const parseAdvantages = (text: string | null): string[] => {
  if (!text) return [];
  return text
    .split('\n')
    .filter((s) => s.trim())
    .map((s) => s.replace(/^[-•]\s*/, '').trim());
};
</script>

<style scoped>
.loading-container {
  min-height: 60vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(102, 126, 234, 0.2);
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-container {
  min-height: 60vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.error-container h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: #ef4444;
  margin-bottom: 0.5rem;
}

.error-container p {
  color: #6b7280;
  margin-bottom: 1.5rem;
}

.section-title {
  font-size: 1.875rem;
  font-weight: 700;
  color: #111827;
  margin-bottom: 3rem;
}

@media (max-width: 768px) {
  .section-title {
    font-size: 1.5rem;
    margin-bottom: 2rem;
  }
}
</style>
