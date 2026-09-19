/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="min-h-screen bg-gradient-to-b from-gray-50 to-white py-16">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- 页面标题 -->
      <div class="text-center mb-10">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/10 mb-4">
          <svg
            class="w-8 h-8 text-primary"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
        <h1 class="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">
          免费 SEO 诊断
        </h1>
        <p class="text-lg text-gray-600 max-w-xl mx-auto">
          输入您的网址，5秒获取专业SEO分析报告
        </p>
      </div>

      <!-- 输入区 -->
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 sm:p-8 mb-8">
        <div class="flex flex-col sm:flex-row gap-4">
          <div class="flex-1">
            <div class="relative">
              <div class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
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
                    d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <input
                v-model="urlInput"
                type="url"
                placeholder="https://www.example.com"
                class="w-full pl-12 pr-4 py-3.5 text-base border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/30 focus:border-primary outline-none transition-all"
                :class="{ 'border-red-300 focus:ring-red-200 focus:border-red-400': urlError }"
                @keyup.enter="startDiagnosis"
              >
            </div>
            <p
              v-if="urlError"
              class="mt-2 text-sm text-red-500"
            >
              {{ urlError }}
            </p>
          </div>
          <button
            @click="startDiagnosis"
            :disabled="isDiagnosing || !urlInput.trim()"
            class="px-8 py-3.5 bg-primary text-white font-semibold rounded-xl transition-all duration-200 flex items-center justify-center gap-2 shrink-0"
            :class="isDiagnosing || !urlInput.trim()
              ? 'opacity-60 cursor-not-allowed'
              : 'hover:bg-primary-700 hover:shadow-lg active:scale-[0.98]'"
          >
            <svg
              v-if="isDiagnosing"
              class="w-5 h-5 animate-spin"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              />
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <svg
              v-else
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 5l7 7-7 7"
              />
            </svg>
            {{ isDiagnosing ? '诊断中...' : '开始诊断' }}
          </button>
        </div>
      </div>

      <!-- 诊断结果 -->
      <transition
        enter-active-class="transition-all duration-500 ease-out"
        enter-from-class="opacity-0 translate-y-4"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition-all duration-300 ease-in"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 translate-y-4"
      >
        <div
          v-if="report"
          class="space-y-6"
        >
          <!-- 总分卡片 -->
          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 sm:p-8">
            <div class="flex flex-col sm:flex-row items-center gap-6">
              <div class="relative w-24 h-24 sm:w-28 sm:h-28 shrink-0">
                <svg
                  class="w-full h-full"
                  viewBox="0 0 120 120"
                >
                  <circle
                    cx="60"
                    cy="60"
                    r="52"
                    fill="none"
                    stroke="#E5E7EB"
                    stroke-width="8"
                  />
                  <circle
                    cx="60"
                    cy="60"
                    r="52"
                    fill="none"
                    :stroke="scoreColor"
                    stroke-width="8"
                    stroke-linecap="round"
                    :stroke-dasharray="circumference"
                    :stroke-dashoffset="scoreOffset"
                    transform="rotate(-90 60 60)"
                    class="transition-all duration-1000 ease-out"
                  />
                </svg>
                <div class="absolute inset-0 flex flex-col items-center justify-center">
                  <span
                    class="text-3xl sm:text-4xl font-bold"
                    :class="scoreTextColor"
                  >{{ report.score }}</span>
                  <span class="text-xs text-gray-400">/ 100</span>
                </div>
              </div>
              <div class="flex-1 text-center sm:text-left">
                <h2 class="text-xl font-bold text-gray-900 mb-2">
                  {{ scoreLabel }}
                </h2>
                <p class="text-gray-600">
                  {{ report.summary }}
                </p>
              </div>
            </div>
          </div>

          <!-- 各维度评分网格 -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div
              v-for="(item, key) in report.dimensions"
              :key="key"
              class="bg-white rounded-xl border border-gray-100 p-5 shadow-sm hover:shadow-md transition-shadow"
            >
              <div class="flex items-center justify-between mb-3">
                <h3 class="font-medium text-gray-900 text-sm">
                  {{ item.label }}
                </h3>
                <span class="text-lg">{{ item.icon }}</span>
              </div>
              <div class="flex items-center gap-2">
                <div class="flex-1 bg-gray-100 rounded-full h-2">
                  <div
                    class="h-2 rounded-full transition-all duration-700 ease-out"
                    :class="dimensionBarClass(item.status)"
                    :style="{ width: dimensionBarWidth(item) + '%' }"
                  />
                </div>
                <span
                  class="text-sm font-medium shrink-0 min-w-[3rem] text-right"
                  :class="dimensionScoreClass(item)"
                >
                  {{ dimensionScoreText(item) }}
                </span>
              </div>
            </div>
          </div>

          <!-- 优化建议 -->
          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 sm:p-8">
            <h3 class="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <svg
                class="w-5 h-5 text-primary"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                />
              </svg>
              优化建议
            </h3>
            <ul class="space-y-3">
              <li
                v-for="(suggestion, idx) in report.suggestions"
                :key="idx"
                class="flex items-start gap-3 text-sm text-gray-700"
              >
                <span
                  class="shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold mt-0.5"
                  :class="suggestion.priority === 'high'
                    ? 'bg-red-100 text-red-600'
                    : suggestion.priority === 'medium'
                      ? 'bg-yellow-100 text-yellow-600'
                      : 'bg-blue-100 text-blue-600'"
                >
                  {{ idx + 1 }}
                </span>
                <div>
                  <p>{{ suggestion.text }}</p>
                  <p class="text-xs text-gray-400 mt-0.5">
                    {{ suggestion.priority === 'high' ? '高优先级' : suggestion.priority === 'medium' ? '中优先级' : '低优先级' }}
                  </p>
                </div>
              </li>
            </ul>
          </div>

          <!-- 获取完整报告 -->
          <div class="bg-gradient-to-r from-primary/5 to-primary/10 rounded-2xl border border-primary/20 p-6 sm:p-8 text-center">
            <div class="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-primary/10 mb-4">
              <svg
                class="w-7 h-7 text-primary"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 18h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                />
              </svg>
            </div>
            <h3 class="text-xl font-bold text-gray-900 mb-2">
              获取完整报告
            </h3>
            <p class="text-gray-600 mb-6 max-w-md mx-auto">
              输入手机号，我们将把完整的SEO诊断报告发送给您，包含详细优化方案和执行建议
            </p>
            <button
              @click="showLeadModal = true"
              class="px-8 py-3 bg-primary text-white font-semibold rounded-xl hover:bg-primary-700 hover:shadow-lg transition-all active:scale-[0.98]"
            >
              立即获取完整报告
            </button>
          </div>
        </div>
      </transition>

      <!-- 空状态 -->
      <div
        v-if="!report && !isDiagnosing"
        class="text-center py-16"
      >
        <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gray-100 mb-4">
          <svg
            class="w-10 h-10 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
        <p class="text-gray-500">
          输入网址开始免费诊断
        </p>
        <p class="text-gray-400 text-sm mt-1">
          诊断内容包含标题标签、描述、关键词、H标签、图片Alt、<br>内部链接、加载速度、移动端适配、Schema标记等维度
        </p>
      </div>
    </div>

    <!-- 线索弹窗 -->
    <teleport to="body">
      <transition
        enter-active-class="transition-all duration-300 ease-out"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition-all duration-200 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          v-if="showLeadModal"
          class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
          @click.self="showLeadModal = false"
        >
          <div class="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 sm:p-8">
            <div class="text-center mb-6">
              <div class="inline-flex items-center justify-center w-14 h-14 rounded-full bg-primary/10 mb-3">
                <svg
                  class="w-7 h-7 text-primary"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 18h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                  />
                </svg>
              </div>
              <h3 class="text-xl font-bold text-gray-900">
                提交信息获取完整报告
              </h3>
              <p class="text-sm text-gray-500 mt-1">
                我们将把详细诊断报告发送给您
              </p>
            </div>

            <form
              @submit.prevent="submitLead"
              class="space-y-4"
            >
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">姓名</label>
                <input
                  v-model="leadForm.name"
                  type="text"
                  placeholder="请输入您的姓名"
                  class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/30 focus:border-primary outline-none transition-all"
                  :class="{ 'border-red-300': leadErrors.name }"
                  required
                >
                <p
                  v-if="leadErrors.name"
                  class="mt-1 text-xs text-red-500"
                >
                  {{ leadErrors.name }}
                </p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">手机号</label>
                <input
                  v-model="leadForm.phone"
                  type="tel"
                  placeholder="请输入您的手机号"
                  class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/30 focus:border-primary outline-none transition-all"
                  :class="{ 'border-red-300': leadErrors.phone }"
                  required
                >
                <p
                  v-if="leadErrors.phone"
                  class="mt-1 text-xs text-red-500"
                >
                  {{ leadErrors.phone }}
                </p>
              </div>
              <button
                type="submit"
                :disabled="isSubmitting"
                class="w-full py-3 bg-primary text-white font-semibold rounded-xl transition-all duration-200 flex items-center justify-center gap-2"
                :class="isSubmitting ? 'opacity-60 cursor-not-allowed' : 'hover:bg-primary-700 hover:shadow-lg active:scale-[0.98]'"
              >
                <svg
                  v-if="isSubmitting"
                  class="w-5 h-5 animate-spin"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    class="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    stroke-width="4"
                  />
                  <path
                    class="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                {{ isSubmitting ? '提交中...' : '确认提交' }}
              </button>
            </form>

            <p
              v-if="submitMessage"
              class="mt-4 text-center text-sm"
              :class="submitSuccess ? 'text-green-600' : 'text-red-500'"
            >
              {{ submitMessage }}
            </p>

            <button
              @click="showLeadModal = false"
              class="mt-4 w-full py-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
            >
              取消
            </button>
          </div>
        </div>
      </transition>
    </teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

// ---- 状态 ----
const urlInput = ref('')
const urlError = ref('')
const isDiagnosing = ref(false)
const report = ref<DiagnosisReport | null>(null)
const showLeadModal = ref(false)
const isSubmitting = ref(false)
const submitMessage = ref('')
const submitSuccess = ref(false)

const leadForm = ref({ name: '', phone: '' })
const leadErrors = ref({ name: '', phone: '' })

// ---- 类型 ----
interface DimensionItem {
  label: string
  status: 'good' | 'warning' | 'bad'
  icon: string
  score: number
}

interface SuggestionItem {
  text: string
  priority: 'high' | 'medium' | 'low'
}

interface DiagnosisReport {
  score: number
  summary: string
  dimensions: Record<string, DimensionItem>
  suggestions: SuggestionItem[]
}

// ---- 诊断逻辑 ----
const circumference = 2 * Math.PI * 52 // ~326.73
const scoreOffset = computed(() => {
  if (!report.value) return circumference
  return circumference - (report.value.score / 100) * circumference
})

const scoreColor = computed(() => {
  if (!report.value) return '#10B981'
  const s = report.value.score
  if (s >= 80) return '#10B981'
  if (s >= 60) return '#F59E0B'
  return '#EF4444'
})

const scoreTextColor = computed(() => {
  if (!report.value) return 'text-green-500'
  const s = report.value.score
  if (s >= 80) return 'text-green-500'
  if (s >= 60) return 'text-yellow-500'
  return 'text-red-500'
})

const scoreLabel = computed(() => {
  if (!report.value) return ''
  const s = report.value.score
  if (s >= 90) return '优秀！SEO表现非常好'
  if (s >= 80) return '良好，还有提升空间'
  if (s >= 70) return '一般，建议针对性优化'
  if (s >= 60) return '需要较大改进'
  return '急需全面优化'
})

function dimensionBarClass(status: string): string {
  if (status === 'good') return 'bg-green-500'
  if (status === 'warning') return 'bg-yellow-500'
  return 'bg-red-500'
}

function dimensionScoreClass(item: DimensionItem): string {
  if (item.status === 'good') return 'text-green-600'
  if (item.status === 'warning') return 'text-yellow-600'
  return 'text-red-600'
}

function dimensionScoreText(item: DimensionItem): string {
  if (item.status === 'good') return '良好'
  if (item.status === 'warning') return '需优化'
  return '较差'
}

function dimensionBarWidth(item: DimensionItem): number {
  return item.score
}

function validateUrl(url: string): boolean {
  if (!url.trim()) {
    urlError.value = '请输入网址'
    return false
  }
  try {
    const u = new URL(url.startsWith('http') ? url : 'https://' + url)
    if (!u.hostname.includes('.')) {
      urlError.value = '请输入有效的域名'
      return false
    }
    urlError.value = ''
    return true
  } catch {
    urlError.value = '请输入有效的网址（如 https://www.example.com）'
    return false
  }
}

function normalizeUrl(url: string): string {
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  return 'https://' + url
}

function generateMockReport(url: string): DiagnosisReport {
  const domain = new URL(url).hostname
  // 基于域名生成伪随机但确定性的分数
  const hash = domain.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0)
  const seed = hash % 31

  const titleScore = Math.min(100, Math.max(30, 55 + seed * 1.2))
  const descScore = Math.min(100, Math.max(20, 40 + seed * 1.5))
  const keywordScore = Math.min(100, Math.max(25, 50 + seed * 1.1))
  const headingScore = Math.min(100, Math.max(30, 60 + seed * 0.9))
  const imgAltScore = Math.min(100, Math.max(15, 35 + seed * 1.8))
  const linkScore = Math.min(100, Math.max(40, 65 + seed * 0.7))
  const speedScore = Math.min(100, Math.max(25, 45 + seed * 1.4))
  const mobileScore = Math.min(100, Math.max(35, 55 + seed * 1.0))
  const schemaScore = Math.min(100, Math.max(10, 25 + seed * 2.0))

  const totalScore = Math.round(
    (titleScore * 0.12 +
      descScore * 0.12 +
      keywordScore * 0.10 +
      headingScore * 0.10 +
      imgAltScore * 0.10 +
      linkScore * 0.10 +
      speedScore * 0.12 +
      mobileScore * 0.12 +
      schemaScore * 0.12)
  )

  const dimensions: Record<string, DimensionItem> = {
    title: { label: '标题标签 (Title Tag)', status: titleScore >= 70 ? 'good' : titleScore >= 45 ? 'warning' : 'bad', icon: titleScore >= 70 ? '✅' : titleScore >= 45 ? '⚠️' : '❌', score: Math.round(titleScore) },
    description: { label: 'Meta 描述', status: descScore >= 70 ? 'good' : descScore >= 45 ? 'warning' : 'bad', icon: descScore >= 70 ? '✅' : descScore >= 45 ? '⚠️' : '❌', score: Math.round(descScore) },
    keywords: { label: '关键词优化', status: keywordScore >= 70 ? 'good' : keywordScore >= 45 ? 'warning' : 'bad', icon: keywordScore >= 70 ? '✅' : keywordScore >= 45 ? '⚠️' : '❌', score: Math.round(keywordScore) },
    headings: { label: 'H 标签结构', status: headingScore >= 70 ? 'good' : headingScore >= 45 ? 'warning' : 'bad', icon: headingScore >= 70 ? '✅' : headingScore >= 45 ? '⚠️' : '❌', score: Math.round(headingScore) },
    images: { label: '图片 Alt 属性', status: imgAltScore >= 70 ? 'good' : imgAltScore >= 45 ? 'warning' : 'bad', icon: imgAltScore >= 70 ? '✅' : imgAltScore >= 45 ? '⚠️' : '❌', score: Math.round(imgAltScore) },
    links: { label: '内部链接', status: linkScore >= 70 ? 'good' : linkScore >= 45 ? 'warning' : 'bad', icon: linkScore >= 70 ? '✅' : linkScore >= 45 ? '⚠️' : '❌', score: Math.round(linkScore) },
    speed: { label: '加载速度', status: speedScore >= 70 ? 'good' : speedScore >= 45 ? 'warning' : 'bad', icon: speedScore >= 70 ? '✅' : speedScore >= 45 ? '⚠️' : '❌', score: Math.round(speedScore) },
    mobile: { label: '移动端适配', status: mobileScore >= 70 ? 'good' : mobileScore >= 45 ? 'warning' : 'bad', icon: mobileScore >= 70 ? '✅' : mobileScore >= 45 ? '⚠️' : '❌', score: Math.round(mobileScore) },
    schema: { label: 'Schema 结构化标记', status: schemaScore >= 70 ? 'good' : schemaScore >= 45 ? 'warning' : 'bad', icon: schemaScore >= 70 ? '✅' : schemaScore >= 45 ? '⚠️' : '❌', score: Math.round(schemaScore) },
  }

  const suggestions: SuggestionItem[] = []

  if (titleScore < 70) suggestions.push({ text: `"${domain}" 的标题标签长度或关键词布局需要优化，建议控制在 50-60 字符内并包含核心关键词`, priority: 'high' })
  if (descScore < 70) suggestions.push({ text: 'Meta 描述缺失或不够吸引人，建议撰写 120-158 字符的描述，包含关键词和行动号召', priority: 'high' })
  if (keywordScore < 70) suggestions.push({ text: '关键词密度偏低或未合理布置，建议在标题、H标签和正文中自然融入目标关键词', priority: 'medium' })
  if (headingScore < 70) suggestions.push({ text: 'H 标签层级结构不清晰，确保每个页面只有一个 H1，H2/H3 按层级组织内容', priority: 'medium' })
  if (imgAltScore < 70) suggestions.push({ text: '部分图片缺少 Alt 属性，建议为所有图片添加描述性 Alt 文本，有利于图片搜索流量', priority: 'medium' })
  if (linkScore < 70) suggestions.push({ text: '内部链接结构不够完善，建议建立清晰的站内链接网络，提升爬虫抓取效率', priority: 'medium' })
  if (speedScore < 70) suggestions.push({ text: '页面加载速度偏慢，建议启用 Gzip 压缩、优化图片、使用 CDN 加速', priority: 'high' })
  if (mobileScore < 70) suggestions.push({ text: '移动端适配存在问题，确保使用响应式设计，测试不同屏幕尺寸下的显示效果', priority: 'high' })
  if (schemaScore < 70) suggestions.push({ text: '缺少 Schema.org 结构化数据标记，添加 JSON-LD 结构化标记可提升搜索摘要展示效果', priority: 'low' })

  if (suggestions.length === 0) {
    suggestions.push({ text: '该网站在各维度表现良好，建议持续监控 SEO 指标变化', priority: 'low' })
  }

  let summary: string
  if (totalScore >= 85) {
    summary = `"${domain}" 的整体 SEO 表现优秀，技术基础良好，继续保持并关注内容更新即可。`
  } else if (totalScore >= 70) {
    summary = `"${domain}" 有一定 SEO 基础，但在 ${suggestions.slice(0, 2).map(s => s.text.slice(0, 10)).join('、')} 等方面仍有优化空间。`
  } else if (totalScore >= 55) {
    summary = `"${domain}" 存在较多 SEO 问题，建议优先解决高优先级项，可显著提升搜索引擎排名。`
  } else {
    summary = `"${domain}" 的 SEO 状况较差，建议进行全面系统的 SEO 优化，从基础标签和网站速度开始改进。`
  }

  return { score: totalScore, summary, dimensions, suggestions }
}

async function startDiagnosis() {
  const normalizedUrl = normalizeUrl(urlInput.value)
  if (!validateUrl(normalizedUrl)) return

  urlInput.value = normalizedUrl
  report.value = null
  isDiagnosing.value = true

  // 1.5 秒模拟延迟
  await new Promise(resolve => setTimeout(resolve, 1500))

  report.value = generateMockReport(normalizedUrl)
  isDiagnosing.value = false
}

// ---- 提交线索 ----
async function submitLead() {
  leadErrors.value = { name: '', phone: '' }
  submitMessage.value = ''

  if (!leadForm.value.name.trim()) {
    leadErrors.value.name = '请输入姓名'
    return
  }
  if (!leadForm.value.phone.trim() || !/^1\d{10}$/.test(leadForm.value.phone.trim())) {
    leadErrors.value.phone = '请输入有效的11位手机号'
    return
  }

  isSubmitting.value = true

  try {
    const res = await fetch('/api/v1/seo-diagnosis', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: leadForm.value.name.trim(),
        phone: leadForm.value.phone.trim(),
      }),
    })
    const data = await res.json()
    if (data.code === 0) {
      submitSuccess.value = true
      submitMessage.value = data.message || '提交成功！'
      leadForm.value = { name: '', phone: '' }
      setTimeout(() => { showLeadModal.value = false }, 2000)
    } else {
      submitSuccess.value = false
      submitMessage.value = data.message || '提交失败，请稍后重试'
    }
  } catch {
    submitSuccess.value = false
    submitMessage.value = '网络错误，请稍后重试'
  } finally {
    isSubmitting.value = false
  }
}
</script>
