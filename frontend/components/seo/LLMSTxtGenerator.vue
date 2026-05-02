<template>
  <div class="space-y-6">
    <div class="bg-white rounded-xl shadow-sm p-6">
      <h3 class="text-lg font-semibold mb-4">
        LLMs.txt 生成器
      </h3>
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">选择生成模块</label>
          <div class="flex flex-wrap gap-3">
            <label
              v-for="section in availableSections"
              :key="section.type"
              class="flex items-center space-x-2 cursor-pointer"
            >
              <input
                v-model="selectedSectionTypes"
                type="checkbox"
                :value="section.type"
                class="rounded border-gray-300 text-brand-blue focus:ring-brand-blue"
              >
              <span>{{ sectionLabels[section.type] || section.type }}</span>
            </label>
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">AI指令</label>
          <label class="flex items-center space-x-2 cursor-pointer">
            <input
              v-model="includeAiInstructions"
              type="checkbox"
              class="rounded border-gray-300 text-brand-blue focus:ring-brand-blue"
            >
            <span class="text-sm text-gray-600">包含AI指令（指导AI如何与网站互动）</span>
          </label>
        </div>
        <div class="flex items-center space-x-4">
          <button
            :disabled="generating"
            class="px-6 py-2 bg-brand-blue text-white rounded-lg hover:bg-blue-800 disabled:opacity-50 transition-colors"
            @click="handleGenerate"
          >
            {{ generating ? '生成中...' : '生成 LLMs.txt' }}
          </button>
          <button
            v-if="result"
            class="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            @click="handleCopy"
          >
            复制内容
          </button>
          <button
            v-if="result"
            class="px-6 py-2 bg-orange-50 text-orange-700 rounded-lg hover:bg-orange-100 transition-colors"
            @click="handleValidate"
          >
            验证合规
          </button>
        </div>
      </div>
    </div>

    <div
      v-if="error"
      class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg"
    >
      {{ error }}
    </div>

    <div
      v-if="validationResult"
      class="bg-white rounded-xl shadow-sm p-6"
    >
      <h3 class="text-lg font-semibold mb-4">
        验证结果
      </h3>
      <div class="flex items-center space-x-2 mb-4">
        <span
          :class="validationResult.is_valid ? 'text-green-600' : 'text-red-600'"
          class="font-medium"
        >
          {{ validationResult.is_valid ? '通过' : '存在问题' }}
        </span>
        <span class="text-gray-500 text-sm">({{ validationResult.section_count }} 个模块)</span>
      </div>
      <ul
        v-if="validationResult.issues.length"
        class="space-y-2"
      >
        <li
          v-for="(issue, i) in validationResult.issues"
          :key="i"
          class="text-sm px-3 py-2 rounded"
          :class="issue.severity === 'error' ? 'text-red-600 bg-red-50' : 'text-orange-600 bg-orange-50'"
        >
          {{ issue.message }}
        </li>
      </ul>
    </div>

    <div
      v-if="result"
      class="bg-white rounded-xl shadow-sm p-6"
    >
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold">
          生成结果
        </h3>
        <div class="text-sm text-gray-500">
          {{ result.line_count }} 行 | {{ (result.size_bytes / 1024).toFixed(1) }} KB
        </div>
      </div>
      <pre class="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm font-mono whitespace-pre-wrap max-h-96 overflow-y-auto">{{ result.content }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useSeo } from '~/composables/useSeo'

const seo = useSeo()

interface SectionTemplate {
  type: string
  title: string
  url?: string
  description?: string
}

const sectionLabels: Record<string, string> = {
  brand: '品牌介绍',
  product: '产品信息',
  faq: '常见问题',
  contact: '联系方式',
}

const availableSections = ref<SectionTemplate[]>([
  { type: 'brand', title: '品牌介绍', url: '/about', description: '优丁公司介绍' },
  { type: 'product', title: '产品信息', url: '/products', description: '轻集料混凝土产品' },
  { type: 'faq', title: '常见问题', url: '/faq', description: '用户常见问题' },
  { type: 'contact', title: '联系方式', url: '/contact', description: '公司联系信息' },
])

const selectedSectionTypes = ref<string[]>(['brand', 'product', 'contact'])
const includeAiInstructions = ref(true)
const generating = ref(false)
const error = ref<string | null>(null)
const result = ref<{
  content: string
  line_count: number
  size_bytes: number
} | null>(null)
const validationResult = ref<{
  is_valid: boolean
  issues: Array<{ severity: string; message: string }>
  section_count: number
} | null>(null)

async function handleGenerate() {
  generating.value = true
  error.value = null
  result.value = null
  validationResult.value = null
  try {
    const sections = availableSections.value
      .filter(s => selectedSectionTypes.value.includes(s.type))
      .map(s => ({ ...s }))
    result.value = await seo.generateLlmsTxt({
      sections,
      include_ai_instructions: includeAiInstructions.value,
    })
  } catch (e: any) {
    error.value = e.message || '生成失败'
  } finally {
    generating.value = false
  }
}

async function handleValidate() {
  if (!result.value) return
  try {
    validationResult.value = await seo.validateLlmsTxt(result.value.content)
  } catch (e: any) {
    error.value = e.message || '验证失败'
  }
}

async function handleCopy() {
  if (!result.value) return
  try {
    await navigator.clipboard.writeText(result.value.content)
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = result.value.content
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
  }
}
</script>
