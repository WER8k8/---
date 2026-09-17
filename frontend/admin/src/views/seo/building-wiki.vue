/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="AI建材百科" subtitle="AI自动生成建材行业知识文章并发布到网站" surface="elevated">
    <!-- 生成文章区域 -->
    <a-card class="mb-6" title="生成文章" :bordered="false">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <a-input v-model="keyword" placeholder="输入主题关键词，如：轻集料混凝土" size="large">
          <template #prefix><SearchOutlined /></template>
        </a-input>
        <a-select v-model="style" size="large" placeholder="选择文章风格">
          <a-select-option value="科普风">科普风</a-select-option>
          <a-select-option value="技术篇">技术篇</a-select-option>
          <a-select-option value="选购指南">选购指南</a-select-option>
          <a-select-option value="对比分析">对比分析</a-select-option>
          <a-select-option value="行业趋势">行业趋势</a-select-option>
        </a-select>
        <a-button type="primary" size="large" :loading="generating" @click="handleGenerate" class="h-full">
          <template #icon><BulbOutlined /></template>
          AI生成文章
        </a-button>
      </div>

      <!-- 内置关键词快捷入口 -->
      <div class="flex flex-wrap gap-2 mt-2">
        <span class="text-xs text-gray-400 leading-7">内置关键词：</span>
        <a-tag
          v-for="kw in builtinKeywords"
          :key="kw"
          color="blue"
          class="cursor-pointer hover:opacity-80"
          @click="keyword = kw"
        >
          {{ kw }}
        </a-tag>
      </div>
    </a-card>

    <!-- 文章预览 -->
    <a-card v-if="previewArticle" class="mb-6" :bordered="false">
      <template #title>
        <div class="flex items-center justify-between">
          <span>文章预览</span>
          <a-tag :color="previewArticle.status === 'published' ? 'green' : 'orange'">
            {{ previewArticle.status === 'published' ? '已发布' : '草稿' }}
          </a-tag>
        </div>
      </template>
      <div class="prose max-w-none">
        <h2 class="text-xl font-bold text-gray-900 mb-4">{{ previewArticle.title }}</h2>
        <div class="text-sm text-gray-400 mb-4">
          <span v-if="previewArticle.published_at">发布于 {{ previewArticle.published_at }}</span>
          <span v-if="previewArticle.views" class="ml-4">{{ previewArticle.views }} 次浏览</span>
        </div>
        <div class="article-content text-gray-700 leading-relaxed whitespace-pre-line">
          {{ previewArticle.content }}
        </div>
      </div>
      <div class="mt-6 pt-4 border-t border-gray-100 flex flex-wrap gap-3">
        <a-button @click="handleEdit(previewArticle)">
          <template #icon><EditOutlined /></template>
          编辑
        </a-button>
        <a-button v-if="previewArticle.status !== 'published'" type="primary" @click="handlePublish(previewArticle.id)">
          <template #icon><SendOutlined /></template>
          发布到网站
        </a-button>
        <a-button v-else type="default" @click="handleUnpublish(previewArticle.id)">
          <template #icon><StopOutlined /></template>
          下架
        </a-button>
        <a-button danger @click="handleDelete(previewArticle.id)">
          <template #icon><DeleteOutlined /></template>
          删除
        </a-button>
      </div>
    </a-card>

    <!-- 文章列表 -->
    <a-card :bordered="false">
      <template #title>
        <div class="flex items-center justify-between">
          <span>已发布的文章</span>
          <a-select v-model="filterStatus" style="width: 120px" placeholder="全部状态" @change="(v) => fetchArticles(v as unknown as number)">
            <a-select-option value="">全部状态</a-select-option>
            <a-select-option value="published">已发布</a-select-option>
            <a-select-option value="draft">草稿</a-select-option>
          </a-select>
        </div>
      </template>
      <div ref="tablePanelRef" class="yd-panel yd-table-panel">
        <div class="panel-head mb-3">
          <YdTableToolbar :loading="tableLoading" :target-ref="tablePanelRef" :show-export="false" @refresh="() => fetchArticles()" />
        </div>
        <YdDataTable
          :columns="columns"
          :data-source="articles"
          :pagination="pagination"
          :loading="tableLoading"
          :table-props="{ size: tableSize, rowKey: 'id' }"
          @page-change="onPageChange"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'title'">
              <div class="font-medium text-gray-900 cursor-pointer hover:text-blue-600" @click="handlePreview(record)">
                {{ record.title }}
              </div>
              <div class="text-xs text-gray-400">关键词：{{ record.keyword }}</div>
            </template>
            <template v-else-if="column.key === 'status'">
              <a-tag :color="record.status === 'published' ? 'green' : 'orange'">
                {{ record.status === 'published' ? '已发布' : '草稿' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'style'">
              <a-tag>{{ record.style }}</a-tag>
            </template>
            <template v-else-if="column.key === 'published_at'">
              {{ record.published_at || '-' }}
            </template>
            <template v-else-if="column.key === 'views'">
              {{ record.views || 0 }}
            </template>
            <template v-else-if="column.key === 'actions'">
              <a-space>
                <a-button type="text" @click="handlePreview(record)" title="预览">
                  <template #icon><EyeOutlined /></template>
                </a-button>
                <a-button type="text" @click="handleEdit(record)" title="编辑">
                  <template #icon><EditOutlined /></template>
                </a-button>
                <a-button
                  v-if="record.status !== 'published'"
                  type="text"
                  class="text-green-600"
                  @click="handlePublish(record.id)"
                  title="发布"
                >
                  <template #icon><SendOutlined /></template>
                </a-button>
                <a-button
                  v-else
                  type="text"
                  @click="handleUnpublish(record.id)"
                  title="下架"
                >
                  <template #icon><StopOutlined /></template>
                </a-button>
                <a-button type="text" danger @click="handleDelete(record.id)" title="删除">
                  <template #icon><DeleteOutlined /></template>
                </a-button>
              </a-space>
            </template>
          </template>
        </YdDataTable>
      </div>
    </a-card>

    <!-- 编辑弹窗 -->
    <a-modal v-model:open="editModalVisible" title="编辑文章" width="800px" @ok="handleSaveEdit" :confirm-loading="saving">
      <a-form layout="vertical">
        <a-form-item label="标题">
          <a-input v-model="editForm.title" />
        </a-form-item>
        <a-form-item label="文章风格">
          <a-select v-model="editForm.style">
            <a-select-option value="科普风">科普风</a-select-option>
            <a-select-option value="技术篇">技术篇</a-select-option>
            <a-select-option value="选购指南">选购指南</a-select-option>
            <a-select-option value="对比分析">对比分析</a-select-option>
            <a-select-option value="行业趋势">行业趋势</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="正文">
          <a-textarea v-model="editForm.content" :rows="16" />
        </a-form-item>
      </a-form>
    </a-modal>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { YdDataTable, YdPage, YdTableToolbar } from '@/components/youding'
import { useUiPreferencesStore } from '@/stores/uiPreferences'
import {
  SearchOutlined,
  EditOutlined,
  SendOutlined,
  DeleteOutlined,
  EyeOutlined,
  StopOutlined,
  BulbOutlined,
} from '@ant-design/icons-vue'
import {
  Card as ACard,
  Input as AInput,
  Select as ASelect,
  SelectOption as ASelectOption,
  Button as AButton,
  Tag as ATag,
  Space as ASpace,
  Modal as AModal,
  Form as AForm,
  FormItem as AFormItem,
  Textarea as ATextarea,
  Modal,
  message,
} from 'ant-design-vue'
import api from '@/api'
import { ydConfirm } from '@/utils/ydModal'

const basePath = '/building-wiki'

const tablePanelRef = ref<HTMLElement | null>(null)
const ui = useUiPreferencesStore()
const { antTableSize: tableSize } = storeToRefs(ui)

// 内置关键词
const builtinKeywords = ['轻集料混凝土', '陶粒混凝土', '保温砂浆', '加气砖', '干混砂浆']

// 表单
const keyword = ref('')
const style = ref('科普风')
const generating = ref(false)

// 预览
const previewArticle = ref<any>(null)

// 列表
const articles = ref<any[]>([])
const tableLoading = ref(false)
const filterStatus = ref('')
const pagination = ref({
  current: 1,
  pageSize: 10,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 篇文章`,
  total: 0,
})

// 编辑
const editModalVisible = ref(false)
const editingArticle = ref<any>(null)
const saving = ref(false)
const editForm = ref({ title: '', content: '', style: '科普风' })

const columns = [
  { title: '文章标题', key: 'title', width: 300 },
  { title: '风格', key: 'style', width: 80 },
  { title: '状态', key: 'status', width: 80 },
  { title: '浏览量', key: 'views', width: 80 },
  { title: '发布时间', key: 'published_at', width: 160 },
  { title: '操作', key: 'actions', width: 200 },
]

async function handleGenerate() {
  if (!keyword.value.trim()) {
    Modal.warning({ title: '提示', content: '请输入主题关键词' })
    return
  }
  generating.value = true
  try {
    const res = await api.post(`${basePath}/generate`, { keyword: keyword.value.trim(), style: style.value })
    const data = res.data as any
    previewArticle.value = data
    message.success('文章生成成功')
    await fetchArticles()
  } catch (e: any) {
    if (e.response?.status === 409) {
      Modal.warning({ title: '提示', content: e.response.data?.message || '该关键词的文章已存在' })
    } else {
      Modal.error({ title: '生成失败', content: e.message || '请稍后重试' })
    }
  } finally {
    generating.value = false
  }
}

async function fetchArticles(page = 1) {
  tableLoading.value = true
  pagination.value.current = page
  try {
    const params: Record<string, any> = { page, page_size: pagination.value.pageSize }
    if (filterStatus.value) params.status = filterStatus.value
    const res = await api.get(`${basePath}/articles`, { params })
    const data = res.data as any
    articles.value = data.items || []
    pagination.value.total = data.total || 0
  } catch (e) {
    console.error('Failed to fetch articles:', e)
  } finally {
    tableLoading.value = false
  }
}

function onPageChange(p: { current: number; pageSize: number }) {
  pagination.value.pageSize = p.pageSize
  void fetchArticles(p.current)
}

function handlePreview(record: any) {
  previewArticle.value = record
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function handleEdit(record: any) {
  editingArticle.value = record
  editForm.value = {
    title: record.title || '',
    content: record.content || '',
    style: record.style || '科普风',
  }
  editModalVisible.value = true
}

async function handleSaveEdit() {
  if (!editForm.value.title.trim()) {
    Modal.warning({ title: '提示', content: '请输入文章标题' })
    return
  }
  if (!editForm.value.content.trim()) {
    Modal.warning({ title: '提示', content: '请输入文章正文' })
    return
  }
  saving.value = true
  try {
    await api.put(`${basePath}/articles/${editingArticle.value.id}`, {
      title: editForm.value.title,
      content: editForm.value.content,
      style: editForm.value.style,
    })
    message.success('保存成功')
    editModalVisible.value = false
    // 刷新预览和列表
    if (previewArticle.value?.id === editingArticle.value.id) {
      previewArticle.value = { ...previewArticle.value, ...editForm.value }
    }
    await fetchArticles()
  } catch (e: any) {
    Modal.error({ title: '保存失败', content: e.message })
  } finally {
    saving.value = false
  }
}

async function handlePublish(id: string) {
  ydConfirm({
    title: '确认发布',
    content: '确定要将该文章发布到网站吗？',
    onOk() {
      return (async () => {
        try {
          const res = await api.post(`${basePath}/publish/${id}`)
          const data = res.data as any
          message.success('发布成功')
          if (previewArticle.value?.id === id) {
            previewArticle.value = data
          }
          await fetchArticles()
        } catch (e: any) {
          Modal.error({ title: '发布失败', content: e.message })
        }
      })()
    },
  })
}

async function handleUnpublish(id: string) {
  ydConfirm({
    title: '确认下架',
    content: '确定要将该文章下架吗？',
    onOk() {
      return (async () => {
        try {
          await api.post(`${basePath}/unpublish/${id}`)
          message.success('已下架')
          if (previewArticle.value?.id === id) {
            previewArticle.value.status = 'draft'
            previewArticle.value.published_at = null
          }
          await fetchArticles()
        } catch (e: any) {
          Modal.error({ title: '操作失败', content: e.message })
        }
      })()
    },
  })
}

async function handleDelete(id: string) {
  ydConfirm({
    title: '确认删除',
    content: '确定要删除该文章吗？此操作不可恢复。',
    okType: 'danger',
    onOk() {
      return (async () => {
        try {
          await api.delete(`${basePath}/articles/${id}`)
          message.success('已删除')
          if (previewArticle.value?.id === id) {
            previewArticle.value = null
          }
          await fetchArticles()
        } catch (e: any) {
          Modal.error({ title: '删除失败', content: e.message })
        }
      })()
    },
  })
}

onMounted(() => {
  fetchArticles()
})
</script>

<style scoped>
.article-content {
  font-size: 0.95rem;
  line-height: 1.8;
}
.article-content :deep(p) {
  margin-bottom: 1rem;
}
</style>
