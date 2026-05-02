<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-primary-900">
        {{ isNew ? '添加产品' : '编辑产品' }}
      </h1>
      <NuxtLink
        to="/admin/products"
        class="text-sm text-text-secondary hover:text-primary-900 transition-colors"
      >
        ← 返回产品列表
      </NuxtLink>
    </div>

    <div class="space-y-6">
      <div class="bg-surface rounded-xl border border-border p-6 space-y-6">
        <h3 class="text-lg font-semibold text-primary-900">
          基本信息
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-semibold text-primary-900 mb-2">产品名称</label>
            <input
              v-model="form.name"
              class="w-full bg-surface-elevated border border-border rounded-xl px-4 py-2.5 text-primary-900 placeholder:text-text-muted focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
              placeholder="如: 岩棉保温板"
              @input="autoGenerateSlug"
            >
          </div>
          <div>
            <label class="block text-sm font-semibold text-primary-900 mb-2">URL别名 (slug)</label>
            <div class="flex items-center space-x-2">
              <span class="text-sm text-text-muted">/</span>
              <input
                v-model="form.slug"
                class="flex-1 bg-surface-elevated border border-border rounded-xl px-4 py-2.5 text-primary-900 placeholder:text-text-muted focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
                placeholder="rock-wool-board"
              >
            </div>
          </div>
          <div>
            <label class="block text-sm font-semibold text-primary-900 mb-2">所属分类</label>
            <select
              v-model="form.category_id"
              class="w-full bg-surface-elevated border border-border rounded-xl px-4 py-2.5 text-primary-900 focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
            >
              <option value="">
                请选择分类
              </option>
              <option
                v-for="cat in categories"
                :key="cat.id"
                :value="cat.id"
              >
                {{ cat.name }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-semibold text-primary-900 mb-2">副标题</label>
            <input
              v-model="form.subtitle"
              class="w-full bg-surface-elevated border border-border rounded-xl px-4 py-2.5 text-primary-900 placeholder:text-text-muted focus:outline-none focus:border-secondary-500 focus:ring-2 focus:ring-secondary-500/20 transition-all"
              placeholder="简短的产品描述"
            >
          </div>
        </div>

        <div>
          <label class="block text-sm font-semibold text-primary-900 mb-2">产品描述</label>
          <RichTextEditor
            v-model="form.description"
            placeholder="详细描述产品特性和优势..."
          />
        </div>

        <div>
          <label class="block text-sm font-semibold text-primary-900 mb-2">产品封面图</label>
          <div class="flex items-center space-x-4">
            <img
              v-if="form.image_url"
              :src="form.image_url"
              class="w-24 h-24 object-cover rounded-xl border border-border"
              @error="form.image_url = ''"
            >
            <div class="flex-1">
              <FileUploader
                accept="image/*"
                :show-doc-type="false"
                api-endpoint="/api/v1/system/upload"
                @uploaded="onImageUploaded"
              />
            </div>
          </div>
        </div>
      </div>

      <div class="bg-surface rounded-xl border border-border p-6">
        <ProductParamForm v-model="params.value" />
      </div>

      <div class="bg-surface rounded-xl border border-border p-6">
        <h3 class="text-lg font-semibold text-primary-900 mb-4">
          应用场景
        </h3>
        <RichTextEditor
          v-model="form.application_scenarios"
          placeholder="描述产品的典型应用场景..."
        />
      </div>

      <div class="bg-surface rounded-xl border border-border p-6">
        <h3 class="text-lg font-semibold text-primary-900 mb-4">
          产品优势
        </h3>
        <RichTextEditor
          v-model="form.advantages"
          placeholder="列举产品的核心优势..."
        />
      </div>

      <div class="bg-surface rounded-xl border border-border p-6">
        <h3 class="text-lg font-semibold text-primary-900 mb-4">
          资料下载
        </h3>
        <div class="mb-4">
          <FileUploader
            accept=".pdf,.dwg,.dxf,.jpg,.png"
            :show-doc-type="true"
            :api-endpoint="`/api/v1/products/${productId}/documents`"
            @uploaded="onDocumentUploaded"
          />
        </div>
        <div
          v-if="documents.length"
          class="space-y-2"
        >
          <div
            v-for="doc in documents"
            :key="doc.id"
            class="flex items-center justify-between bg-surface-elevated rounded-xl px-4 py-3"
          >
            <div class="flex items-center space-x-3">
              <span class="text-lg">{{ docTypeIcon(doc.doc_type) }}</span>
              <div>
                <p class="text-sm font-medium text-primary-900">
                  {{ doc.file_name }}
                </p>
                <p class="text-xs text-text-muted">
                  {{ docTypeLabel(doc.doc_type) }} · {{ (doc.file_size / 1024 / 1024).toFixed(1) }} MB
                </p>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <a
                :href="doc.file_path"
                target="_blank"
                class="text-sm text-secondary hover:text-secondary/80 font-medium"
              >下载</a>
              <button
                class="text-sm text-danger hover:text-danger/80 font-medium"
                @click="handleDeleteDocument(doc.id)"
              >
                删除
              </button>
            </div>
          </div>
        </div>
        <div
          v-else
          class="text-center py-6 text-text-muted text-sm"
        >
          暂无附件，请上传产品规格书、检测报告等文件
        </div>
      </div>

      <div class="bg-surface rounded-xl border border-border p-6">
        <SeoPanel
          v-model="seo.value"
          :slug="form.slug"
        />
      </div>

      <div
        v-if="saveError"
        class="bg-danger/10 border border-danger/20 text-danger px-4 py-3 rounded-xl text-sm"
      >
        {{ saveError }}
      </div>

      <div class="flex items-center justify-between pt-4">
        <button
          v-if="!isNew"
          class="px-4 py-2.5 text-danger border border-danger/20 rounded-xl hover:bg-danger/10 text-sm font-medium transition-colors"
          @click="handleDeleteProduct"
        >
          删除此产品
        </button>
        <div class="flex items-center space-x-3 ml-auto">
          <button
            :disabled="saving"
            class="px-6 py-2.5 bg-surface-elevated text-text-secondary rounded-xl hover:bg-surface-hover disabled:opacity-50 text-sm font-medium transition-colors"
            @click="handleSave(false)"
          >
            {{ saving ? '保存中...' : '保存草稿' }}
          </button>
          <button
            :disabled="saving"
            class="px-6 py-2.5 bg-gradient-to-r from-secondary-500 to-secondary-600 text-white rounded-xl hover:from-secondary-600 hover:to-secondary-700 disabled:opacity-50 text-sm font-medium transition-all shadow-lg shadow-secondary-200"
            @click="handleSave(true)"
          >
            {{ saving ? '发布中...' : '发布' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, navigateTo } from '#app'
import RichTextEditor from '~/components/admin/RichTextEditor.vue'
import ProductParamForm from '~/components/admin/ProductParamForm.vue'
import FileUploader from '~/components/admin/FileUploader.vue'
import SeoPanel from '~/components/admin/SeoPanel.vue'
import type { SeoData } from '~/components/admin/SeoPanel.vue'

definePageMeta({ layout: 'admin' })

const route = useRoute()
const isNew = computed(() => !route.params.id || route.params.id === 'new')
const productId = computed(() => route.params.id as string)
const saving = ref(false)
const saveError = ref<string | null>(null)
const categories = ref<Array<{ id: string; name: string; parent_id: string | null }>>([])
const documents = ref<Array<{ id: string; doc_type: string; file_name: string; file_path: string; file_size: number }>>([])

const form = reactive({
  name: '',
  slug: '',
  category_id: '',
  subtitle: '',
  description: '',
  application_scenarios: '',
  advantages: '',
  image_url: '',
})

const params = ref({
  density: '',
  strength: '',
  thermal_conductivity: '',
  unit_weight: '',
  fire_rating: '',
  specifications_text: '',
  specifications: {} as Record<string, string>,
})

const seo = ref<SeoData>({
  meta_title: '',
  meta_description: '',
  meta_keywords: '',
  canonical_url: '',
  og_title: '',
  og_description: '',
  og_image: '',
  h1_tag: '',
  noindex: false,
})

function autoGenerateSlug() {
  if (form.slug || !form.name) return
  form.slug = form.name
    .replace(/[^\w\u4e00-\u9fff]/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
    .toLowerCase()
}

function docTypeIcon(type: string) {
  const icons: Record<string, string> = { pdf: '📕', cad: '📐', report: '📊', certificate: '📜', other: '📄' }
  return icons[type] || '📄'
}

function docTypeLabel(type: string) {
  const labels: Record<string, string> = { pdf: '规格书', cad: 'CAD图纸', report: '检测报告', certificate: '资质证书', other: '其他' }
  return labels[type] || type
}

function onImageUploaded(result: { url: string }) {
  form.image_url = result.url
}

function onDocumentUploaded(result: { url: string; filename: string; docType: string }) {
  fetchDocuments()
}

async function fetchCategories() {
  try {
    const token = localStorage.getItem('admin_token')
    const res = await fetch('/api/v1/products/categories', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) {
      categories.value = await res.json()
    }
  } catch {}
}

async function fetchDocuments() {
  if (isNew.value) return
  try {
    const token = localStorage.getItem('admin_token')
    const res = await fetch(`/api/v1/products/${productId.value}/documents`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) {
      documents.value = await res.json()
    }
  } catch {}
}

async function handleDeleteDocument(docId: string) {
  if (!confirm('确定要删除此文件吗？')) return
  try {
    const token = localStorage.getItem('admin_token')
    const res = await fetch(`/api/v1/products/documents/${docId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) {
      await fetchDocuments()
    }
  } catch {}
}

async function handleDeleteProduct() {
  if (!confirm(`确定要删除产品 "${form.name}" 吗？此操作不可撤销。`)) return
  try {
    const token = localStorage.getItem('admin_token')
    const res = await fetch(`/api/v1/products/${productId.value}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) {
      await navigateTo('/admin/products')
    }
  } catch {}
}

async function handleSave(publish: boolean) {
  saving.value = true
  saveError.value = null
  try {
    const token = localStorage.getItem('admin_token')
    const body = {
      ...form,
      ...params.value,
      sort_order: 0,
      is_active: publish,
    }

    let id = productId.value

    if (isNew.value) {
      const res = await fetch('/api/v1/products', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || '保存失败')
      }
      const product = await res.json()
      id = product.id
    } else {
      const res = await fetch(`/api/v1/products/${id}`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...body, is_active: publish }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || '保存失败')
      }
    }

    await saveSeo(token, id)
    await navigateTo('/admin/products')
  } catch (e: any) {
    saveError.value = e.message
  } finally {
    saving.value = false
  }
}

async function saveSeo(token: string, resourceId: string) {
  const hasSeoFields = seo.value.meta_title || seo.value.meta_description || seo.value.meta_keywords
  if (!hasSeoFields) return

  try {
    const existingRes = await fetch(`/api/v1/content/seo/product/${resourceId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })

    const payload = {
      resource_type: 'product',
      resource_id: resourceId,
      meta_title: seo.value.meta_title,
      meta_description: seo.value.meta_description,
      meta_keywords: seo.value.meta_keywords,
      canonical_url: seo.value.canonical_url,
      og_title: seo.value.og_title,
      og_description: seo.value.og_description,
      og_image: seo.value.og_image,
      h1_tag: seo.value.h1_tag,
      noindex: seo.value.noindex,
    }

    if (existingRes.ok) {
      await fetch(`/api/v1/content/seo/product/${resourceId}`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
    } else {
      await fetch('/api/v1/content/seo', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
    }
  } catch {}
}

onMounted(async () => {
  await fetchCategories()

  if (!isNew.value) {
    try {
      const token = localStorage.getItem('admin_token')
      const res = await fetch(`/api/v1/products/${productId.value}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) {
        const data = await res.json()
        form.name = data.name || ''
        form.slug = data.slug || ''
        form.category_id = data.category_id || ''
        form.subtitle = data.subtitle || ''
        form.description = data.description || ''
        form.application_scenarios = data.application_scenarios || ''
        form.advantages = data.advantages || ''
        form.image_url = data.image_url || ''

        params.value.density = data.density || ''
        params.value.strength = data.strength || ''
        params.value.thermal_conductivity = data.thermal_conductivity || ''
        params.value.unit_weight = data.unit_weight || ''
        params.value.fire_rating = data.fire_rating || ''
        params.value.specifications_text = data.specifications_text || ''
        params.value.specifications = (typeof data.specifications === 'object' && data.specifications) ? data.specifications : {}

        try {
          const seoRes = await fetch(`/api/v1/content/seo/product/${productId.value}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          })
          if (seoRes.ok) {
            const seoData = await seoRes.json()
            seo.value.meta_title = seoData.meta_title || ''
            seo.value.meta_description = seoData.meta_description || ''
            seo.value.meta_keywords = seoData.meta_keywords || ''
            seo.value.canonical_url = seoData.canonical_url || ''
            seo.value.og_title = seoData.og_title || ''
            seo.value.og_description = seoData.og_description || ''
            seo.value.og_image = seoData.og_image || ''
            seo.value.h1_tag = seoData.h1_tag || ''
            seo.value.noindex = seoData.noindex || false
          }
        } catch {}
      }
    } catch (e: any) {
      saveError.value = '加载产品失败: ' + e.message
    }
    await fetchDocuments()
  }
})
</script>
