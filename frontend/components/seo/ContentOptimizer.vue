<template>
  <div class="space-y-6">
    <div class="bg-white rounded-xl shadow-sm p-6">
      <h3 class="text-lg font-semibold mb-4">
        AI 内容优化
      </h3>
      <div class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">优化类型</label>
            <select
              v-model="optType"
              class="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
            >
              <option value="content">
                内容正文
              </option>
              <option value="title">
                标题
              </option>
              <option value="description">
                描述
              </option>
              <option value="alt_text">
                Alt文本
              </option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">目标关键词 (逗号分隔)</label>
            <input
              v-model="keywordsRaw"
              placeholder="轻集料混凝土,陶粒混凝土"
              class="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">AI模型</label>
            <select
              v-model="model"
              class="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
            >
              <option value="gpt-4o">
                GPT-4o (推荐)
              </option>
              <option value="gpt-4o-mini">
                GPT-4o Mini (快速)
              </option>
              <option value="claude-3-haiku">
                Claude 3 Haiku
              </option>
            </select>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">原始内容</label>
          <textarea
            v-model="content"
            rows="8"
            class="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-brand-blue focus:border-transparent"
            placeholder="请输入需要优化的内容..."
          />
        </div>

        <div class="flex items-center space-x-4">
          <button
            :disabled="optimizing"
            class="px-6 py-2 bg-brand-blue text-white rounded-lg hover:bg-blue-800 disabled:opacity-50 transition-colors"
            @click="handleOptimize"
          >
            {{ optimizing ? '优化中...' : '开始优化' }}
          </button>
          <button
            class="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            @click="handleExtractParams"
          >
            提取技术参数
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
      v-if="extractedParamsResult"
      class="bg-white rounded-xl shadow-sm p-6"
    >
      <h3 class="text-lg font-semibold mb-4">
        提取的技术参数
      </h3>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
          v-for="(value, key) in extractedParamsResult.technical_params"
          :key="key"
          class="bg-gray-50 rounded-lg p-4"
        >
          <span class="text-sm text-gray-500">{{ paramLabels[key] || key }}</span>
          <div class="text-gray-900 font-medium mt-1">
            {{ value }}
          </div>
        </div>
      </div>
      <p
        v-if="!extractedParamsResult.found"
        class="text-sm text-gray-400 mt-2"
      >
        未识别到行业标准技术参数
      </p>
    </div>

    <div
      v-if="result"
      class="space-y-4"
    >
      <div class="bg-white rounded-xl shadow-sm p-6">
        <h3 class="text-lg font-semibold mb-4">
          优化结果
        </h3>
        <div class="bg-green-50 border border-green-200 rounded-lg p-4 whitespace-pre-wrap">
          {{ result.optimized_content }}
        </div>
        <div class="flex items-center justify-between mt-4 text-sm text-gray-500">
          <span>Token用量: {{ result.token_usage }} | 费用: ¥{{ result.cost }}</span>
          <span class="text-green-600">{{ result.changes.length }} 项变更</span>
        </div>
        <div
          v-if="result.technical_params_preserved"
          class="mt-2 text-xs text-green-600"
        >
          技术参数已保留 ✓
        </div>
        <div
          v-else
          class="mt-2 text-xs text-orange-600"
        >
          技术参数可能丢失，请检查
        </div>
      </div>

      <div
        v-if="validation"
        class="bg-white rounded-xl shadow-sm p-6"
      >
        <h3 class="text-lg font-semibold mb-4">
          合规校验
        </h3>
        <div class="flex items-center space-x-2 mb-4">
          <span
            :class="validation.is_valid ? 'text-green-600' : 'text-red-600'"
            class="font-medium"
          >
            {{ validation.is_valid ? '通过' : '存在问题' }}
          </span>
          <span :class="validation.technical_params_preserved ? 'text-green-600' : 'text-orange-600'">
            | 技术参数{{ validation.technical_params_preserved ? '已保留' : '可能丢失' }}
          </span>
        </div>
        <ul
          v-if="validation.issues.length"
          class="space-y-2"
        >
          <li
            v-for="(issue, i) in validation.issues"
            :key="i"
            class="text-sm text-red-600 bg-red-50 px-3 py-2 rounded"
          >
            <span
              v-if="issue.param"
              class="font-medium"
            >{{ issue.param }}: </span>{{ issue.issue }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useSeo } from '~/composables/useSeo'

const seo = useSeo()

const optType = ref<'title' | 'description' | 'alt_text' | 'content'>('content')
const keywordsRaw = ref('')
const content = ref('')
const model = ref('gpt-4o')
const optimizing = ref(false)
const error = ref<string | null>(null)
const result = ref<{
  optimized_content: string
  changes: string[]
  token_usage: number
  cost: number
  technical_params_preserved: boolean
} | null>(null)
const validation = ref<{
  is_valid: boolean
  issues: Array<{ param: string | null; issue: string }>
  technical_params_preserved: boolean
} | null>(null)
const extractedParamsResult = ref<{
  technical_params: Record<string, string>
  found: boolean
} | null>(null)

const paramLabels: Record<string, string> = {
  density: '密度',
  strength_grade: '强度等级',
  thermal_conductivity: '导热系数',
  particle_size: '粒径',
  water_absorption: '吸水率',
  specification: '规格型号',
  material: '材料类型',
}

async function handleOptimize() {
  if (!content.value || content.value.length < 10) {
    error.value = '内容至少需要10个字符'
    return
  }
  const keywords = keywordsRaw.value.split(',').map(k => k.trim()).filter(Boolean)
  if (!keywords.length) {
    error.value = '请至少输入一个关键词'
    return
  }
  optimizing.value = true
  error.value = null
  result.value = null
  validation.value = null
  try {
    result.value = await seo.optimizeContent({
      content: content.value,
      opt_type: optType.value,
      keywords,
      model: model.value,
    })
    validation.value = await seo.validateContent(content.value, result.value.optimized_content)
  } catch (e: any) {
    error.value = e.message || '优化失败'
  } finally {
    optimizing.value = false
  }
}

async function handleExtractParams() {
  if (!content.value) {
    error.value = '请输入内容'
    return
  }
  error.value = null
  try {
    extractedParamsResult.value = await seo.extractParams(content.value)
  } catch (e: any) {
    error.value = e.message || '参数提取失败'
  }
}
</script>
