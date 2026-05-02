<template>
  <div>
    <section
      v-if="loading"
      class="py-20 text-center"
    >
      <div class="flex items-center justify-center">
        <div class="w-8 h-8 border-2 border-secondary-500 border-t-transparent rounded-full animate-spin" />
        <span class="ml-3 text-text-muted">加载中...</span>
      </div>
    </section>

    <template v-else-if="caseItem">
      <section class="relative overflow-hidden bg-gradient-to-br from-primary-900 via-primary-800 to-secondary-700">
        <div class="absolute inset-0 opacity-10">
          <div class="absolute top-1/4 right-1/4 w-96 h-96 bg-secondary-400 rounded-full blur-3xl" />
          <div class="absolute bottom-1/4 left-1/4 w-80 h-80 bg-accent-400 rounded-full blur-3xl" />
        </div>
        <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-24">
          <NuxtLink
            to="/cases"
            class="text-white/70 hover:text-white mb-4 inline-block flex items-center gap-1 transition-colors"
          >
            <svg
              class="w-4 h-4"
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
            返回案例列表
          </NuxtLink>
          <div class="max-w-4xl">
            <span class="text-sm font-medium bg-white/10 text-white px-3 py-1 rounded-full">工程案例</span>
            <h1 class="text-3xl md:text-5xl font-bold text-white mt-4 mb-4">
              {{ caseItem.project_name }}
            </h1>
            <p
              v-if="caseItem.client_name"
              class="text-xl text-white/80 flex items-center gap-2"
            >
              <svg
                class="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                />
              </svg>
              {{ caseItem.client_name }}
            </p>
          </div>
        </div>
      </section>

      <section class="py-12 bg-gradient-to-b from-surface-elevated to-surface">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div
              v-if="caseItem.construction_area"
              class="bg-white rounded-xl p-5 border border-border hover:border-secondary-200 hover:shadow-card-hover transition-all text-center"
            >
              <div class="text-xs text-text-muted mb-1">
                施工面积
              </div>
              <div class="text-lg font-bold text-secondary-600">
                {{ caseItem.construction_area }}
              </div>
            </div>
            <div
              v-if="caseItem.project_date"
              class="bg-white rounded-xl p-5 border border-border hover:border-secondary-200 hover:shadow-card-hover transition-all text-center"
            >
              <div class="text-xs text-text-muted mb-1">
                完工时间
              </div>
              <div class="text-lg font-bold text-secondary-600">
                {{ caseItem.project_date }}
              </div>
            </div>
            <div
              v-if="caseItem.location"
              class="bg-white rounded-xl p-5 border border-border hover:border-secondary-200 hover:shadow-card-hover transition-all text-center"
            >
              <div class="text-xs text-text-muted mb-1">
                项目地点
              </div>
              <div class="text-lg font-bold text-secondary-600">
                {{ caseItem.location }}
              </div>
            </div>
            <div
              v-if="caseItem.materials_used"
              class="bg-white rounded-xl p-5 border border-border hover:border-secondary-200 hover:shadow-card-hover transition-all text-center"
            >
              <div class="text-xs text-text-muted mb-1">
                使用材料
              </div>
              <div class="text-lg font-bold text-secondary-600">
                {{ caseItem.materials_used }}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section
        v-if="caseItem.images && caseItem.images.length"
        class="py-16 bg-surface"
      >
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="inline-flex items-center px-3 py-1.5 bg-accent-50 rounded-full mb-4">
            <span class="w-1.5 h-1.5 bg-accent-500 rounded-full mr-2" />
            <span class="text-sm font-medium text-accent-600">项目图集</span>
          </div>
          <h2 class="text-2xl md:text-3xl font-bold text-primary-900 mb-6">
            项目展示
          </h2>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
            <a
              v-for="img in caseItem.images"
              :key="img.id"
              :href="img.image_url"
              target="_blank"
              class="aspect-[4/3] overflow-hidden rounded-xl group"
            >
              <img
                :src="img.image_url"
                :alt="img.image_alt || caseItem.project_name"
                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              >
            </a>
          </div>
        </div>
      </section>

      <section
        v-if="caseItem.description"
        class="py-16 bg-gradient-to-b from-surface to-surface-elevated"
      >
        <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="inline-flex items-center px-3 py-1.5 bg-secondary-50 rounded-full mb-4">
            <span class="w-1.5 h-1.5 bg-secondary-500 rounded-full mr-2" />
            <span class="text-sm font-medium text-secondary-600">项目详情</span>
          </div>
          <h2 class="text-2xl md:text-3xl font-bold text-primary-900 mb-6">
            项目概述
          </h2>
          <div
            class="bg-white rounded-2xl p-8 border border-border"
            v-html="caseItem.description"
          />
        </div>
      </section>
    </template>

    <section
      v-else
      class="py-20 text-center bg-surface"
    >
      <div class="w-20 h-20 bg-surface-elevated rounded-full flex items-center justify-center mx-auto mb-4">
        <svg
          class="w-10 h-10 text-text-muted"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </div>
      <p class="text-text-muted text-lg">
        案例不存在
      </p>
      <NuxtLink
        to="/cases"
        class="mt-4 inline-flex items-center text-secondary-600 font-medium hover:text-secondary-700"
      >
        <svg
          class="w-4 h-4 mr-1"
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
        返回案例列表
      </NuxtLink>
    </section>

    <section class="py-16 bg-gradient-to-r from-secondary-600 via-secondary-500 to-accent-500">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 class="text-3xl font-bold text-white mb-4">
          需要类似解决方案？
        </h2>
        <p class="text-white/80 mb-8 max-w-2xl mx-auto">
          我们的技术团队根据您的工程需求提供定制化保温方案
        </p>
        <NuxtLink
          to="/contact"
          class="inline-flex items-center px-8 py-4 bg-white text-secondary-600 font-semibold rounded-xl hover:bg-gray-100 transition-all shadow-lg"
        >
          <svg
            class="w-5 h-5 mr-2"
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
          免费获取方案
        </NuxtLink>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watchEffect } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const loading = ref(false)
const caseItem = ref<any>(null)

const slug = computed(() => route.params.slug as string)

async function fetchCase() {
  loading.value = true
  try {
    const res = await fetch(`/api/v1/cases/by-slug/${slug.value}`)
    if (res.ok) {
      caseItem.value = await res.json()
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchCase)

watchEffect(() => {
  if (caseItem.value) {
    useHead({
      title: `${caseItem.value.project_name} - 优丁保温材料案例`,
      meta: [
        { name: 'description', content: `${caseItem.value.project_name}案例，使用${caseItem.value.materials_used || '优质保温材料'}，施工面积${caseItem.value.construction_area || '若干'}，位于${caseItem.value.location || '项目工地'}` },
      ],
    })
  }
})
</script>
