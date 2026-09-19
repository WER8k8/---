/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 产品详情页 - SSR渲染，SEO友好 -->
    <div class="max-w-4xl mx-auto px-4 py-8">
      <!-- 产品标题区 -->
      <div class="mb-6">
        <h1 class="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
          {{ product?.name || t('product.title') }}
        </h1>
        <p class="text-lg text-gray-600 mb-4">
          {{ product?.subtitle || t('product.subtitle') }}
        </p>

        <!-- Meta描述（SEO） -->
        <MetaHead
          :title="product?.meta_title || t('meta.title')"
          :description="product?.meta_description || t('meta.description')"
          :og-image="product?.image_url"
        />
      </div>

      <!-- 产品图片 -->
      <div
        v-if="product?.image_url"
        class="mb-8 rounded-2xl overflow-hidden shadow-lg"
      >
        <img
          :src="product.image_url"
          :alt="product?.name"
          class="w-full h-auto object-cover"
          loading="lazy"
        >
      </div>

      <!-- 技术参数折叠框 -->
      <ProductSpecAccordion
        :title="t('product.title') + ' - ' + t('product.spec_weight')"
        :specs="specsList"
        :badges="trustBadges"
        :default-open="true"
        class="mb-6"
      />

      <!-- 物流时间线 -->
      <ShippingTimeline
        :country-code="buyerCountry"
        class="mb-8"
      />

      <!-- 产品描述 -->
      <div
        v-if="product?.description"
        class="prose max-w-none mb-8"
        v-html="sanitizedDescription"
      />

      <!-- 底部CTA -->
      <div class="sticky bottom-0 bg-white border-t border-gray-200 p-4 -mx-4">
        <div class="flex gap-3 max-w-4xl mx-auto">
          <a
            :href="imLink"
            target="_blank"
            rel="noopener"
            class="flex-1 bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-4 rounded-xl text-center transition-colors active:scale-95"
          >
            {{ t('product.chat_now') }}
          </a>
          <button
            @click="showForm = true"
            class="flex-1 bg-orange-500 hover:bg-orange-600 text-white font-bold py-3 px-4 rounded-xl text-center transition-colors active:scale-95"
          >
            {{ t('product.free_sample') }}
          </button>
        </div>
      </div>
    </div>

    <!-- 询盘抽屉表单 -->
    <Transition name="slide-up">
      <div
        v-if="showForm"
        class="fixed inset-0 z-[60] bg-white overflow-y-auto"
      >
        <div
          class="h-1.5 w-10 bg-gray-300 rounded-full mx-auto mt-2 cursor-pointer"
          @click="showForm = false"
        />
        <div class="p-6 space-y-5">
          <h3 class="text-xl font-bold text-gray-800">
            {{ t('chat.form_title') }}
          </h3>
          <form
            @submit.prevent="submitForm"
            class="space-y-4"
          >
            <input
              v-model="form.name"
              type="text"
              :placeholder="t('chat.form_name')"
              class="w-full p-4 text-lg border-b-2 border-gray-200 focus:border-green-500 outline-none"
              required
            >
            <input
              v-model="form.email"
              type="email"
              :placeholder="t('chat.form_email')"
              class="w-full p-4 text-lg border-b-2 border-gray-200 focus:border-green-500 outline-none"
              required
            >
            <textarea
              v-model="form.spec"
              :placeholder="t('chat.form_spec')"
              class="w-full p-4 text-lg border-b-2 border-gray-200 focus:border-green-500 outline-none h-32 resize-none"
            />
            <button
              type="submit"
              class="w-full py-4 bg-green-500 hover:bg-green-600 text-white text-lg font-bold rounded-xl transition-colors active:scale-95"
            >
              {{ t('chat.form_submit') }}
            </button>
          </form>
        </div>
      </div>
    </Transition>

    <!-- 吸底IM条 -->
    <StickyImBar />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import ProductSpecAccordion from '~/components/ProductSpecAccordion.vue'
import ShippingTimeline from '~/components/ShippingTimeline.vue'
import StickyImBar from '~/components/StickyImBar.vue'
import { useSanitize } from '~/composables/useSanitize'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()

// 产品数据
const product = ref<any>(null)
const imChannels = ref<any[]>([])
const { sanitizeHtml } = useSanitize()
const sanitizedDescription = computed(() => sanitizeHtml(product.value?.description || ''))
const buyerCountry = ref('US')
const showForm = ref(false)

// 表单
const form = ref({ name: '', email: '', spec: '' })

// 技术参数列表（从product.specifications转换）
const specsList = computed(() => {
  if (!product.value?.specifications) return []
  const specs = product.value.specifications
  return [
    { key: t('product.spec_weight'), value: specs.weight || '-', metric_unit: 'g/m²', imperial_unit: 'oz/yd²' },
    { key: t('product.spec_mesh'), value: specs.mesh_size || '-', metric_unit: 'mm', imperial_unit: 'inch' },
    { key: t('product.spec_tensile'), value: specs.tensile_strength || '-', metric_unit: 'N/5cm', imperial_unit: 'lbf/in' },
    { key: t('product.spec_alkali'), value: specs.alkali_resistance || '-', metric_unit: '%', imperial_unit: '%' }
  ].filter(s => s.value !== '-')
})

// 证书徽章
const trustBadges = computed(() => {
  if (!product.value?.specifications?.trust_badges) return []
  return product.value.specifications.trust_badges
})

// IM链接
const imLink = computed(() => {
  const ch = imChannels.value[0]
  if (!ch) return '#'
  if (ch.channel_type === 'whatsapp') return `https://wa.me/${ch.account_id}?text=${encodeURIComponent(t('chat.welcome'))}`
  if (ch.channel_type === 'telegram') return `https://t.me/${ch.account_id}`
  return '#'
})

// 获取产品数据（SSR阶段完成）
const fetchProduct = async () => {
  try {
    const res = await $fetch('/api/v1/mobile/product/' + route.params.id, {
      params: {
        country: buyerCountry.value,
        merchant_id: 'default'
      }
    })
    product.value = res.product
    imChannels.value = res.im_channels || []
  } catch (e) {
    console.error('Failed to fetch product:', e)
  }
}

const submitForm = async () => {
  try {
    await $fetch('/api/v1/inquiries', {
      method: 'POST',
      body: {
        name: form.value.name,
        email: form.value.email,
        message: form.value.spec,
        product: route.params.id as string,
        source_channel: imChannels.value[0]?.channel_type || 'form',
        merchant_id: 'default'
      }
    })
    alert(t('chat.form_submit') + ' - Success!')
    showForm.value = false
    form.value = { name: '', email: '', spec: '' }
  } catch (e) {
    alert('Error: ' + (e.data?.detail || e.message))
  }
}

onMounted(() => {
  const country = route.query.country as string || 'US'
  buyerCountry.value = country
  fetchProduct()
})
</script>

<style scoped>
.prose h2 { @apply text-xl font-bold mt-6 mb-3; }
.prose p { @apply text-gray-700 mb-4; }
.prose ul { @apply list-disc pl-5 mb-4; }
.prose li { @apply text-gray-700 mb-1; }
</style>
