<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 页面头部 -->
    <div class="bg-white border-b border-gray-200 px-6 py-4">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-xl font-semibold text-gray-800">
            Schema标记管理
          </h1>
          <p class="text-sm text-gray-500 mt-1">
            生成和管理结构化数据标记，提升搜索引擎可见性
          </p>
        </div>
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
    </div>

    <!-- 主内容区 -->
    <div class="p-6">
      <!-- Schema生成器 -->
      <div v-if="activeTab === 'generator'">
        <SchemaMarkupGenerator />
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
import { ref, computed } from 'vue'
import { useApi } from '~/composables/useApi'
import SchemaMarkupGenerator from '~/components/seo/SchemaMarkupGenerator.vue'

const api = useApi()

const activeTab = ref('generator')
const searchQuery = ref('')
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

const refreshList = async () => {
  try {
    const response = await api.get('/api/v1/seo/schema')
    schemaList.value = response || []
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
    const response = await api.get(`/api/v1/seo/schema/export/${item.id}`)
    const blob = new Blob([response.json_ld], { type: 'application/json' })
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
    await api.delete(`/api/v1/seo/schema/${id}`)
    await refreshList()
  } catch (error) {
    console.error('删除Schema失败:', error)
  }
}

// 初始化加载列表
if (activeTab.value === 'list') {
  refreshList()
}
</script>
