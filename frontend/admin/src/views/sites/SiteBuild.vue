/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="p-6 max-w-4xl mx-auto">
    <h1 class="text-2xl font-bold text-gray-800 mb-6 flex items-center">
      <span class="mr-3">🏗️</span>一键建站
    </h1>

    <!-- 步骤指示器 -->
    <div class="flex items-center mb-8">
      <div
        v-for="(step, idx) in steps"
        :key="idx"
        class="flex items-center"
      >
        <div
          :class="[
            'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold',
            currentStep > idx ? 'bg-green-500 text-white' : currentStep === idx ? 'bg-blue-500 text-white' : 'bg-gray-300 text-gray-600'
          ]"
        >
          {{ idx + 1 }}
        </div>
        <span class="ml-2 text-sm text-gray-600">{{ step }}</span>
        <div v-if="idx < steps.length - 1" class="w-12 h-0.5 bg-gray-300 mx-3"></div>
      </div>
    </div>

    <!-- 步骤1: 上传产品图片 -->
    <div v-if="currentStep === 0" class="bg-white rounded-lg shadow p-6">
      <h2 class="text-lg font-semibold mb-4">上传产品图片</h2>
      <div
        class="border-2 border-dashed border-gray-300 rounded-lg p-10 text-center cursor-pointer hover:border-blue-400 transition-colors"
        @click="triggerUpload"
        @dragover.prevent="dragOver = true"
        @dragleave="dragOver = false"
        @drop.prevent="handleDrop"
        :class="{ 'border-blue-400 bg-blue-50': dragOver }"
      >
        <input ref="fileInput" type="file" class="hidden" multiple accept="image/*" @change="handleFileSelect" />
        <div v-if="form.images.length === 0">
          <div class="text-4xl mb-2">📦</div>
          <p class="text-gray-500">拖拽图片到此处或点击上传</p>
          <p class="text-sm text-gray-400 mt-1">支持 JPG/PNG，单张最大 10MB</p>
        </div>
        <div v-else class="flex flex-wrap gap-3 justify-center">
          <div v-for="(img, i) in form.images" :key="i" class="relative w-24 h-24 rounded overflow-hidden border">
            <img :src="img.preview" class="w-full h-full object-cover" />
            <button class="absolute top-0 right-0 bg-red-500 text-white w-5 h-5 rounded-bl text-xs" @click.stop="removeImage(i)">×</button>
          </div>
        </div>
      </div>
      <div class="mt-4 flex justify-end">
        <button
          class="px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          :disabled="form.images.length === 0"
          @click="currentStep = 1"
        >
          下一步：填写资料
        </button>
      </div>
    </div>

    <!-- 步骤2: 填写产品资料 -->
    <div v-if="currentStep === 1" class="bg-white rounded-lg shadow p-6">
      <h2 class="text-lg font-semibold mb-4">填写产品资料</h2>
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">产品名称 *</label>
          <input v-model="form.name" type="text" class="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-300 outline-none" placeholder="输入产品名称" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">产品描述 *</label>
          <textarea v-model="form.description" rows="4" class="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-300 outline-none" placeholder="用自然语言描述产品特性、应用场景、目标客户..."></textarea>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">目标市场</label>
            <select v-model="form.targetMarket" class="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-300 outline-none">
              <option value="">选择目标市场</option>
              <option value="us">北美</option>
              <option value="eu">欧洲</option>
              <option value="sea">东南亚</option>
              <option value="中东">中东</option>
              <option value="global">全球</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">主要语言</label>
            <select v-model="form.language" class="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-300 outline-none">
              <option value="en">English</option>
              <option value="zh">中文</option>
              <option value="es">Español</option>
              <option value="fr">Français</option>
              <option value="ar">العربية</option>
              <option value="ja">日本語</option>
            </select>
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">行业品类</label>
          <input v-model="form.industry" type="text" class="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-300 outline-none" placeholder="如: Building Materials, Industrial Equipment..." />
        </div>
      </div>
      <div class="mt-4 flex justify-between">
        <button class="px-6 py-2 border text-gray-600 rounded hover:bg-gray-50" @click="currentStep = 0">上一步</button>
        <button
          class="px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          :disabled="!form.name || !form.description"
          @click="currentStep = 2"
        >
          下一步：确认生成
        </button>
      </div>
    </div>

    <!-- 步骤3: 确认并生成 -->
    <div v-if="currentStep === 2" class="bg-white rounded-lg shadow p-6">
      <h2 class="text-lg font-semibold mb-4">确认并生成网站</h2>
      <div class="bg-gray-50 rounded p-4 space-y-2 text-sm">
        <div class="flex justify-between"><span class="text-gray-500">产品图片:</span><span>{{ form.images.length }} 张</span></div>
        <div class="flex justify-between"><span class="text-gray-500">产品名称:</span><span>{{ form.name }}</span></div>
        <div class="flex justify-between"><span class="text-gray-500">目标市场:</span><span>{{ form.targetMarket || '未指定' }}</span></div>
        <div class="flex justify-between"><span class="text-gray-500">主要语言:</span><span>{{ form.language }}</span></div>
        <div class="flex justify-between"><span class="text-gray-500">行业品类:</span><span>{{ form.industry || '未指定' }}</span></div>
      </div>

      <!-- 进度条 -->
      <div v-if="building" class="mt-6">
        <div class="flex items-center mb-2">
          <div class="animate-spin w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full mr-3"></div>
          <span class="text-sm text-gray-600">{{ buildStatus }}</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-2">
          <div class="bg-blue-500 h-2 rounded-full transition-all duration-500" :style="{ width: buildProgress + '%' }"></div>
        </div>
      </div>

      <!-- 结果 -->
      <div v-if="result" class="mt-6 bg-green-50 border border-green-200 rounded p-4">
        <div class="flex items-center text-green-700 font-medium mb-2">
          <span class="mr-2">✅</span>建站成功！
        </div>
        <div class="text-sm text-gray-600 space-y-1">
          <div>站点ID: <code class="bg-gray-100 px-1 rounded">{{ result.site_id }}</code></div>
          <div>生成页面: {{ result.pages?.length || 0 }} 个</div>
          <div v-if="result.pages?.length" class="mt-2">
            <a
              v-for="page in result.pages"
              :key="page.url"
              :href="page.url"
              target="_blank"
              class="inline-block mr-2 mb-1 text-blue-500 hover:underline text-xs bg-blue-50 px-2 py-1 rounded"
            >
              {{ page.title }}
            </a>
          </div>
        </div>
      </div>

      <!-- 错误 -->
      <div v-if="error" class="mt-6 bg-red-50 border border-red-200 rounded p-4">
        <div class="flex items-center text-red-700 font-medium mb-2">
          <span class="mr-2">❌</span>建站失败
        </div>
        <p class="text-sm text-red-600">{{ error }}</p>
      </div>

      <div class="mt-6 flex justify-between">
        <button class="px-6 py-2 border text-gray-600 rounded hover:bg-gray-50" :disabled="building" @click="currentStep = 1">上一步</button>
        <button
          v-if="!result"
          class="px-6 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
          :disabled="building"
          @click="startBuild"
        >
          {{ building ? '生成中...' : '开始生成网站' }}
        </button>
        <button v-else class="px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600" @click="resetForm">
          再建一个
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import axios from 'axios'

const steps = ['上传图片', '填写资料', '确认生成']
const currentStep = ref(0)
const dragOver = ref(false)
const building = ref(false)
const buildProgress = ref(0)
const buildStatus = ref('')
const result = ref<any>(null)
const error = ref('')

const fileInput = ref<HTMLInputElement>()

const form = reactive({
  images: [] as Array<{ file: File; preview: string }>,
  name: '',
  description: '',
  targetMarket: '',
  language: 'en',
  industry: '',
})

function triggerUpload() {
  fileInput.value?.click()
}

function handleFileSelect(e: Event) {
  const files = (e.target as HTMLInputElement).files
  if (files) addFiles(Array.from(files))
}

function handleDrop(e: DragEvent) {
  dragOver.value = false
  const files = Array.from(e.dataTransfer?.files || []).filter(f => f.type.startsWith('image/'))
  addFiles(files)
}

function addFiles(files: File[]) {
  files.forEach(file => {
    const reader = new FileReader()
    reader.onload = (e) => {
      form.images.push({ file, preview: e.target?.result as string })
    }
    reader.readAsDataURL(file)
  })
}

function removeImage(idx: number) {
  form.images.splice(idx, 1)
}

async function startBuild() {
  building.value = true
  buildProgress.value = 0
  error.value = ''
  result.value = null

  const progressSteps = [
    { p: 15, t: '正在分析产品图片...' },
    { p: 35, t: '正在生成网站结构...' },
    { p: 55, t: '正在生成多语言内容...' },
    { p: 75, t: '正在优化SEO...' },
    { p: 90, t: '正在组装站点...' },
    { p: 100, t: '建站完成!' },
  ]

  const progressTimer = setInterval(() => {
    const step = progressSteps.find(s => s.p > buildProgress.value)
    if (step) {
      buildProgress.value = step.p
      buildStatus.value = step.t
    }
  }, 800)

  try {
    const payload = {
      name: form.name,
      description: form.description,
      target_market: form.targetMarket,
      language: form.language,
      industry: form.industry,
      images_count: form.images.length,
    }
    const { data } = await axios.post('/api/v1/sites/build', payload)
    result.value = data
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || '未知错误'
  } finally {
    clearInterval(progressTimer)
    building.value = false
  }
}

function resetForm() {
  currentStep.value = 0
  buildProgress.value = 0
  buildStatus.value = ''
  result.value = null
  error.value = ''
  form.images = []
  form.name = ''
  form.description = ''
  form.targetMarket = ''
  form.language = 'en'
  form.industry = ''
}
</script>
