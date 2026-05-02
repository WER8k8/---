<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">
          自定义拖拽模块
        </h1>
        <p class="text-gray-500 mt-1">
          配置可拖拽的页面模块
        </p>
      </div>
    </div>

    <a-card
      title="拖拽模块列表"
      class="mb-6"
    >
      <div class="flex gap-4 mb-4">
        <a-button
          type="primary"
          @click="showAddModal = true"
        >
          <PlusOutlined class="w-4 h-4 mr-2" />
          添加模块
        </a-button>
      </div>
      
      <div class="bg-gray-50 rounded-xl p-6 min-h-64">
        <div class="flex flex-wrap gap-4">
          <div
            v-for="(module, index) in modules"
            :key="module.id"
            class="w-40 h-40 bg-white border-2 border-dashed border-gray-200 rounded-xl flex flex-col items-center justify-center cursor-move hover:border-primary-300 hover:bg-primary-50 transition-all group relative"
            draggable="true"
            @dragstart="handleDragStart($event, index)"
            @dragover.prevent
            @drop="handleDrop($event, index)"
          >
            <div class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
              <button
                class="p-1 bg-white rounded shadow hover:bg-gray-100"
                @click.stop="editModule(module)"
              >
                <EditOutlined class="w-3 h-3 text-gray-600" />
              </button>
              <button
                class="p-1 bg-white rounded shadow hover:bg-red-50"
                @click.stop="deleteModule(module.id)"
              >
                <DeleteOutlined class="w-3 h-3 text-red-500" />
              </button>
            </div>
            <component
              :is="getModuleIcon(module.icon)"
              class="w-8 h-8 text-gray-400 mb-2"
            />
            <span class="text-sm text-gray-600">{{ module.name }}</span>
          </div>
        </div>
        
        <div
          v-if="modules.length === 0"
          class="text-center py-12"
        >
          <MouseOutlined class="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p class="text-gray-400">
            暂无拖拽模块，点击上方按钮添加
          </p>
        </div>
      </div>
    </a-card>

    <a-card title="拖拽区域设置">
      <a-form
        :model="dragSettings"
        layout="vertical"
      >
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="启用拖拽">
              <a-switch v-model="dragSettings.enabled" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="动画效果">
              <a-select v-model="dragSettings.animation">
                <a-select-option value="none">
                  无
                </a-select-option>
                <a-select-option value="fade">
                  淡入淡出
                </a-select-option>
                <a-select-option value="slide">
                  滑动
                </a-select-option>
                <a-select-option value="scale">
                  缩放
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="拖拽延迟 (ms)">
              <a-input-number
                v-model="dragSettings.delay"
                :min="0"
                :max="1000"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="吸附距离 (px)">
              <a-input-number
                v-model="dragSettings.snapDistance"
                :min="0"
                :max="50"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item>
          <a-button
            type="primary"
            @click="saveSettings"
          >
            保存设置
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <a-modal
      v-model:open="showAddModal"
      :title="editingModule ? '编辑模块' : '添加模块'"
      @ok="saveModule"
      @cancel="showAddModal = false"
    >
      <a-form
        :model="moduleForm"
        layout="vertical"
      >
        <a-form-item
          label="模块名称"
          :required="true"
        >
          <a-input
            v-model="moduleForm.name"
            placeholder="请输入模块名称"
          />
        </a-form-item>
        <a-form-item label="模块图标">
          <a-select v-model="moduleForm.icon">
            <a-select-option
              v-for="icon in availableIcons"
              :key="icon"
              :value="icon"
            >
              <component
                :is="getModuleIcon(icon)"
                class="w-4 h-4 mr-2"
              />
              {{ icon }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="模块描述">
          <a-textarea
            v-model="moduleForm.description"
            placeholder="请输入模块描述"
            :rows="3"
          />
        </a-form-item>
        <a-form-item label="模块类型">
          <a-select v-model="moduleForm.type">
            <a-select-option value="widget">
              小部件
            </a-select-option>
            <a-select-option value="section">
              区块
            </a-select-option>
            <a-select-option value="panel">
              面板
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  LayoutOutlined,
  BarChartOutlined,
  FileTextOutlined,
  PictureOutlined,
  LinkOutlined,
} from '@ant-design/icons-vue'
import {
  Card as ACard,
  Button as AButton,
  Form as AForm,
  FormItem as AFormItem,
  Input as AInput,
  Select as ASelect,
  SelectOption as ASelectOption,
  InputNumber as AInputNumber,
  Switch as ASwitch,
  Modal,
  Row as ARow,
  Col as ACol,
  Textarea as ATextarea,
} from 'ant-design-vue'

interface Module {
  id: string
  name: string
  icon: string
  description: string
  type: string
}

const modules = ref<Module[]>([])
const showAddModal = ref(false)
const editingModule = ref<Module | null>(null)
const moduleForm = ref({
  name: '',
  icon: 'WidgetOutlined',
  description: '',
  type: 'widget',
})

const dragSettings = ref({
  enabled: true,
  animation: 'fade',
  delay: 0,
  snapDistance: 10,
})

const availableIcons = [
  'LayoutOutlined',
  'BarChartOutlined',
  'FileTextOutlined',
  'PictureOutlined',
  'LinkOutlined',
]

const iconMap: Record<string, any> = {
  LayoutOutlined,
  BarChartOutlined,
  FileTextOutlined,
  PictureOutlined,
  LinkOutlined,
}

function getModuleIcon(iconName: string) {
  return iconMap[iconName] || LayoutOutlined
}

let draggedIndex = -1

function handleDragStart(event: DragEvent, index: number) {
  draggedIndex = index
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
  }
}

function handleDrop(_event: DragEvent, index: number) {
  if (draggedIndex !== -1 && draggedIndex !== index) {
    const dragged = modules.value.splice(draggedIndex, 1)[0]
    modules.value.splice(index, 0, dragged)
  }
  draggedIndex = -1
}

function editModule(module: Module) {
  editingModule.value = module
  moduleForm.value = {
    name: module.name,
    icon: module.icon,
    description: module.description,
    type: module.type,
  }
  showAddModal.value = true
}

async function deleteModule(id: string) {
  Modal.confirm({
    title: '确认删除',
    content: '确定要删除该模块吗？',
    async onOk() {
      modules.value = modules.value.filter(m => m.id !== id)
      Modal.success({ title: '删除成功' })
    },
  })
}

async function saveModule() {
  if (!moduleForm.value.name) {
    Modal.warning({ title: '提示', content: '请输入模块名称' })
    return
  }
  
  if (editingModule.value) {
    const index = modules.value.findIndex(m => m.id === editingModule.value!.id)
    if (index > -1) {
      modules.value[index] = {
        ...editingModule.value,
        ...moduleForm.value,
      }
    }
    Modal.success({ title: '修改成功' })
  } else {
    modules.value.push({
      id: Date.now().toString(),
      ...moduleForm.value,
    })
    Modal.success({ title: '创建成功' })
  }
  
  showAddModal.value = false
  editingModule.value = null
  moduleForm.value = {
    name: '',
    icon: 'WidgetOutlined',
    description: '',
    type: 'widget',
  }
}

function saveSettings() {
  Modal.success({ title: '保存成功', content: '拖拽设置已更新' })
}

onMounted(() => {
  modules.value = [
    { id: '1', name: '数据统计', icon: 'BarChartOutlined', description: '显示关键数据指标', type: 'widget' },
    { id: '2', name: '内容展示', icon: 'FileTextOutlined', description: '展示文章内容', type: 'section' },
    { id: '3', name: '图片画廊', icon: 'ImageOutlined', description: '展示产品图片', type: 'panel' },
    { id: '4', name: '链接导航', icon: 'LinkOutlined', description: '快速导航链接', type: 'widget' },
  ]
})
</script>
