<template>
  <div>
    <section class="relative overflow-hidden bg-gradient-to-br from-primary-900 via-primary-800 to-secondary-700">
      <div class="absolute inset-0 opacity-10">
        <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-secondary-400 rounded-full blur-3xl" />
        <div class="absolute bottom-1/4 right-1/4 w-80 h-80 bg-accent-400 rounded-full blur-3xl" />
      </div>
      <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-24 text-center">
        <div class="inline-flex items-center px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full mb-6">
          <span class="w-2 h-2 bg-secondary-400 rounded-full mr-2" />
          <span class="text-sm font-medium text-white">工程案例</span>
        </div>
        <h1 class="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-4 leading-tight">
          工程案例
        </h1>
        <p class="text-xl text-white/80">
          累计服务 500+ 工程项目，涵盖建筑外墙、管道保温、冷链物流等领域
        </p>
      </div>
    </section>

    <section class="py-20 bg-gradient-to-b from-surface-elevated to-surface">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div
          v-if="loading"
          class="text-center py-12"
        >
          <div class="flex items-center justify-center">
            <div class="w-8 h-8 border-2 border-secondary-500 border-t-transparent rounded-full animate-spin" />
            <span class="ml-3 text-text-muted">加载中...</span>
          </div>
        </div>

        <template v-else-if="cases.length">
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <NuxtLink
              v-for="case_item in cases"
              :key="case_item.id"
              :to="'/cases/' + case_item.slug"
              class="group bg-white rounded-2xl overflow-hidden border border-border hover:border-secondary-200 hover:shadow-card-hover transition-all duration-300 hover:-translate-y-1"
            >
              <div class="h-48 bg-gradient-to-br from-secondary-50 via-white to-accent-50 flex items-center justify-center relative overflow-hidden">
                <img
                  v-if="case_item.cover_image"
                  :src="case_item.cover_image"
                  :alt="case_item.project_name"
                  class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                >
                <div
                  v-else
                  class="w-full h-full flex items-center justify-center text-6xl"
                >
                  🏗️
                </div>
                <div class="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent" />
                <div class="absolute bottom-4 left-4 right-4">
                  <span
                    v-if="case_item.status === 'published'"
                    class="inline-block text-xs bg-accent-500 text-white px-3 py-1 rounded-full"
                  >已发布</span>
                  <span
                    v-else
                    class="inline-block text-xs bg-text-muted text-white px-3 py-1 rounded-full"
                  >草稿</span>
                </div>
              </div>
              <div class="p-6">
                <h3 class="text-lg font-semibold text-primary-900 mb-3 group-hover:text-secondary-600 transition-colors">
                  {{ case_item.project_name }}
                </h3>
                <div class="space-y-1 text-sm text-text-muted">
                  <p
                    v-if="case_item.client_name"
                    class="flex items-center gap-2"
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
                        d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                      />
                    </svg>
                    {{ case_item.client_name }}
                  </p>
                  <p
                    v-if="case_item.construction_area"
                    class="flex items-center gap-2"
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
                        d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"
                      />
                    </svg>
                    {{ case_item.construction_area }}
                  </p>
                  <p
                    v-if="case_item.location"
                    class="flex items-center gap-2"
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
                        d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                      />
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                      />
                    </svg>
                    {{ case_item.location }}
                  </p>
                </div>
              </div>
            </NuxtLink>
          </div>
        </template>

        <div
          v-else
          class="text-center py-20"
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
          <p class="text-text-muted text-lg mb-4">
            暂无案例内容
          </p>
          <p class="text-text-muted">
            敬请期待更多工程项目展示
          </p>
        </div>
      </div>
    </section>

    <section class="py-16 bg-gradient-to-r from-secondary-600 via-secondary-500 to-accent-500">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 class="text-3xl font-bold text-white mb-4">
          承接各类保温工程
        </h2>
        <p class="text-white/80 mb-8 max-w-2xl mx-auto">
          我们提供从材料供应到施工指导的一站式服务，欢迎来电咨询
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
          立即咨询
        </NuxtLink>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface CaseItem {
  id: string
  project_name: string
  slug: string
  client_name: string | null
  construction_area: string | null
  location: string | null
  cover_image: string | null
  status: string
  is_active: boolean
}

const cases = ref<CaseItem[]>([])
const loading = ref(false)

async function fetchCases() {
  loading.value = true
  try {
    const res = await fetch('/api/v1/case-studies')
    if (res.ok) {
      const data = await res.json()
      const items = data.items || []
      cases.value = items.filter((c: CaseItem) => c.is_active)
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchCases)

useHead({
  title: '工程案例 - 优丁保温材料',
  meta: [
    { name: 'description', content: '优丁保温材料工程案例展示，涵盖建筑外墙保温、管道保温、冷链物流等领域，累计服务500+工程项目' },
  ],
})
</script>
