<template>
  <YdPage title="内容生成模板" subtitle="管理 AI 内容生成模板，支持优化、SEO、代码等场景" surface="elevated">
    <template #actions>
      <a-select v-model:value="filterTask" style="width:140px" @change="() => loadTemplates()">
        <a-select-option value="">全部任务</a-select-option>
        <a-select-option value="optimize">内容优化</a-select-option>
        <a-select-option value="llms_txt">LLMs.txt</a-select-option>
        <a-select-option value="seo_analysis">SEO分析</a-select-option>
        <a-select-option value="code">代码生成</a-select-option>
        <a-select-option value="product_gen">产品描述</a-select-option>
        <a-select-option value="polish">内容润色</a-select-option>
        <a-select-option value="general">通用生成</a-select-option>
      </a-select>
      <a-button type="primary" @click="showCreateModal=true; editing=null; resetForm()">新建模板</a-button>
    </template>
  <div class="tpl-mgr">
    <!-- 统计 -->
    <div class="stats-row">
      <a-card size="small" v-for="s in stats" :key="s.label">
        <a-statistic :title="s.label" :value="s.value" :suffix="s.suffix" :value-style="{color:s.color}" />
      </a-card>
    </div>

    <!-- 模板列表 -->
    <div class="panel">
      <h3 class="panel-title">模板列表</h3>

      <a-table :columns="cols" :data-source="templates" :loading="loading" :pagination="pagination" row-key="id" size="small" @change="handleTableChange">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key==='task_type'">
            <a-tag :color="taskColor(record.task_type)">{{ taskLabel(record.task_type) }}</a-tag>
          </template>
          <template v-if="column.key==='is_active'">
            <a-switch :checked="record.is_active" size="small" @change="(v:any)=>toggleActive(record, !!v)" />
          </template>
          <template v-if="column.key==='actions'">
            <a-space size="small">
              <a-button size="small" @click="editTemplate(record)">编辑</a-button>
              <a-button size="small" danger @click="deleteTemplate(record.id)">删除</a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>

    <!-- 创建/编辑弹窗 -->
    <a-modal v-model:open="showCreateModal" :title="editing ? '编辑模板' : '新建模板'" @ok="saveTemplate" :confirm-loading="saving">
      <a-form layout="vertical" :model="form">
        <a-form-item label="模板名称">
          <a-input v-model:value="form.name" placeholder="如：建材产品描述生成器" />
        </a-form-item>
        <a-form-item label="任务类型">
          <a-select v-model:value="form.task_type">
            <a-select-option value="optimize">内容优化</a-select-option>
            <a-select-option value="llms_txt">LLMs.txt</a-select-option>
            <a-select-option value="seo_analysis">SEO分析</a-select-option>
            <a-select-option value="code">代码生成</a-select-option>
            <a-select-option value="product_gen">产品描述</a-select-option>
            <a-select-option value="polish">内容润色</a-select-option>
            <a-select-option value="general">通用生成</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="系统提示词（System Prompt）">
          <a-textarea v-model:value="form.system_prompt" :rows="4" placeholder="AI 的角色定位与行为规则..." />
        </a-form-item>
        <a-form-item label="用户提示词模板（User Prompt Template）">
          <a-textarea v-model:value="form.user_prompt_template" :rows="6" placeholder="用 {{变量名}} 表示动态变量，如：请为产品{{product_name}}生成描述..." />
          <div v-pre style="color:#8c8c8c;font-size:12px;margin-top:4px">可用变量：{{product_name}}, {{industry}}, {{target_market}}, {{keywords}}, {{tone}}</div>
        </a-form-item>
        <a-form-item label="可用变量（JSON数组）">
          <a-textarea v-model:value="form.variables_json" :rows="2" placeholder='["product_name", "industry", "target_market"]' />
        </a-form-item>
        <a-form-item label="默认参数（JSON）">
          <a-textarea v-model:value="form.default_params_json" :rows="2" placeholder='{"temperature": 0.7, "max_tokens": 2000}' />
        </a-form-item>
        <a-form-item label="状态">
          <a-switch v-model:checked="form.is_active" checked-children="启用" un-checked-children="禁用" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import { apiGet, apiPost, apiPut, apiDelete } from '@/utils/api';

const templates = ref<any[]>([]);
const loading = ref(false);
const saving = ref(false);
const filterTask = ref<string>('');
const showCreateModal = ref(false);
const editing = ref<string|null>(null);

const form = ref<any>({
  name: '',
  task_type: 'product_gen',
  system_prompt: '',
  user_prompt_template: '',
  variables_json: '[]',
  default_params_json: '{"temperature": 0.7, "max_tokens": 2000}',
  is_active: true,
});

const stats = ref<any[]>([]);

const pagination = ref({ current: 1, pageSize: 20, total: 0 });

const cols = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '模板名称', dataIndex: 'name', key: 'name' },
  { title: '任务类型', key: 'task_type', width: 120 },
  { title: '变量数', key: 'var_count', width: 80, customRender: ({ record }: { record: { variables_json?: string } }) => JSON.parse(record.variables_json || '[]').length },
  { title: '状态', key: 'is_active', width: 80 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180, customRender: ({ text }: { text?: string }) => (text ? new Date(text).toLocaleString('zh-CN') : '-') },
  { title: '操作', key: 'actions', width: 160 },
];

const taskColorMap: Record<string,string> = {
  optimize: 'blue', llms_txt: 'cyan', seo_analysis: 'green',
  code: 'purple', product_gen: 'orange', polish: 'pink', general: 'default',
};
const taskLabelMap: Record<string,string> = {
  optimize: '内容优化', llms_txt: 'LLMs.txt', seo_analysis: 'SEO分析',
  code: '代码生成', product_gen: '产品描述', polish: '内容润色', general: '通用',
};
function taskColor(t:string) { return taskColorMap[t] || 'default'; }
function taskLabel(t:string) { return taskLabelMap[t] || t; }

async function loadTemplates() {
  loading.value = true;
  try {
    const res = await apiGet('/api/v1/ai/templates', {
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
      task_type: filterTask.value || undefined,
    });
    if (res.code === 0) {
      templates.value = res.data.items || [];
      pagination.value.total = res.data.total || 0;
      stats.value[0].value = res.data.total || 0;
      stats.value[1].value = (res.data.items||[]).filter((t:any) => t.is_active).length;
      stats.value[2].value = (res.data.items||[]).filter((t:any) => !t.is_active).length;
    }
  } catch (e: any) {
    message.error('加载模板失败: ' + e.message);
  } finally {
    loading.value = false;
  }
}

function resetForm() {
  form.value = { name:'', task_type:'product_gen', system_prompt:'', user_prompt_template:'', variables_json:'[]', default_params_json:'{"temperature":0.7,"max_tokens":2000}', is_active:true };
}

function editTemplate(rec: any) {
  editing.value = rec.id;
  form.value = {
    name: rec.name,
    task_type: rec.task_type,
    system_prompt: rec.system_prompt,
    user_prompt_template: rec.user_prompt_template,
    variables_json: rec.variables_json,
    default_params_json: rec.default_params_json,
    is_active: rec.is_active,
  };
  showCreateModal.value = true;
}

async function saveTemplate() {
  saving.value = true;
  try {
    const payload = { ...form.value };
    let res;
    if (editing.value) {
      res = await apiPut(`/api/v1/ai/templates/${editing.value}`, payload);
    } else {
      res = await apiPost('/api/v1/ai/templates', payload);
    }
    if (res.code === 0) {
      message.success(editing.value ? '更新成功' : '创建成功');
      showCreateModal.value = false;
      await loadTemplates();
    } else {
      message.error(res.message || '操作失败');
    }
  } catch (e: any) {
    message.error('保存失败: ' + e.message);
  } finally {
    saving.value = false;
  }
}

async function toggleActive(rec: any, active: boolean) {
  try {
    const res = await apiPut(`/api/v1/ai/templates/${rec.id}`, { is_active: active });
    if (res.code === 0) {
      rec.is_active = active;
      message.success(active ? '已启用' : '已禁用');
      await loadTemplates();
    }
  } catch (e: any) {
    message.error('操作失败: ' + e.message);
  }
}

async function deleteTemplate(id: string) {
  if (!confirm('确定删除此模板？')) return;
  try {
    await apiDelete(`/api/v1/ai/templates/${id}`);
    message.success('删除成功');
    await loadTemplates();
  } catch (e: any) {
    message.error('删除失败: ' + e.message);
  }
}

function handleTableChange(p: any) {
  pagination.value.current = p.current;
  pagination.value.pageSize = p.pageSize;
  loadTemplates();
}

onMounted(() => { loadTemplates(); });
</script>

<style scoped>
.tpl-mgr { padding: 24px; }
.page-header { margin-bottom: 24px; }
.page-title { font-size: 24px; font-weight: 600; margin: 0 0 8px 0; }
.page-desc { color: #8c8c8c; margin: 0; }
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.panel { background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 2px rgba(0,0,0,0.06); }
.panel-title { font-size: 16px; font-weight: 600; margin: 0; padding-bottom: 12px; border-bottom: 1px solid #f0f0f0; }
</style>
