<template>
  <div class="cases-page">
    <!-- Hero Section -->
    <section class="cases-hero bg-gradient-to-br from-accent/5 via-surface to-primary/5 py-16 md:py-24">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <AnimatedSection animation="fade-in-up" :delay="0">
          <h1 class="text-4xl md:text-5xl font-bold text-text-primary mb-4">工程案例</h1>
          <p class="text-xl text-text-secondary max-w-2xl mx-auto">
            500+成功案例，见证优丁建材的品质与实力
          </p>
        </AnimatedSection>
      </div>
    </section>

    <!-- Filter Section -->
    <section class="filter-section bg-surface-elevated border-b border-border">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div class="flex flex-col md:flex-row gap-4 items-center justify-between">
          <div class="flex flex-wrap gap-2">
            <button
              v-for="filter in filters"
              :key="filter.id"
              @click="selectedFilter = filter.id"
              :class="[
                'px-4 py-2 rounded-full text-sm font-medium transition-all duration-200',
                selectedFilter === filter.id
                  ? 'bg-accent text-white shadow-md'
                  : 'bg-surface text-text-secondary hover:bg-accent/10 hover:text-accent'
              ]"
            >
              {{ filter.name }}
            </button>
          </div>
          <div class="relative w-full md:w-64">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索案例..."
              class="w-full pl-10 pr-4 py-2 border border-border rounded-xl focus:ring-2 focus:ring-accent-500/20 focus:border-accent-500 transition-all"
            />
            <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>
      </div>
    </section>

    <!-- Cases Grid -->
    <section class="cases-section py-12 md:py-16">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <!-- Loading State -->
        <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div v-for="i in 6" :key="i" class="case-card-skeleton animate-pulse">
            <div class="bg-gray-200 h-56 rounded-t-2xl"></div>
            <div class="p-6">
              <div class="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
              <div class="h-4 bg-gray-200 rounded w-full mb-2"></div>
              <div class="h-4 bg-gray-200 rounded w-2/3"></div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else-if="filteredCases.length === 0" class="text-center py-16">
          <svg class="w-24 h-24 mx-auto text-text-secondary/30 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          <h3 class="text-xl font-semibold text-text-primary mb-2">暂无案例</h3>
          <p class="text-text-secondary">当前筛选条件下暂无案例，请稍后查看</p>
        </div>

        <!-- Cases List -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <AnimatedSection
            v-for="(caseItem, index) in paginatedCases"
            :key="caseItem.id"
            animation="fade-in-up"
            :delay="index * 50"
          >
            <NuxtLink
              :to="`/cases/${caseItem.slug}`"
              class="case-card group bg-surface-elevated rounded-2xl shadow-card overflow-hidden hover:shadow-card-hover hover:-translate-y-2 transition-all duration-300"
            >
              <!-- Case Image -->
              <div class="case-image relative h-56 overflow-hidden bg-gradient-to-br from-accent/5 to-primary/5">
                <img
                  :src="caseItem.cover_image || '/images/case-default.jpg'"
                  :alt="caseItem.project_name"
                  class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  loading="lazy"
                />
                <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
                <div class="absolute bottom-4 left-4 right-4">
                  <span class="px-3 py-1 bg-accent/90 text-white text-xs font-medium rounded-full">
                    {{ caseItem.location || '全国' }}
                  </span>
                </div>
              </div>

              <!-- Case Info -->
              <div class="p-6">
                <h3 class="text-lg font-semibold text-text-primary mb-2 group-hover:text-accent transition-colors">
                  {{ caseItem.project_name }}
                </h3>
                <p class="text-sm text-text-secondary line-clamp-2 mb-4">
                  {{ caseItem.description || '点击查看案例详情' }}
                </p>

                <!-- Case Meta -->
                <div class="flex flex-wrap gap-3 text-sm text-text-secondary mb-4">
                  <span v-if="caseItem.construction_area" class="flex items-center">
                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                    </svg>
                    {{ caseItem.construction_area }}
                  </span>
                  <span v-if="caseItem.project_date" class="flex items-center">
                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    {{ caseItem.project_date }}
                  </span>
                </div>

                <!-- View Count -->
                <div class="flex items-center justify-between text-sm text-text-secondary">
                  <div class="flex items-center">
                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    {{ caseItem.view_count }} 次浏览
                  </div>
                  <span class="text-accent font-medium group-hover:underline">
                    查看详情 →
                  </span>
                </div>
              </div>
            </NuxtLink>
          </AnimatedSection>
        </div>

        <!-- Pagination -->
        <div v-if="totalPages > 1" class="mt-12 flex justify-center">
          <nav class="flex items-center gap-2">
            <button
              @click="currentPage--"
              :disabled="currentPage === 1"
              class="px-4 py-2 rounded-lg border border-border text-text-secondary hover:bg-accent/10 hover:text-accent disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              上一页
            </button>
            <button
              v-for="page in visiblePages"
              :key="page"
              @click="currentPage = page"
              :class="[
                'w-10 h-10 rounded-lg font-medium transition-all',
                currentPage === page
                  ? 'bg-accent text-white'
                  : 'border border-border text-text-secondary hover:bg-accent/10 hover:text-accent'
              ]"
            >
              {{ page }}
            </button>
            <button
              @click="currentPage++"
              :disabled="currentPage === totalPages"
              class="px-4 py-2 rounded-lg border border-border text-text-secondary hover:bg-accent/10 hover:text-accent disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              下一页
            </button>
          </nav>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="cta-section py-16 bg-gradient-to-br from-accent/5 via-surface-elevated to-primary/5">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <AnimatedSection animation="fade-in-up" :delay="0">
          <h2 class="text-2xl md:text-3xl font-bold text-text-primary mb-4">成为下一个成功案例</h2>
          <p class="text-lg text-text-secondary mb-8">
            选择优丁建材，享受专业品质保障与全方位技术支持
          </p>
          <div class="flex flex-wrap justify-center gap-4">
            <NuxtLink to="/contact" class="btn-primary btn-primary-lg">
              立即咨询
            </NuxtLink>
            <a :href="`tel:${contactPhone}`" class="btn-outline">
              电话咨询：{{ contactPhone }}
            </a>
          </div>
        </AnimatedSection>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useCaseStore } from '~/stores/case'
import { SITE_CONFIG } from '~/config/site'

const caseStore = useCaseStore()
const contactPhone = SITE_CONFIG.phone

const selectedFilter = ref<string>('all')
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = 9

const loading = computed(() => caseStore.loading)

const filters = [
  { id: 'all', name: '全部案例' },
  { id: 'published', name: '已完工' },
  { id: 'ongoing', name: '进行中' },
]

const filteredCases = computed(() => {
  let cases = caseStore.publishedCases
  
  if (selectedFilter.value !== 'all') {
    cases = cases.filter(c => c.status === selectedFilter.value)
  }
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    cases = cases.filter(c => 
      c.project_name.toLowerCase().includes(query) || 
      (c.description && c.description.toLowerCase().includes(query)) ||
      (c.location && c.location.toLowerCase().includes(query))
    )
  }
  
  return cases
})

const totalPages = computed(() => Math.ceil(filteredCases.value.length / pageSize))
const paginatedCases = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredCases.value.slice(start, start + pageSize)
})

const visiblePages = computed(() => {
  const pages: number[] = []
  const maxVisible = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
  let end = Math.min(totalPages.value, start + maxVisible - 1)
  
  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1)
  }
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  return pages
})

watch([selectedFilter, searchQuery], () => {
  currentPage.value = 1
})

onMounted(async () => {
  await caseStore.fetchCases()
})

useHead({
  title: '工程案例 - 轻集料混凝土应用案例 | 优丁建材',
  meta: [
    { name: 'description', content: '优丁建材500+成功案例，涵盖商业建筑、工业厂房、公共设施等领域，展示轻集料混凝土与保温材料的实际应用效果。' },
    { name: 'keywords', content: '工程案例,轻集料混凝土应用,保温工程案例,优丁建材案例' },
  ],
})
</script>

<style scoped>
.case-card-skeleton {
  border-radius: 1rem;
  overflow: hidden;
  background: white;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
