<template>
  <YdPage title="低代码平台" subtitle="可视化拖拽搭建应用界面" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="showEditor = true">进入编辑器</a-button>
    </template>
  <div class="space-y-6 animate-fade-in">
    <a-card title="组件拖拽区域">
      <div class="drag-zone">
        <div class="drag-left">
          <p class="text-sm font-semibold mb-3">可用组件</p>
          <div class="drag-items">
            <div v-for="c in components" :key="c.name" class="drag-item" @click="addComponent(c)">
              <YdNavIcon :name="c.iconKey" size="sm" />
              <span class="text-xs">{{ c.name }}</span>
            </div>
          </div>
        </div>
        <div class="drag-canvas">
          <p class="text-sm font-semibold mb-3">画布区域</p>
          <div class="canvas-area">
            <div v-if="selectedComponents.length === 0" class="canvas-placeholder">
              <YdIllustration icon="AppstoreOutlined" size="lg" />
              <p class="text-gray-400">从左侧拖拽组件到此处</p>
              <p class="text-xs text-gray-300">支持表单、表格、图表、搜索等组件</p>
            </div>
            <div v-for="(c, i) in selectedComponents" :key="i" class="canvas-item">
              <YdNavIcon :name="c.iconKey" size="sm" />
              <span class="text-sm">{{ c.name }}</span>
              <a-button size="small" type="link" danger @click="removeComponent(i)">移除</a-button>
            </div>
          </div>
        </div>
      </div>
    </a-card>
    <a-card title="模板市场">
      <p class="text-xs text-gray-400 mb-4">选择一个模板快速开始搭建</p>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <a-card v-for="t in templates" :key="t.id" hoverable size="small" @click="useTemplate(t)">
          <div class="text-center">
            <YdIllustration :icon="t.iconKey" size="md" class="mb-3" />
            <h3 class="font-semibold">{{ t.name }}</h3>
            <p class="text-xs text-gray-400 mt-1">{{ t.desc }}</p>
            <a-tag class="mt-2" size="small">{{ t.components }} 个组件</a-tag>
          </div>
        </a-card>
      </div>
    </a-card>
    <a-modal v-model:open="showEditor" title="低代码编辑器" width="900px" :footer="null">
      <div class="text-center py-12">
        <YdIllustration icon="ToolOutlined" size="lg" />
        <h3 class="text-xl font-bold mt-4">低代码编辑器正在加载中</h3>
        <p class="text-gray-400 mt-2">可视化拖拽引擎正在初始化...</p>
        <p class="text-xs text-gray-300 mt-1">您可以先在下方选择模板快速开始</p>
        <div class="mt-4">
          <a-tag v-for="c in selectedComponents" :key="c.name" class="mr-1 mb-1" closable @close="removeComponent(selectedComponents.indexOf(c))">
            {{ c.name }}
          </a-tag>
        </div>
        <a-button type="primary" class="mt-4" @click="showEditor = false">关闭</a-button>
      </div>
    </a-modal>
  </div>
  </YdPage>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { YdIllustration, YdNavIcon, YdPage } from '@/components/youding';
import { lowcodeIconForName } from '@/constants/iconCatalog';
import { getAuthToken } from '@/utils/api';

const showEditor = ref(false)

type PaletteItem = { iconKey: string; name: string }

const components: PaletteItem[] = [
  '输入框', '图表', '表格', '搜索', '轮播图', '列表',
  '导航栏', '联系方式', '日期选择', '按钮组', '标签页', '信息提示',
].map((name) => ({ name, iconKey: lowcodeIconForName(name) }))

const selectedComponents = ref<PaletteItem[]>([])

const templates = ref([
  { id: 1, name: '表单模板', iconKey: lowcodeIconForName('表单模板'), desc: '客户信息收集、询盘登记', components: 5 },
  { id: 2, name: '列表模板', iconKey: lowcodeIconForName('列表模板'), desc: '产品列表、订单管理', components: 8 },
  { id: 3, name: '详情模板', iconKey: lowcodeIconForName('详情模板'), desc: '产品详情、文章页面', components: 6 },
  { id: 4, name: '仪表盘模板', iconKey: lowcodeIconForName('仪表盘模板'), desc: '数据看板、统计图表', components: 12 },
])

function addComponent(c: PaletteItem) {
  if (!selectedComponents.value.find(sc => sc.name === c.name)) {
    selectedComponents.value.push(c)
    message.success(`已添加组件: ${c.name}`)
  } else {
    message.warning('该组件已在画布中')
  }
}

function removeComponent(i: number) {
  selectedComponents.value.splice(i, 1)
}

function useTemplate(t: { name: string; components: number }) {
  message.info(`已选择模板「${t.name}」，含 ${t.components} 个组件`)
  showEditor.value = true
}

onMounted(() => {
  if (!getAuthToken()) return
})
</script>

<style scoped>
.drag-zone { display: flex; gap: 16px; min-height: 280px; }
.drag-left { width: 200px; flex-shrink: 0; }
.drag-items { display: flex; flex-direction: column; gap: 8px; }
.drag-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
}
.drag-item:hover { border-color: var(--uj-brand, #4a9b8c); }
.drag-canvas { flex: 1; }
.canvas-area {
  min-height: 240px;
  border: 2px dashed #e2e8f0;
  border-radius: 12px;
  padding: 16px;
}
.canvas-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  text-align: center;
}
.canvas-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  margin-bottom: 8px;
  background: #f8fafc;
  border-radius: 8px;
}
</style>
