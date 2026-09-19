/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="min-h-screen bg-white">
    <!-- 首屏 Hero 区 - 移动端优先，1.5秒内可见 -->
    <section class="relative bg-gradient-to-br from-green-50 to-blue-50 py-16 px-4">
      <div class="max-w-4xl mx-auto text-center">
        <h1 class="text-3xl md:text-4xl font-extrabold text-gray-900 mb-4 leading-tight">
          {{ t('meta.title') }}
        </h1>
        <p class="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
          {{ t('meta.description') }}
        </p>
        <div class="flex flex-col sm:flex-row gap-3 justify-center">
          <a
            :href="imLink"
            target="_blank"
            rel="noopener"
            class="inline-flex items-center justify-center px-6 py-3 bg-green-500 hover:bg-green-600 text-white font-bold rounded-xl transition-colors active:scale-95"
          >
            {{ t('product.chat_now') }}
          </a>
          <button
            @click="showForm = true"
            class="inline-flex items-center justify-center px-6 py-3 bg-orange-500 hover:bg-orange-600 text-white font-bold rounded-xl transition-colors active:scale-95"
          >
            {{ t('product.free_sample') }}
          </button>
        </div>
      </div>
    </section>

    <!-- 产品列表区 -->
    <section class="py-12 px-4 max-w-6xl mx-auto">
      <h2 class="text-2xl font-bold text-gray-900 mb-6">
        {{ t('product.title') }}
      </h2>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="product in products"
          :key="product.id"
          class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow cursor-pointer"
          @click="goProduct(product.id)"
        >
          <img
            v-if="product.image_url"
            :src="product.image_url"
            :alt="product.name"
            class="w-full h-48 object-cover"
            loading="lazy"
          >
          <div class="p-4">
            <h3 class="font-bold text-gray-900 mb-1">
              {{ product.name }}
            </h3>
            <p class="text-sm text-gray-500 mb-3">
              {{ product.subtitle }}
            </p>
            <div class="flex gap-2">
              <span
                v-for="badge in product.trust_badges || []"
                :key="badge"
                class="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded"
              >{{ badge }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 物流时间线 -->
    <section class="py-12 px-4 bg-gray-50">
      <div class="max-w-4xl mx-auto">
        <ShippingTimeline :country-code="buyerCountry" />
      </div>
    </section>

    <!-- 询盘抽屉 -->
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
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import StickyImBar from '~/components/StickyImBar.vue'
import ShippingTimeline from '~/components/ShippingTimeline.vue'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()

const products = ref<any[]>([])
const buyerCountry = ref('US')
const showForm = ref(false)
const form = ref({ name: '', email: '', spec: '' })

// IM链接（首页默认）
const imLink = ref('#')

const fetchProducts = async () => {
  try {
    const res = await $fetch('/api/v1/products', { params: { merchant_id: 'default', limit: 12 } })
    products.value = res.items || res || []
  } catch (e) {
    console.error('Failed to fetch products:', e)
  }
}

const goProduct = (id: string) => {
  router.push(`/${locale.value}/product/${id}`)
}

const submitForm = async () => {
  try {
    await $fetch('/api/v1/inquiries', {
      method: 'POST',
      body: {
        name: form.value.name,
        email: form.value.email,
        message: form.value.spec,
        product: '',
        source_channel: 'form',
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
  fetchProducts()
})
</script>
