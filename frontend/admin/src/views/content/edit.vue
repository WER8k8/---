<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">
          {{ isEdit ? '编辑内容' : '添加内容' }}
        </h1>
        <p class="text-gray-500 mt-1">
          {{ isEdit ? '修改页面内容' : '创建新的页面' }}
        </p>
      </div>
      <div class="flex items-center space-x-3">
        <router-link
          to="/content"
          class="px-4 py-2.5 border border-gray-200 text-gray-600 rounded-xl hover:bg-gray-50 text-sm font-medium transition-colors"
        >
          返回列表
        </router-link>
      </div>
    </div>

    <a-card>
      <a-form
        :model="form"
        layout="vertical"
      >
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item
              label="页面标题"
              :required="true"
            >
              <a-input
                v-model="form.title"
                placeholder="请输入页面标题"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item
              label="页面类型"
              :required="true"
            >
              <a-select
                v-model="form.page_type"
                placeholder="请选择页面类型"
              >
                <a-select-option value="about">
                  关于我们
                </a-select-option>
                <a-select-option value="news">
                  新闻资讯
                </a-select-option>
                <a-select-option value="contact">
                  联系我们
                </a-select-option>
                <a-select-option value="custom">
                  自定义页面
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="SEO标题">
          <a-input
            v-model="form.meta_title"
            placeholder="请输入SEO标题（建议不超过60字符）"
          />
        </a-form-item>
        <a-form-item label="SEO描述">
          <a-textarea
            v-model="form.meta_description"
            :rows="2"
            placeholder="请输入SEO描述（建议不超过160字符）"
          />
        </a-form-item>
        <a-form-item label="页面内容">
          <a-textarea
            v-model="form.content"
            :rows="10"
            placeholder="请输入页面内容（支持HTML）"
          />
        </a-form-item>
        <a-form-item>
          <a-checkbox v-model="form.is_published">
            发布页面
          </a-checkbox>
        </a-form-item>
        <a-form-item>
          <a-button
            type="primary"
            :loading="loading"
            @click="handleSubmit"
          >
            {{ isEdit ? '保存修改' : '创建页面' }}
          </a-button>
          <a-button
            class="ml-4"
            @click="handleReset"
          >
            重置
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Card as ACard,
  Form as AForm,
  FormItem as AFormItem,
  Input as AInput,
  Select as ASelect,
  SelectOption as ASelectOption,
  Textarea as ATextarea,
  Checkbox as ACheckbox,
  Button as AButton,
  Modal,
  Row as ARow,
  Col as ACol,
} from 'ant-design-vue'
import { contentAPI } from '@/api'

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => route.params.id !== 'new')
const loading = ref(false)

const form = ref({
  title: '',
  page_type: '',
  content: '',
  meta_title: '',
  meta_description: '',
  is_published: false,
})

async function fetchContent(id: string) {
  try {
    const res = await contentAPI.get(id)
    const data = res.data
    form.value = {
      title: data.title || '',
      page_type: data.page_type || '',
      content: data.content || '',
      meta_title: data.meta_title || '',
      meta_description: data.meta_description || '',
      is_published: data.is_published || false,
    }
  } catch (e) {
    console.error('Failed to fetch content:', e)
  }
}

async function handleSubmit() {
  if (!form.value.title || !form.value.page_type) {
    Modal.warning({ title: '提示', content: '请填写必填字段' })
    return
  }

  loading.value = true
  try {
    const data = {
      ...form.value,
      slug: form.value.title.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, ''),
    }

    if (isEdit.value) {
      await contentAPI.update(route.params.id as string, data)
      Modal.success({ title: '修改成功', content: '页面内容已更新' })
    } else {
      await contentAPI.create(data)
      Modal.success({ title: '创建成功', content: '页面已创建' })
    }

    router.push('/content')
  } catch (e: any) {
    Modal.error({ title: '操作失败', content: e.message })
  } finally {
    loading.value = false
  }
}

function handleReset() {
  form.value = {
    title: '',
    page_type: '',
    content: '',
    meta_title: '',
    meta_description: '',
    is_published: false,
  }
}

onMounted(async () => {
  if (isEdit.value) {
    await fetchContent(route.params.id as string)
  }
})
</script>