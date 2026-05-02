<template>
  <div>
    <section class="relative overflow-hidden bg-gradient-to-br from-primary-900 via-primary-800 to-secondary-700">
      <div class="absolute inset-0 opacity-10">
        <div class="absolute top-1/4 right-1/4 w-96 h-96 bg-secondary-400 rounded-full blur-3xl" />
        <div class="absolute bottom-1/4 left-1/4 w-80 h-80 bg-accent-400 rounded-full blur-3xl" />
      </div>
      <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-24">
        <NuxtLink
          to="/products"
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
          返回产品列表
        </NuxtLink>
        <div class="max-w-4xl">
          <span class="text-sm font-medium bg-white/10 text-white px-3 py-1 rounded-full">
            {{ categoryName }}
          </span>
          <h1 class="text-3xl md:text-5xl font-bold text-white mt-4 mb-4">
            {{ product?.name }}
          </h1>
          <p
            v-if="product?.subtitle"
            class="text-xl text-white/80"
          >
            {{ product.subtitle }}
          </p>
        </div>
      </div>
    </section>

    <section
      v-if="loading"
      class="py-20 text-center"
    >
      <div class="flex items-center justify-center">
        <div class="w-8 h-8 border-2 border-secondary-500 border-t-transparent rounded-full animate-spin" />
        <span class="ml-3 text-text-muted">加载中...</span>
      </div>
    </section>

    <template v-else-if="product">
      <section class="py-12 bg-gradient-to-b from-surface-elevated to-surface">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
            <div
              v-if="product.density"
              class="bg-white rounded-xl p-4 border border-border hover:border-secondary-200 hover:shadow-card-hover transition-all"
            >
              <div class="text-xs text-text-muted mb-1">
                密度等级
              </div>
              <div class="text-lg font-bold text-secondary-600">
                {{ product.density }}
              </div>
            </div>
            <div
              v-if="product.strength"
              class="bg-white rounded-xl p-4 border border-border hover:border-secondary-200 hover:shadow-card-hover transition-all"
            >
              <div class="text-xs text-text-muted mb-1">
                强度等级
              </div>
              <div class="text-lg font-bold text-secondary-600">
                {{ product.strength }}
              </div>
            </div>
            <div
              v-if="product.thermal_conductivity"
              class="bg-white rounded-xl p-4 border border-border hover:border-secondary-200 hover:shadow-card-hover transition-all"
            >
              <div class="text-xs text-text-muted mb-1">
                导热系数
              </div>
              <div class="text-lg font-bold text-secondary-600">
                {{ product.thermal_conductivity }}
              </div>
            </div>
            <div
              v-if="product.fire_rating"
              class="bg-white rounded-xl p-4 border border-border hover:border-secondary-200 hover:shadow-card-hover transition-all"
            >
              <div class="text-xs text-text-muted mb-1">
                防火等级
              </div>
              <div class="text-lg font-bold text-secondary-600">
                {{ product.fire_rating }}
              </div>
            </div>
            <div
              v-if="product.unit_weight"
              class="bg-white rounded-xl p-4 border border-border hover:border-secondary-200 hover:shadow-card-hover transition-all"
            >
              <div class="text-xs text-text-muted mb-1">
                单位重量
              </div>
              <div class="text-lg font-bold text-secondary-600">
                {{ product.unit_weight }}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="py-16 bg-surface">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-12">
            <div class="lg:col-span-2 space-y-12">
              <div v-if="product.description">
                <div class="inline-flex items-center px-3 py-1.5 bg-secondary-50 rounded-full mb-4">
                  <span class="w-1.5 h-1.5 bg-secondary-500 rounded-full mr-2" />
                  <span class="text-sm font-medium text-secondary-600">产品介绍</span>
                </div>
                <h2 class="text-2xl md:text-3xl font-bold text-primary-900 mb-6">
                  关于 {{ product.name }}
                </h2>
                <div
                  class="bg-white rounded-2xl p-8 border border-border"
                  v-html="renderMarkdown(product.description)"
                />
              </div>

              <div v-if="product.technical_params">
                <div class="inline-flex items-center px-3 py-1.5 bg-accent-50 rounded-full mb-4">
                  <span class="w-1.5 h-1.5 bg-accent-500 rounded-full mr-2" />
                  <span class="text-sm font-medium text-accent-600">技术参数</span>
                </div>
                <h2 class="text-2xl md:text-3xl font-bold text-primary-900 mb-6">
                  详细技术规格
                </h2>
                <div class="bg-white rounded-2xl border border-border overflow-hidden">
                  <table class="w-full">
                    <thead>
                      <tr class="bg-surface-elevated">
                        <th class="px-6 py-4 text-left text-sm font-semibold text-primary-900">
                          参数名称
                        </th>
                        <th class="px-6 py-4 text-left text-sm font-semibold text-primary-900">
                          参数值
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="(param, idx) in parseParams(product.technical_params)"
                        :key="idx"
                        class="border-b border-border last:border-0 hover:bg-surface-hover/50 transition-colors"
                      >
                        <td class="px-6 py-4 text-text-secondary font-medium w-1/3">
                          {{ param.label }}
                        </td>
                        <td class="px-6 py-4 text-primary-900">
                          {{ param.value }}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <div v-if="product.application_scenarios">
                <div class="inline-flex items-center px-3 py-1.5 bg-warm-50 rounded-full mb-4">
                  <span class="w-1.5 h-1.5 bg-warm-500 rounded-full mr-2" />
                  <span class="text-sm font-medium text-warm-600">应用场景</span>
                </div>
                <h2 class="text-2xl md:text-3xl font-bold text-primary-900 mb-6">
                  适用场景
                </h2>
                <div
                  class="bg-white rounded-2xl p-8 border border-border"
                  v-html="renderMarkdown(product.application_scenarios)"
                />
              </div>

              <div v-if="product.advantages">
                <div class="inline-flex items-center px-3 py-1.5 bg-secondary-50 rounded-full mb-4">
                  <span class="w-1.5 h-1.5 bg-secondary-500 rounded-full mr-2" />
                  <span class="text-sm font-medium text-secondary-600">产品优势</span>
                </div>
                <h2 class="text-2xl md:text-3xl font-bold text-primary-900 mb-6">
                  核心优势
                </h2>
                <div
                  class="bg-white rounded-2xl p-8 border border-border"
                  v-html="renderMarkdown(product.advantages)"
                />
              </div>

              <div
                v-if="documents.length"
                class="bg-gradient-to-r from-secondary-50 to-accent-50 rounded-2xl p-6 border border-secondary-100"
              >
                <h2 class="text-xl font-bold text-primary-900 mb-4 flex items-center gap-2">
                  <svg
                    class="w-5 h-5 text-secondary-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                    />
                  </svg>
                  相关下载
                </h2>
                <div class="space-y-3">
                  <a
                    v-for="doc in documents"
                    :key="doc.id"
                    :href="doc.file_path"
                    target="_blank"
                    class="flex items-center justify-between bg-white rounded-xl px-5 py-4 hover:bg-surface-hover transition-colors border border-border group"
                  >
                    <div class="flex items-center gap-3">
                      <div class="w-10 h-10 bg-gradient-to-br from-secondary-50 to-accent-50 rounded-lg flex items-center justify-center">
                        <span class="text-lg">{{ docTypeIcon(doc.doc_type) }}</span>
                      </div>
                      <div>
                        <p class="text-sm font-medium text-primary-900">{{ doc.file_name }}</p>
                        <p class="text-xs text-text-muted">{{ docTypeLabel(doc.doc_type) }}</p>
                      </div>
                    </div>
                    <span class="text-secondary-600 text-sm font-medium flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                      下载
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
                          d="M19 14l-7 7m0 0l-7-7m7 7V3"
                        />
                      </svg>
                    </span>
                  </a>
                </div>
              </div>
            </div>

            <div class="space-y-6">
              <div class="bg-white rounded-2xl p-6 border border-border shadow-card sticky top-24">
                <h3 class="text-lg font-semibold text-primary-900 mb-4">
                  产品咨询
                </h3>
                <p class="text-sm text-text-secondary mb-6">
                  对该产品感兴趣？我们的技术团队为您提供详细参数和报价
                </p>
                <div class="space-y-3">
                  <NuxtLink
                    to="/contact"
                    class="inline-flex items-center justify-center w-full px-6 py-4 bg-gradient-to-r from-secondary-500 to-secondary-600 text-white font-semibold rounded-xl hover:from-secondary-600 hover:to-secondary-700 transition-all shadow-lg shadow-secondary-200"
                  >
                    立即咨询
                  </NuxtLink>
                  <a
                    href="tel:400-888-8888"
                    class="flex items-center justify-center w-full px-6 py-4 bg-secondary-50 text-secondary-600 font-medium rounded-xl hover:bg-secondary-100 transition-colors"
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
                        d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                      />
                    </svg>
                    拨打 400-888-8888
                  </a>
                </div>
                <div class="mt-6 pt-6 border-t border-border">
                  <h4 class="text-sm font-semibold text-primary-900 mb-3">
                    其他产品
                  </h4>
                  <div class="space-y-2">
                    <NuxtLink
                      v-for="other in otherProducts"
                      :key="other.id"
                      :to="'/products/' + other.slug"
                      class="block text-sm text-text-secondary hover:text-secondary-600 transition-colors py-1"
                    >
                      {{ other.name }}
                    </NuxtLink>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section
        v-if="product.specifications"
        class="py-16 bg-gradient-to-b from-surface to-surface-elevated"
      >
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="inline-flex items-center px-3 py-1.5 bg-accent-50 rounded-full mb-4">
            <span class="w-1.5 h-1.5 bg-accent-500 rounded-full mr-2" />
            <span class="text-sm font-medium text-accent-600">规格型号</span>
          </div>
          <h2 class="text-2xl md:text-3xl font-bold text-primary-900 mb-6">
            产品规格
          </h2>
          <div
            class="bg-white rounded-2xl p-8 border border-border"
            v-html="renderMarkdown(product.specifications)"
          />
        </div>
      </section>

      <section class="py-16 bg-gradient-to-r from-secondary-600 via-secondary-500 to-accent-500">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 class="text-3xl font-bold text-white mb-4">
            需要定制化解决方案？
          </h2>
          <p class="text-white/80 mb-8 max-w-2xl mx-auto">
            我们的技术团队拥有丰富的行业经验，可以根据您的具体工程需求提供最优产品方案
          </p>
          <div class="flex flex-wrap justify-center gap-4">
            <NuxtLink
              to="/contact"
              class="inline-flex items-center px-8 py-4 bg-white text-secondary-600 font-semibold rounded-xl hover:bg-gray-100 transition-all shadow-lg"
            >
              免费获取方案
            </NuxtLink>
            <a
              href="tel:400-888-8888"
              class="inline-flex items-center px-8 py-4 border-2 border-white text-white font-semibold rounded-xl hover:bg-white/10 transition-all"
            >
              拨打 400-888-8888
            </a>
          </div>
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
        产品不存在或已下架
      </p>
      <NuxtLink
        to="/products"
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
        返回产品列表
      </NuxtLink>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watchEffect } from 'vue'
import { useRoute } from 'vue-router'

interface ProductDocument {
  id: string
  file_name: string
  file_path: string
  doc_type: string
  file_size: number
}

const route = useRoute()
const loading = ref(false)
const product = ref<any>(null)
const documents = ref<ProductDocument[]>([])

const slug = computed(() => route.params.slug as string)

const categoryName = computed(() => {
  if (!product.value) return ''
  return '产品分类'
})

const otherProducts = computed(() => [])

function docTypeIcon(type: string): string {
  const map: Record<string, string> = {
    pdf: '📄', cad: '📐', report: '🔬', certificate: '🏆', other: '📎'
  }
  return map[type] || '📎'
}

function docTypeLabel(type: string): string {
  const map: Record<string, string> = {
    pdf: 'PDF文档', cad: 'CAD图纸', report: '检测报告', certificate: '资质证书', other: '其他文件'
  }
  return map[type] || '其他文件'
}

function parseParams(text: string | null): Array<{ label: string; value: string }> {
  if (!text) return []
  try {
    const parsed = JSON.parse(text)
    if (typeof parsed === 'object' && !Array.isArray(parsed)) {
      return Object.entries(parsed).map(([key, val]) => ({ label: key, value: String(val) }))
    }
  } catch {}
  return text.split('\n').filter(Boolean).map(line => {
    const sep = line.includes('：') ? '：' : line.includes(':') ? ':' : '|'
    const idx = line.indexOf(sep)
    if (idx > 0) return { label: line.slice(0, idx).trim(), value: line.slice(idx + 1).trim() }
    return { label: '', value: line }
  })
}

function renderMarkdown(text: string | null): string {
  if (!text) return ''
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  html = html.replace(/### (.+)/g, '<h3 class="text-xl font-semibold text-text-primary mt-6 mb-3">$1</h3>')
  html = html.replace(/## (.+)/g, '<h2 class="text-2xl font-bold text-text-primary mt-8 mb-4">$1</h2>')
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\n\s*[-•]\s+(.+)/g, '<li class="text-text-secondary ml-4">$1</li>')
  html = html.replace(/(<li.+<\/li>)/g, '<ul class="list-disc space-y-1 mb-4">$1</ul>')
  html = html.replace(/\n\n/g, '</p><p class="text-text-secondary leading-relaxed mb-4">')
  html = '<p class="text-text-secondary leading-relaxed mb-4">' + html + '</p>'
  html = html.replace(/<p class="[^"]*"><\/p>/g, '')
  return html
}

async function fetchProduct() {
  loading.value = true
  try {
    const res = await fetch(`/api/v1/products/by-slug/${slug.value}`)
    if (res.ok) {
      product.value = await res.json()
      await fetchDocuments()
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function fetchDocuments() {
  if (!product.value) return
  try {
    const res = await fetch(`/api/v1/products/${product.value.id}/documents`)
    if (res.ok) {
      documents.value = await res.json()
    }
  } catch (e) {
    console.error(e)
  }
}

onMounted(fetchProduct)

watchEffect(() => {
  if (product.value) {
    const metaTitle = product.value.meta_title || `${product.value.name} - 优丁保温材料厂家`
    const metaDesc = product.value.meta_description
      || product.value.subtitle
      || (product.value.description ? product.value.description.replace(/<[^>]+>/g, '').slice(0, 160) : '')
      || `${product.value.name}技术参数、应用场景和产品优势`
    useHead({
      title: metaTitle,
      meta: [
        { name: 'description', content: metaDesc },
        { name: 'keywords', content: `${product.value.name},保温材料,${product.value.category_id || ''}` },
      ],
    })
  }
})
</script>
