<template>
  <div class="space-y-4">
    <div
      v-if="!file"
      class="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-brand-blue transition-colors cursor-pointer"
      @click="triggerUpload"
    >
      <div class="text-gray-400 mb-2">
        <svg
          class="w-10 h-10 mx-auto"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="1.5"
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
      </div>
      <p class="text-sm text-gray-500">
        点击或拖拽文件到此区域上传
      </p>
      <p class="text-xs text-gray-400 mt-1">
        支持 PDF、CAD、图片等格式，最大 20MB
      </p>
    </div>
    <div
      v-else
      class="bg-gray-50 border border-gray-200 rounded-lg p-4"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 bg-brand-blue/10 rounded-lg flex items-center justify-center text-brand-blue text-lg">
            {{ fileIcon }}
          </div>
          <div>
            <p class="text-sm font-medium text-gray-900">
              {{ file.name }}
            </p>
            <p class="text-xs text-gray-500">
              {{ (file.size / 1024 / 1024).toFixed(1) }} MB
            </p>
          </div>
        </div>
        <button
          class="text-gray-400 hover:text-red-500 transition-colors"
          @click="removeFile"
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
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
      <div
        v-if="uploading"
        class="mt-3"
      >
        <div class="bg-gray-200 rounded-full h-1.5">
          <div
            class="bg-brand-blue h-1.5 rounded-full transition-all"
            :style="{ width: uploadProgress + '%' }"
          />
        </div>
        <p class="text-xs text-gray-400 mt-1">
          {{ uploadProgress }}%
        </p>
      </div>
      <div
        v-if="uploadedUrl"
        class="mt-2 flex items-center space-x-2"
      >
        <span class="text-xs text-green-600">✓ 上传成功</span>
        <button
          class="text-xs text-brand-blue hover:text-blue-800"
          @click="copyUrl"
        >
          复制链接
        </button>
      </div>
    </div>
    <input
      ref="fileInputRef"
      type="file"
      class="hidden"
      :accept="accept"
      @change="onFileSelected"
    >

    <div
      v-if="showDocType"
      class="grid grid-cols-2 md:grid-cols-5 gap-2"
    >
      <button
        v-for="dt in docTypes"
        :key="dt.value"
        :class="selectedDocType === dt.value ? 'bg-brand-blue text-white border-brand-blue' : 'bg-white text-gray-600 border-gray-300 hover:border-gray-400'"
        class="px-3 py-2 rounded-lg text-xs font-medium border transition-colors"
        @click="selectedDocType = dt.value"
      >
        {{ dt.label }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  accept?: string
  showDocType?: boolean
  apiEndpoint?: string
}>()

const emit = defineEmits<{
  (e: 'uploaded', result: { url: string; filename: string; docType: string }): void
  (e: 'error', message: string): void
}>()

const fileInputRef = ref<HTMLInputElement>()
const file = ref<File | null>(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadedUrl = ref('')
const selectedDocType = ref('pdf')

const docTypes = [
  { value: 'pdf', label: '规格书' },
  { value: 'cad', label: 'CAD图纸' },
  { value: 'report', label: '检测报告' },
  { value: 'certificate', label: '资质证书' },
  { value: 'other', label: '其他' },
]

const fileIcon = computed(() => {
  if (!file.value) return '📄'
  const ext = file.value.name.split('.').pop()?.toLowerCase()
  if (ext === 'pdf') return '📕'
  if (['dwg', 'dxf'].includes(ext || '')) return '📐'
  if (['jpg', 'jpeg', 'png', 'webp'].includes(ext || '')) return '🖼'
  return '📄'
})

function triggerUpload() {
  fileInputRef.value?.click()
}

function onFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.length) {
    file.value = input.files[0]
    uploadFile()
  }
}

function removeFile() {
  file.value = null
  uploadedUrl.value = ''
  uploadProgress.value = 0
}

async function uploadFile() {
  if (!file.value) return
  uploading.value = true
  uploadProgress.value = 0
  try {
    const token = localStorage.getItem('admin_token')
    const formData = new FormData()
    formData.append('file', file.value)
    formData.append('doc_type', selectedDocType.value)
    formData.append('description', '')

    const res = await fetch(props.apiEndpoint || '/api/v1/system/upload', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData,
    })

    uploadProgress.value = 100

    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || '上传失败')
    }

    const result = await res.json()
    uploadedUrl.value = result.url
    emit('uploaded', { url: result.url, filename: result.filename || file.value.name, docType: selectedDocType.value })
  } catch (e: any) {
    emit('error', e.message)
    removeFile()
  } finally {
    uploading.value = false
  }
}

async function copyUrl() {
  if (uploadedUrl.value) {
    try {
      await navigator.clipboard.writeText(uploadedUrl.value)
    } catch {
      const input = document.createElement('input')
      input.value = uploadedUrl.value
      document.body.appendChild(input)
      input.select()
      document.execCommand('copy')
      document.body.removeChild(input)
    }
  }
}
</script>
