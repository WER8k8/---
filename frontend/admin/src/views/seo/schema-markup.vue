<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-xl font-semibold text-gray-800">
        Schema标记管理
      </h2>
      <div class="flex items-center gap-3">
        <button
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
            activeTab === 'generator'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          ]"
          @click="activeTab = 'generator'"
        >
          生成器
        </button>
        <button
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
            activeTab === 'list'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          ]"
          @click="activeTab = 'list'"
        >
          已保存列表
        </button>
      </div>
    </div>

    <!-- Schema生成器 -->
    <div
      v-if="activeTab === 'generator'"
      class="bg-white rounded-xl shadow-sm border border-gray-100"
    >
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
        <!-- 左侧：配置面板 -->
        <div>
          <h3 class="text-lg font-semibold text-gray-800 mb-4">
            Schema生成器
          </h3>
          
          <!-- Schema类型选择 -->
          <div class="mb-4">
            <label class="block text-sm font-medium text-gray-700 mb-2">Schema类型</label>
            <select
              v-model="form.schemaType"
              class="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              @change="onSchemaTypeChange"
            >
              <option value="">
                请选择Schema类型
              </option>
              <option
                v-for="type in schemaTypes"
                :key="type"
                :value="type"
              >
                {{ type }}
              </option>
            </select>
          </div>

          <!-- 表单字段 -->
          <div
            v-if="currentTemplate"
            class="space-y-4"
          >
            <div
              v-for="(field, key) in templateFields"
              :key="key"
              class="form-field"
            >
              <label class="block text-sm font-medium text-gray-700 mb-1">{{ field.label }}</label>
              <input
                v-if="field.type === 'text'"
                v-model="form.data[key]"
                :placeholder="field.placeholder"
                class="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              >
              <textarea
                v-else-if="field.type === 'textarea'"
                v-model="form.data[key]"
                :placeholder="field.placeholder"
                rows="3"
                class="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors resize-none"
              />
              <input
                v-else-if="field.type === 'number'"
                v-model.number="form.data[key]"
                :placeholder="field.placeholder"
                type="number"
                class="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              >
            </div>
          </div>

          <!-- 包含上下文选项 -->
          <div class="flex items-center justify-between py-4">
            <span class="text-sm text-gray-600">包含上下文信息</span>
            <label class="relative inline-flex items-center cursor-pointer">
              <input
                v-model="form.includeContext"
                type="checkbox"
                class="sr-only peer"
              >
              <div class="w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-500" />
            </label>
          </div>

          <!-- 生成按钮 -->
          <button
            :disabled="!form.schemaType || isGenerating"
            class="w-full py-3 px-4 bg-blue-500 text-white font-medium rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            @click="generateSchema"
          >
            <svg
              v-if="isGenerating"
              class="animate-spin h-5 w-5"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
                fill="none"
              />
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            {{ isGenerating ? '生成中...' : '生成Schema标记' }}
          </button>
        </div>

        <!-- 右侧：结果预览 -->
        <div>
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-800">
              生成结果
            </h3>
            <div
              v-if="generatedSchema"
              class="flex gap-2"
            >
              <button
                class="px-3 py-1.5 text-sm text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-1"
                @click="copyToClipboard"
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
                    d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
                </svg>
                {{ copied ? '已复制' : '复制' }}
              </button>
              <button
                class="px-3 py-1.5 text-sm text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors flex items-center gap-1"
                @click="validateSchema"
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
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                验证
              </button>
            </div>
          </div>

          <!-- 结果区域 -->
          <div
            v-if="generatedSchema"
            class="space-y-4"
          >
            <!-- 验证结果 -->
            <div
              v-if="validationResult"
              class="p-4 rounded-lg"
              :class="validationResult.is_valid ? 'bg-green-50' : 'bg-red-50'"
            >
              <div class="flex items-center gap-2 mb-2">
                <svg
                  v-if="validationResult.is_valid"
                  class="w-5 h-5 text-green-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                <svg
                  v-else
                  class="w-5 h-5 text-red-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <span
                  class="font-medium"
                  :class="validationResult.is_valid ? 'text-green-700' : 'text-red-700'"
                >
                  {{ validationResult.is_valid ? '验证通过' : '验证失败' }}
                </span>
              </div>
              <div
                v-if="validationResult.errors.length > 0"
                class="text-sm text-red-600 space-y-1"
              >
                <p
                  v-for="(error, index) in validationResult.errors"
                  :key="index"
                >
                  • {{ error.message }}
                </p>
              </div>
              <div
                v-if="validationResult.warnings.length > 0"
                class="text-sm text-yellow-600 space-y-1"
              >
                <p
                  v-for="(warning, index) in validationResult.warnings"
                  :key="index"
                >
                  • {{ warning.message }}
                </p>
              </div>
            </div>

            <!-- JSON-LD 输出 -->
            <div class="bg-gray-50 rounded-lg p-4 max-h-96 overflow-auto">
              <pre class="text-sm text-gray-700 whitespace-pre-wrap">{{ generatedSchema }}</pre>
            </div>
          </div>

          <!-- 空状态 -->
          <div
            v-else
            class="h-64 flex items-center justify-center text-gray-400 border border-dashed border-gray-200 rounded-lg"
          >
            <div class="text-center">
              <svg
                class="w-12 h-12 mx-auto mb-3 opacity-50"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="1.5"
                  d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
                />
              </svg>
              <p>选择Schema类型并填写数据</p>
              <p class="text-sm">
                点击生成按钮获取JSON-LD代码
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 已保存列表 -->
    <div
      v-else
      class="bg-white rounded-xl shadow-sm border border-gray-100"
    >
      <!-- 搜索栏 -->
      <div class="p-4 border-b border-gray-100">
        <div class="flex items-center justify-between">
          <div class="relative flex-1 max-w-md">
            <svg
              class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
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
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索Schema标记..."
              class="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
            >
          </div>
          <button
            class="px-4 py-2.5 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2"
            @click="refreshList"
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
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            刷新
          </button>
        </div>
      </div>

      <!-- 列表内容 -->
      <div
        v-if="schemaList.length > 0"
        class="divide-y divide-gray-100"
      >
        <div
          v-for="item in filteredSchemaList"
          :key="item.id"
          class="p-4 hover:bg-gray-50 transition-colors"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <svg
                  class="w-5 h-5 text-blue-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
                  />
                </svg>
              </div>
              <div>
                <div class="font-medium text-gray-800">
                  {{ item.name }}
                </div>
                <div class="text-sm text-gray-500">
                  {{ item.schema_type }} · {{ formatDate(item.created_at) }}
                </div>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <button
                class="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                @click="viewSchema(item)"
              >
                查看
              </button>
              <button
                class="px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                @click="exportSchema(item)"
              >
                导出
              </button>
              <button
                class="px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                @click="deleteSchema(item.id)"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div
        v-else
        class="py-16 text-center"
      >
        <svg
          class="w-16 h-16 mx-auto text-gray-300 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="1.5"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <p class="text-gray-500">
          暂无保存的Schema标记
        </p>
        <p class="text-sm text-gray-400 mt-1">
          使用生成器创建第一个Schema标记
        </p>
      </div>
    </div>

    <!-- 查看弹窗 -->
    <div
      v-if="viewModal.show"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click.self="closeViewModal"
    >
      <div class="bg-white rounded-xl shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-hidden">
        <div class="p-4 border-b border-gray-100 flex items-center justify-between">
          <h3 class="font-semibold text-gray-800">
            {{ viewModal.data?.name }}
          </h3>
          <button
            class="text-gray-400 hover:text-gray-600"
            @click="closeViewModal"
          >
            <svg
              class="w-6 h-6"
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
        <div class="p-4 overflow-auto max-h-[60vh]">
          <div class="bg-gray-50 rounded-lg p-4">
            <pre class="text-sm text-gray-700 whitespace-pre-wrap">{{ JSON.stringify(viewModal.data?.content, null, 2) }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { seoAPI } from '@/api'

const schemaTypes = ref<string[]>([])
const activeTab = ref('generator')
const searchQuery = ref('')
const isGenerating = ref(false)
const copied = ref(false)
const generatedSchema = ref('')
const validationResult = ref<{
  is_valid: boolean
  errors: Array<{ code: string; message: string }>
  warnings: Array<{ code: string; message: string }>
  schema_type?: string
} | null>(null)

const form = ref({
  schemaType: '',
  data: {} as Record<string, string | number | undefined>,
  includeContext: true,
})

const schemaList = ref<Array<{
  id: string
  name: string
  schema_type: string
  content: Record<string, unknown>
  page_url?: string
  created_at: string
}>>([])

const viewModal = ref({
  show: false,
  data: null as typeof schemaList.value[0] | null,
})

const templateFields = computed(() => {
  const fields: Record<string, { type: string; label: string; placeholder: string }> = {}
  
  switch (form.value.schemaType) {
    case 'Organization':
      fields.name = { type: 'text', label: '企业名称', placeholder: '优丁建材有限公司' }
      fields.description = { type: 'textarea', label: '企业描述', placeholder: '专业轻集料混凝土生产商' }
      fields.url = { type: 'text', label: '官网地址', placeholder: 'https://www.youdingjiancai.com' }
      fields.logo = { type: 'text', label: 'Logo地址', placeholder: 'https://www.youdingjiancai.com/logo.png' }
      fields.phone = { type: 'text', label: '联系电话', placeholder: '400-888-8888' }
      fields.address = { type: 'text', label: '详细地址', placeholder: '北京市朝阳区xxx路xxx号' }
      fields.city = { type: 'text', label: '城市', placeholder: '北京' }
      break
    case 'Product':
      fields.name = { type: 'text', label: '产品名称', placeholder: 'LC10轻集料混凝土' }
      fields.description = { type: 'textarea', label: '产品描述', placeholder: '优质轻集料混凝土，密度800-1950kg/m³' }
      fields.brand = { type: 'text', label: '品牌', placeholder: '优丁建材' }
      fields.sku = { type: 'text', label: '产品编号', placeholder: 'LC10-25KG' }
      fields.image = { type: 'text', label: '产品图片', placeholder: 'https://.../product.jpg' }
      fields.url = { type: 'text', label: '产品页面', placeholder: 'https://.../products/lc10' }
      fields.price = { type: 'number', label: '价格', placeholder: '150' }
      break
    case 'Article':
      fields.headline = { type: 'text', label: '文章标题', placeholder: '轻集料混凝土的应用优势' }
      fields.description = { type: 'textarea', label: '文章摘要', placeholder: '本文介绍轻集料混凝土的技术特点和应用场景...' }
      fields.content = { type: 'textarea', label: '文章内容', placeholder: '轻集料混凝土是一种新型建筑材料...' }
      fields.author_name = { type: 'text', label: '作者名称', placeholder: '优丁技术团队' }
      fields.published_date = { type: 'text', label: '发布日期', placeholder: '2024-01-15' }
      break
    case 'FAQPage':
      fields.questions = { type: 'textarea', label: 'FAQ内容（JSON格式）', placeholder: '[{\"question\": \"问题1\", \"answer\": \"答案1\"}]' }
      break
    case 'BreadcrumbList':
      fields.items = { type: 'textarea', label: '面包屑项目（JSON格式）', placeholder: '[{\"name\": \"首页\", \"url\": \"/\"}]' }
      break
    case 'LocalBusiness':
      fields.name = { type: 'text', label: '店铺名称', placeholder: '优丁建材旗舰店' }
      fields.phone = { type: 'text', label: '联系电话', placeholder: '010-88888888' }
      fields.address = { type: 'text', label: '详细地址', placeholder: '北京市朝阳区xxx路xxx号' }
      fields.city = { type: 'text', label: '城市', placeholder: '北京' }
      break
  }
  
  return fields
})

const currentTemplate = computed(() => form.value.schemaType)

const filteredSchemaList = computed(() => {
  if (!searchQuery.value) return schemaList.value
  const query = searchQuery.value.toLowerCase()
  return schemaList.value.filter(
    item => item.name.toLowerCase().includes(query) || 
            item.schema_type.toLowerCase().includes(query)
  )
})

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const onSchemaTypeChange = async () => {
  if (!form.value.schemaType) return
  form.value.data = {}
}

const generateSchema = async () => {
  if (!form.value.schemaType) return
  
  isGenerating.value = true
  validationResult.value = null
  
  try {
    const result = await seoAPI.schemaGenerate({
      schema_type: form.value.schemaType,
      data: form.value.data,
      include_context: form.value.includeContext,
    })
    
    if (result.data.success) {
      generatedSchema.value = result.data.json_ld
    }
  } catch (error) {
    console.error('生成Schema失败:', error)
  } finally {
    isGenerating.value = false
  }
}

const validateSchema = async () => {
  if (!generatedSchema.value) return
  
  try {
    const schemaContent = JSON.parse(generatedSchema.value)
    const result = await seoAPI.schemaValidate({ content: schemaContent })
    validationResult.value = result.data
  } catch (error) {
    console.error('验证Schema失败:', error)
  }
}

const copyToClipboard = async () => {
  if (!generatedSchema.value) return
  
  try {
    await navigator.clipboard.writeText(generatedSchema.value)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (error) {
    console.error('复制失败:', error)
  }
}

const refreshList = async () => {
  try {
    const result = await seoAPI.schemaList()
    schemaList.value = result.data || []
  } catch (error) {
    console.error('获取Schema列表失败:', error)
  }
}

const viewSchema = (item: typeof schemaList.value[0]) => {
  viewModal.value = {
    show: true,
    data: item,
  }
}

const closeViewModal = () => {
  viewModal.value = {
    show: false,
    data: null,
  }
}

const exportSchema = async (item: typeof schemaList.value[0]) => {
  try {
    const result = await seoAPI.schemaExport(item.id)
    const blob = new Blob([result.data.json_ld], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${item.name}-schema.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('导出Schema失败:', error)
  }
}

const deleteSchema = async (id: string) => {
  if (!confirm('确定要删除这个Schema标记吗？')) return
  
  try {
    await seoAPI.schemaDelete(id)
    await refreshList()
  } catch (error) {
    console.error('删除Schema失败:', error)
  }
}

const init = async () => {
  try {
    const result = await seoAPI.schemaTypes()
    schemaTypes.value = result.data.types || []
  } catch (error) {
    console.error('获取Schema类型失败:', error)
  }
}

onMounted(() => {
  init()
})
</script>
