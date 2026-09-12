<template>
  <YdPage title="项目中心" subtitle="模板管理与项目创建" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="createOpen = true">新建项目</a-button>
    </template>
  <div class="proj-page">
    <a-card title="模板库" class="section-card">
      <div class="tpl-grid">
        <a-card v-for="t in templates" :key="t.id" class="tpl-card" hoverable>
          <div class="tpl-preview" :style="{ background: t.color }">
            <span class="tpl-preview-text">{{ t.name }}</span>
          </div>
          <div class="tpl-body">
            <h3 class="font-semibold text-gray-900">{{ t.name }}</h3>
            <p class="text-gray-500 text-sm">{{ t.desc }}</p>
            <div class="flex gap-1 flex-wrap mt-2">
              <a-tag v-for="tag in t.tags" :key="tag" size="small">{{ tag }}</a-tag>
            </div>
            <a-button class="mt-3 w-full" @click="previewTpl = t">预览</a-button>
          </div>
        </a-card>
      </div>
    </a-card>

    <a-card title="最近项目" class="section-card">
      <a-table :columns="pcols" :data-source="projects" row-key="id" size="small" :pagination="false">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status==='active'?'green':'default'">{{ record.status==='active'?'运行中':record.status }}</a-tag>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal :open="!!previewTpl" title="模板预览" width="640px" :footer="null" @update:open="(v: boolean) => { if (!v) previewTpl = null }">
      <template v-if="previewTpl">
        <div class="tpl-preview-lg" :style="{ background: previewTpl.color }" style="height:160px; border-radius:8px; margin-bottom:16px; display:flex; align-items:center; justify-content:center">
          <span style="color:#fff; font-size:24px; font-weight:600">{{ previewTpl.name }}</span>
        </div>
        <a-descriptions :column="1" size="small" bordered>
          <a-descriptions-item label="模板名称">{{ previewTpl.name }}</a-descriptions-item>
          <a-descriptions-item label="描述">{{ previewTpl.desc }}</a-descriptions-item>
          <a-descriptions-item label="功能特性">{{ previewTpl.features }}</a-descriptions-item>
          <a-descriptions-item label="技术栈">{{ previewTpl.tech }}</a-descriptions-item>
          <a-descriptions-item label="预估页面数">{{ previewTpl.pages }}</a-descriptions-item>
          <a-descriptions-item label="标签">{{ previewTpl.tags.join(' / ') }}</a-descriptions-item>
        </a-descriptions>
        <div class="text-right mt-4">
          <a-button type="primary" @click="useTemplate(previewTpl)">使用此模板</a-button>
        </div>
      </template>
    </a-modal>

    <a-modal v-model:open="createOpen" title="新建项目" @ok="createProject" ok-text="创建">
      <a-form layout="vertical">
        <a-form-item label="项目名称" required>
          <a-input v-model="form.name" placeholder="请输入项目名称" />
        </a-form-item>
        <a-form-item label="选择模板">
          <a-select v-model="form.template" placeholder="选择模板">
            <a-select-option v-for="t in templates" :key="t.id" :value="t.id">{{ t.name }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="项目描述">
          <a-textarea v-model="form.desc" :rows="3" placeholder="请输入项目描述" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import { apiGet } from '@/utils/api';
import {
  Card as ACard, Tag as ATag, Button as AButton, Modal as AModal,
  Descriptions as ADescriptions, DescriptionsItem as ADescriptionsItem,
  Table as ATable, Form as AForm, FormItem as AFormItem,
  Input as AInput, Select as ASelect, SelectOption as ASelectOption, Textarea as ATextarea
} from 'ant-design-vue';

onMounted(async () => {
  try { await apiGet('/analytics'); } catch { /* 空状态 */ }
});

const createOpen = ref(false)
const previewTpl = ref<any>(null)
const form = reactive({ name: '', template: undefined as number | undefined, desc: '' })

const templates = [
  { id: 1, name: '产品官网模板', desc: '建材产品展示型站点，含产品列表/详情/在线询盘', tags: ['产品展示', '在线询盘', 'SEO优化'], features: '产品列表页、产品详情页、在线询盘表单、关于我们', tech: 'Vue3 + TypeScript + Ant Design Vue', pages: '5-8 页', color: '#4a9b8c' },
  { id: 2, name: '企业品牌站模板', desc: '企业品牌形象站，公司介绍/新闻动态/合作案例/联系我们', tags: ['品牌展示', '新闻中心', '案例展示'], features: '首页轮播、公司介绍、新闻列表、案例展示、联系我们', tech: 'Vue3 + TypeScript + Tailwind CSS', pages: '8-12 页', color: '#10b981' },
  { id: 3, name: 'SEO矩阵站模板', desc: '全国县域SEO覆盖，AI自动生成内容，长尾关键词矩阵', tags: ['SEO矩阵', '县域覆盖', 'AI内容'], features: '地域词库配置、AI批量生成、自动发布、收录监控', tech: 'Next.js + TypeScript + Prisma', pages: '20-50 页', color: '#f59e0b' },
  { id: 4, name: '移动端H5模板', desc: '响应式设计，移动优先，适配微信/浏览器等多端访问', tags: ['响应式', '移动优先', '微信适配'], features: '移动端导航、一键拨号、微信分享、LBS定位', tech: 'React + TypeScript + Vant UI', pages: '3-6 页', color: '#ef4444' },
]

const pcols = [
  { title: '项目名称', dataIndex: 'name', key: 'name' },
  { title: '模板', dataIndex: 'template', key: 'template' },
  { title: '状态', key: 'status' },
  { title: '创建日期', dataIndex: 'date', key: 'date' },
]

const projects = ref<any[]>([])

function createProject() {
  if (!form.name) { message.warning('请输入项目名称'); return }
  projects.value.unshift({ id: Date.now(), name: form.name, template: templates.find(t => t.id === form.template)?.name || '未选择', status: 'active', date: new Date().toISOString().slice(0, 10) })
  message.success('项目创建成功')
  createOpen.value = false
  form.name = ''; form.template = undefined; form.desc = ''
}

function useTemplate(t: any) {
  form.name = t.name + ' 副本'
  form.template = t.id
  form.desc = t.desc
  previewTpl.value = null
  createOpen.value = true
}
</script>

<style scoped>
.proj-page { padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: start; margin-bottom: 16px; }
.section-card { margin-bottom: 16px; }
.tpl-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.tpl-card { overflow: hidden; }
.tpl-preview { height: 100px; display: flex; align-items: center; justify-content: center; margin: -16px -16px 12px -16px; }
.tpl-preview-text { color: #fff; font-size: 16px; font-weight: 600; }
.tpl-body { padding: 0; }
@media (max-width: 1200px) { .tpl-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 768px) { .tpl-grid { grid-template-columns: 1fr; } }
</style>
