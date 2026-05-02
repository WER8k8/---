<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">
          {{ isEdit ? '编辑产品' : '添加产品' }}
        </h1>
        <p class="text-gray-500 mt-1">
          {{ isEdit ? '修改产品信息' : '创建新的产品' }}
        </p>
      </div>
      <div class="flex items-center space-x-3">
        <router-link
          to="/products"
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
              label="产品名称"
              :required="true"
            >
              <a-input
                v-model="form.name"
                placeholder="请输入产品名称"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item
              label="分类"
              :required="true"
            >
              <a-select
                v-model="form.category_id"
                placeholder="请选择分类"
              >
                <a-select-option
                  v-for="cat in categories"
                  :key="cat.id"
                  :value="cat.id"
                >
                  {{ cat.name }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="干密度 (kg/m³)">
              <a-input-number
                v-model="form.density"
                :min="800"
                :max="1950"
                placeholder="干密度"
              />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="强度等级">
              <a-select
                v-model="form.strength_grade"
                placeholder="请选择强度等级"
              >
                <a-select-option value="LC5.0">
                  LC5.0
                </a-select-option>
                <a-select-option value="LC7.5">
                  LC7.5
                </a-select-option>
                <a-select-option value="LC10">
                  LC10
                </a-select-option>
                <a-select-option value="LC15">
                  LC15
                </a-select-option>
                <a-select-option value="LC20">
                  LC20
                </a-select-option>
                <a-select-option value="LC25">
                  LC25
                </a-select-option>
                <a-select-option value="LC30">
                  LC30
                </a-select-option>
                <a-select-option value="LC35">
                  LC35
                </a-select-option>
                <a-select-option value="LC40">
                  LC40
                </a-select-option>
                <a-select-option value="LC45">
                  LC45
                </a-select-option>
                <a-select-option value="LC50">
                  LC50
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="导热系数 (W/m·K)">
              <a-input-number
                v-model="form.thermal_conductivity"
                :min="0.18"
                :max="0.28"
                :step="0.01"
                placeholder="导热系数"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="防火等级">
              <a-select
                v-model="form.fire_rating"
                placeholder="请选择防火等级"
              >
                <a-select-option value="A级">
                  A级
                </a-select-option>
                <a-select-option value="B1级">
                  B1级
                </a-select-option>
                <a-select-option value="B2级">
                  B2级
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="16">
            <a-form-item label="SEO标题">
              <div class="flex items-end space-x-2">
                <a-input 
                  v-model="form.meta_title" 
                  placeholder="请输入SEO标题（建议不超过60字符）"
                  class="flex-1"
                />
                <a-button 
                  type="default" 
                  size="small"
                  :loading="aiLoading"
                  @click="handleAIGenerate('seo_title')"
                >
                  <PlayCircleOutlined /> AI生成
                </a-button>
              </div>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="产品描述">
          <div class="flex items-end space-x-2">
            <a-textarea 
              v-model="form.description" 
              :rows="4" 
              placeholder="请输入产品描述"
              class="flex-1"
            />
            <div class="flex flex-col space-y-2">
              <a-button 
                type="default" 
                size="small"
                :loading="aiLoading"
                @click="handleAIGenerate('description')"
              >
                <PlayCircleOutlined /> AI生成
              </a-button>
              <a-button 
                type="default" 
                size="small"
                :loading="aiLoading"
                @click="handleAIPolish('description')"
              >
                <RestOutlined /> AI润色
              </a-button>
            </div>
          </div>
        </a-form-item>
        <a-form-item label="SEO描述">
          <div class="flex items-end space-x-2">
            <a-textarea 
              v-model="form.meta_description" 
              :rows="2" 
              placeholder="请输入SEO描述（建议不超过160字符）"
              class="flex-1"
            />
            <div class="flex flex-col space-y-2">
              <a-button 
                type="default" 
                size="small"
                :loading="aiLoading"
                @click="handleAIGenerate('seo_description')"
              >
                <PlayCircleOutlined /> AI生成
              </a-button>
              <a-button 
                type="default" 
                size="small"
                :loading="aiLoading"
                @click="handleAIPolish('seo_description')"
              >
                <RestOutlined /> AI润色
              </a-button>
            </div>
          </div>
        </a-form-item>
        <a-form-item>
          <a-checkbox v-model="form.is_active">
            上架产品
          </a-checkbox>
        </a-form-item>
        <a-form-item>
          <a-button
            type="primary"
            :loading="loading"
            @click="handleSubmit"
          >
            {{ isEdit ? '保存修改' : '创建产品' }}
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
  InputNumber as AInputNumber,
  Select as ASelect,
  SelectOption as ASelectOption,
  Textarea as ATextarea,
  Checkbox as ACheckbox,
  Button as AButton,
  Modal,
  Row as ARow,
  Col as ACol,
} from 'ant-design-vue'
import { PlayCircleOutlined, RestOutlined } from '@ant-design/icons-vue'
import { productsAPI, contentAPI } from '@/api'

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => route.params.id !== 'new')
const loading = ref(false)
const aiLoading = ref(false)

const form = ref({
  name: '',
  category_id: '',
  density: null,
  strength_grade: '',
  thermal_conductivity: null,
  fire_rating: '',
  description: '',
  meta_title: '',
  meta_description: '',
  is_active: false,
})

const categories = ref<any[]>([])

async function fetchCategories() {
  try {
    const res = await productsAPI.categories()
    categories.value = res.data
  } catch (e) {
    console.error('Failed to fetch categories:', e)
  }
}

async function fetchProduct(id: string) {
  try {
    const res = await productsAPI.get(id)
    const data = res.data
    form.value = {
      name: data.name || '',
      category_id: data.category_id || '',
      density: data.density || null,
      strength_grade: data.strength_grade || '',
      thermal_conductivity: data.thermal_conductivity || null,
      fire_rating: data.fire_rating || '',
      description: data.description || '',
      meta_title: data.meta_title || '',
      meta_description: data.meta_description || '',
      is_active: data.is_active || false,
    }
  } catch (e) {
    console.error('Failed to fetch product:', e)
  }
}

async function handleSubmit() {
  if (!form.value.name || !form.value.category_id) {
    Modal.warning({ title: '提示', content: '请填写必填字段' })
    return
  }

  loading.value = true
  try {
    const data = {
      ...form.value,
      slug: form.value.name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, ''),
    }

    if (isEdit.value) {
      await productsAPI.update(route.params.id as string, data)
      Modal.success({ title: '修改成功', content: '产品信息已更新' })
    } else {
      await productsAPI.create(data)
      Modal.success({ title: '创建成功', content: '产品已创建' })
    }

    router.push('/products')
  } catch (e: any) {
    Modal.error({ title: '操作失败', content: e.message })
  } finally {
    loading.value = false
  }
}

function handleReset() {
  form.value = {
    name: '',
    category_id: '',
    density: null,
    strength_grade: '',
    thermal_conductivity: null,
    fire_rating: '',
    description: '',
    meta_title: '',
    meta_description: '',
    is_active: false,
  }
}

async function handleAIGenerate(field: string) {
  aiLoading.value = true
  try {
    // 根据字段确定生成类型
    let content_type = 'product'
    if (field === 'seo_title') {
      content_type = 'seo_title'
    } else if (field === 'seo_description') {
      content_type = 'seo_description'
    }
    
    // 获取分类名称
    const category = categories.value.find(cat => cat.id === form.value.category_id)
    const category_name = category ? category.name : ''
    
    // 构建请求参数，传递完整产品信息
    const params = {
      content_type,
      keywords: [form.value.name || '轻集料混凝土', form.value.strength_grade || 'LC15'],
      product_name: form.value.name,
      category_name,
      density: form.value.density,
      strength_grade: form.value.strength_grade,
      thermal_conductivity: form.value.thermal_conductivity,
      fire_rating: form.value.fire_rating,
      existing_description: field === 'seo_description' ? form.value.description : '',
    }
    
    const res = await contentAPI.aiGenerate(params)
    
    // 根据字段更新对应表单值
    if (field === 'description') {
      form.value.description = res.data.content
    } else if (field === 'seo_title') {
      form.value.meta_title = res.data.content
    } else if (field === 'seo_description') {
      form.value.meta_description = res.data.content
    }
    
    // 如果生成了产品描述，自动生成SEO标题和描述（联动）
    if (field === 'description' && !form.value.meta_title) {
      setTimeout(() => {
        handleAIGenerate('seo_title')
      }, 500)
    }
    
    if (res.data.mock) {
      Modal.info({ title: '提示', content: 'AI引擎未配置，当前为模拟模式' })
    }
  } catch (e: any) {
    Modal.error({ title: '生成失败', content: e.message })
  } finally {
    aiLoading.value = false
  }
}

async function handleAIPolish(field: string) {
  aiLoading.value = true
  try {
    const content = field === 'description' ? form.value.description : form.value.meta_description
    
    if (!content.trim()) {
      Modal.warning({ title: '提示', content: '请先输入内容再进行润色' })
      aiLoading.value = false
      return
    }
    
    const res = await contentAPI.aiPolish({
      content,
      polish_type: 'general',
    })
    
    if (field === 'description') {
      form.value.description = res.data.content
    } else if (field === 'seo_description') {
      form.value.meta_description = res.data.content
    }
    
    if (res.data.mock) {
      Modal.info({ title: '提示', content: 'AI引擎未配置，当前为模拟模式' })
    }
  } catch (e: any) {
    Modal.error({ title: '润色失败', content: e.message })
  } finally {
    aiLoading.value = false
  }
}

onMounted(async () => {
  await fetchCategories()
  if (isEdit.value) {
    await fetchProduct(route.params.id as string)
  }
})
</script>