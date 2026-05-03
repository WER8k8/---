<template>
  <div class="product-detail-page">
    <div
      v-if="loading"
      class="loading-container"
    >
      <div class="loading-spinner" />
      <p>加载中...</p>
    </div>

    <div
      v-else-if="error"
      class="error-container"
    >
      <h2>加载失败</h2>
      <p>{{ error }}</p>
      <NuxtLink
        to="/products"
        class="btn-primary"
      >
        返回产品列表
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
                首页
              </NuxtLink>
            </li>
            <li><span class="mx-2">/</span></li>
            <li>
              <NuxtLink
                to="/products"
                class="hover:text-primary transition-colors"
              >
                产品中心
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
      <section class="product-hero bg-gradient-to-br from-primary/5 via-surface to-accent/5 py-12 md:py-20">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
            <!-- Product Image -->
            <AnimatedSection
              animation="slide-right"
              :delay="100"
            >
              <div class="product-image-container rounded-2xl overflow-hidden shadow-card bg-surface-elevated">
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
                      密度
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
                      强度
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
                      导热系数
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
                      防火等级
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
                    立即咨询
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
                    电话咨询
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
              技术参数
            </h2>
          </AnimatedSection>
          <AnimatedSection
            animation="fade-in-up"
            :delay="100"
          >
            <div class="bg-surface rounded-2xl shadow-card p-6 md:p-8">
              <pre class="whitespace-pre-wrap text-text-secondary leading-relaxed font-sans">{{ product.technical_params }}</pre>
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
              应用场景
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
              产品优势
            </h2>
          </AnimatedSection>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <AnimatedSection 
              v-for="(advantage, index) in parseAdvantages(product.advantages)" 
              :key="index"
              animation="fade-in-up"
              :delay="index * 100"
            >
              <div class="advantage-card p-6 bg-surface rounded-2xl shadow-card text-center hover:shadow-card-hover hover:-translate-y-2 transition-all duration-300">
                <div class="w-12 h-12 mx-auto mb-4 bg-gradient-to-br from-primary/10 to-accent/10 rounded-xl flex items-center justify-center">
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
            <div class="bg-gradient-to-r from-primary to-primary-dark rounded-3xl p-8 md:p-12 text-center text-white relative overflow-hidden">
              <div class="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 animate-float" />
              <div class="absolute bottom-0 left-0 w-48 h-48 bg-white/10 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2 animate-float-delayed" />
              <div class="relative">
                <h2 class="text-2xl md:text-3xl font-bold mb-4">
                  需要更多产品信息？
                </h2>
                <p class="text-lg text-white/80 mb-8">
                  专业工程师为您提供产品选型和技术支持
                </p>
                <div class="flex flex-wrap justify-center gap-4">
                  <NuxtLink
                    to="/contact"
                    class="inline-flex items-center px-8 py-4 bg-white text-primary font-semibold rounded-xl hover:bg-gray-100 transition-all duration-300"
                  >
                    在线留言
                  </NuxtLink>
                  <a
                    :href="`tel:${contactPhone}`"
                    class="inline-flex items-center px-8 py-4 border-2 border-white text-white font-semibold rounded-xl hover:bg-white/10 transition-all duration-300"
                  >
                    电话咨询：{{ contactPhone }}
                  </a>
                </div>
              </div>
            </div>
          </AnimatedSection>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useProductStore } from '~/stores/product'
import { SITE_CONFIG } from '~/config/site'

const route = useRoute()
const productStore = useProductStore()

const { slug } = route.params as { slug: string }

await productStore.fetchProductBySlug(slug)

const product = computed(() => productStore.currentProduct)
const loading = computed(() => productStore.loading)
const error = computed(() => productStore.error)

const contactPhone = SITE_CONFIG.phone

useHead({
  title: computed(() => product.value ? `${product.value.name} - ${product.value.subtitle || ''} | 优丁建材` : '产品详情 | 优丁建材'),
  meta: [
    { name: 'description', content: computed(() => product.value?.meta_description || product.value?.description || '') },
    { property: 'og:title', content: computed(() => product.value?.name || '') },
    { property: 'og:description', content: computed(() => product.value?.description || '') },
    { property: 'og:type', content: 'product' },
    { property: 'og:url', content: computed(() => `https://www.youdingjiancai.com/products/${slug}`) },
    { property: 'og:image', content: computed(() => product.value?.image_url || 'https://www.youdingjiancai.com/images/og-default.jpg') },
    { name: 'twitter:card', content: 'summary_large_image' },
    { name: 'twitter:title', content: computed(() => product.value?.name || '') },
    { name: 'twitter:description', content: computed(() => product.value?.description || '') }
  ],
  link: [
    { rel: 'canonical', href: `https://www.youdingjiancai.com/products/${slug}` }
  ],
  script: computed(() => product.value ? [{
    type: 'application/ld+json',
    children: JSON.stringify({
      '@context': 'https://schema.org',
      '@type': 'Product',
      name: product.value.name,
      description: product.value.description || '',
      image: product.value.image_url || 'https://www.youdingjiancai.com/images/product-default.jpg',
      brand: {
        '@type': 'Brand',
        name: '优丁建材'
      },
      offers: {
        '@type': 'Offer',
        url: `https://www.youdingjiancai.com/products/${slug}`,
        priceCurrency: 'CNY',
        availability: 'https://schema.org/InStock',
        seller: {
          '@type': 'Organization',
          name: '优丁建材有限公司'
        }
      },
      additionalProperty: [
        product.value.density && { '@type': 'PropertyValue', name: '密度', value: product.value.density },
        product.value.strength && { '@type': 'PropertyValue', name: '强度', value: product.value.strength },
        product.value.thermal_conductivity && { '@type': 'PropertyValue', name: '导热系数', value: product.value.thermal_conductivity },
        product.value.fire_rating && { '@type': 'PropertyValue', name: '防火等级', value: product.value.fire_rating }
      ].filter(Boolean)
    })
  }] : [])
})

const parseScenarios = (text: string | null): string[] => {
  if (!text) return []
  return text.split('\n').filter(s => s.trim()).map(s => s.replace(/^[-•]\s*/, '').trim())
}

const parseAdvantages = (text: string | null): string[] => {
  if (!text) return []
  return text.split('\n').filter(s => s.trim()).map(s => s.replace(/^[-•]\s*/, '').trim())
}
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
  to { transform: rotate(360deg); }
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
