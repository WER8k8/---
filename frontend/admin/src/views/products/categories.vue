<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">
          分类管理
        </h1>
        <p class="text-gray-500 mt-1">
          管理产品分类结构
        </p>
      </div>
      <a-button
        type="primary"
        @click="showAddModal = true"
      >
        <PlusOutlined class="w-4 h-4 mr-2" />
        添加分类
      </a-button>
    </div>

    <a-card>
      <a-tree
        v-model:expanded-keys="expandedKeys"
        :tree-data="treeData"
        :field-names="fieldNames"
      >
        <template #title="{ title, data }">
          <span class="flex items-center justify-between w-full">
            <span>{{ title }}</span>
            <span class="flex items-center space-x-2">
              <a-button
                type="text"
                size="small"
                @click.stop="handleEdit(data.id)"
              >
                <EditOutlined />
              </a-button>
              <a-button
                type="text"
                size="small"
                danger
                @click.stop="handleDelete(data.id)"
              >
                <DeleteOutlined />
              </a-button>
            </span>
          </span>
        </template>
      </a-tree>
    </a-card>

    <a-modal
      v-model:open="showAddModal"
      :title="editingCategory ? '编辑分类' : '添加分类'"
      @ok="handleSaveCategory"
      @cancel="showAddModal = false"
    >
      <a-form
        :model="categoryForm"
        layout="vertical"
      >
        <a-form-item
          label="分类名称"
          :required="true"
        >
          <a-input
            v-model="categoryForm.name"
            placeholder="请输入分类名称"
          />
        </a-form-item>
        <a-form-item label="上级分类">
          <a-select
            v-model="categoryForm.parent_id"
            placeholder="请选择上级分类（可选）"
          >
            <a-select-option value="">
              无（顶级分类）
            </a-select-option>
            <a-select-option
              v-for="cat in parentOptions"
              :key="cat.id"
              :value="cat.id"
            >
              {{ cat.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons-vue'
import {
  Card as ACard,
  Tree as ATree,
  Button as AButton,
  Modal as AModal,
  Form as AForm,
  FormItem as AFormItem,
  Input as AInput,
  Select as ASelect,
  SelectOption as ASelectOption,
} from 'ant-design-vue'
import { productsAPI } from '@/api'

const categories = ref<any[]>([])
const expandedKeys = ref<string[]>([])
const showAddModal = ref(false)
const editingCategory = ref<any>(null)

const categoryForm = ref({
  name: '',
  parent_id: '',
})

const fieldNames = {
  title: 'name',
  key: 'id',
  children: 'children',
}

const parentOptions = computed(() => {
  const flatList: any[] = []
  const traverse = (items: any[], prefix = '') => {
    items.forEach((item) => {
      if (!editingCategory.value || item.id !== editingCategory.value.id) {
        flatList.push({
          id: item.id,
          name: prefix + item.name,
        })
      }
      if (item.children && item.children.length) {
        traverse(item.children, prefix + '└─ ')
      }
    })
  }
  traverse(categories.value)
  return flatList
})

const treeData = computed(() => {
  const map = new Map<string, any>()
  const roots: any[] = []

  categories.value.forEach((cat) => {
    map.set(cat.id, { ...cat, children: [] })
  })

  map.forEach((cat) => {
    if (cat.parent_id && map.has(cat.parent_id)) {
      map.get(cat.parent_id).children.push(cat)
    } else {
      roots.push(cat)
    }
  })

  return roots
})

async function fetchCategories() {
  try {
    const res = await productsAPI.categories()
    categories.value = res.data || []
  } catch (e) {
    console.error('Failed to fetch categories:', e)
  }
}

function handleEdit(id: string) {
  const cat = categories.value.find((c) => c.id === id)
  if (cat) {
    editingCategory.value = cat
    categoryForm.value = {
      name: cat.name,
      parent_id: cat.parent_id || '',
    }
    showAddModal.value = true
  }
}

async function handleDelete(id: string) {
  AModal.confirm({
    title: '确认删除',
    content: '确定要删除该分类吗？此操作会影响关联的产品。',
    okType: 'danger',
    async onOk() {
      try {
        await productsAPI.deleteCategory(id)
        await fetchCategories()
        AModal.success({ title: '删除成功' })
      } catch (e: any) {
        AModal.error({ title: '删除失败', content: e.message })
      }
    },
  })
}

async function handleSaveCategory() {
  if (!categoryForm.value.name) {
    AModal.warning({ title: '提示', content: '请输入分类名称' })
    return
  }

  try {
    const data = {
      name: categoryForm.value.name,
      parent_id: categoryForm.value.parent_id || null,
    }

    if (editingCategory.value) {
      await productsAPI.updateCategory(editingCategory.value.id, data)
      AModal.success({ title: '修改成功' })
    } else {
      await productsAPI.createCategory(data)
      AModal.success({ title: '创建成功' })
    }

    showAddModal.value = false
    editingCategory.value = null
    categoryForm.value = { name: '', parent_id: '' }
    await fetchCategories()
  } catch (e: any) {
    AModal.error({ title: '操作失败', content: e.message })
  }
}

onMounted(() => {
  fetchCategories()
})
</script>