<template>
  <YdPage title="AI 引擎概览" subtitle="管理 AI 提供商与模型池，快速接入第三方大模型" surface="elevated">
  <div class="ai-overview">
    <div class="stats-row">
      <a-card size="small" v-for="s in stats" :key="s.label">
        <a-statistic :title="s.label" :value="s.value" :suffix="s.suffix" :value-style="{color:s.color}" />
      </a-card>
    </div>

    <div class="panel">
      <h3 class="panel-title">API Key 管理</h3>
      <a-row :gutter="16">
        <a-col :span="8" v-for="p in providers" :key="p.id">
          <a-card size="small" class="pc">
            <template #title><span>{{ p.name }} <a-tag :color="providerConfiguredTagColor(p)">{{ providerConfiguredLabel(p) }}</a-tag></span></template>
            <template #extra><a-switch :checked="p.enabled" size="small" @change="(v:any)=>toggle(p.id,!!v)" /></template>
            <p class="cm">模型: {{ (p.models||[]).map((m:any)=>m.model_name).join(', ') || '-' }}</p>
            <a-space size="small">
              <a :href="links[p.name]" target="_blank" class="action-link">获取 Key</a>
              <a-button size="small" @click="editProvider(p)">编辑</a-button>
              <a-button size="small" danger @click="delProvider(p.id)">删除</a-button>
            </a-space>
          </a-card>
        </a-col>
      </a-row>
      <a-button type="dashed" size="small" style="margin-top:12px" @click="showProvModal=true">添加提供商</a-button>
    </div>

    <div class="panel">
      <h3 class="panel-title">模型提供商官方链接</h3>
      <a-row :gutter="12">
        <a-col :span="4" v-for="l in linkList" :key="l.name">
          <a-card size="small" :hoverable="true" class="link-card" style="cursor:pointer" @click="openLink(l.url)">
            <div class="lc-icon">{{ l.icon }}</div>
            <div class="lc-name">{{ l.name }}</div>
            <a-tag :color="providerStatus[l.name] ? 'green' : 'red'" size="small">{{ providerStatus[l.name] ? '已配置' : '未配置' }}</a-tag>
            <a-button size="small" type="link" block>获取 API Key</a-button>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <div class="panel">
      <h3 class="panel-title">快速接入指南</h3>
      <a-row :gutter="16">
        <a-col :span="8" v-for="(step,i) in steps" :key="i">
          <a-alert :message="`Step ${i+1}`" :description="step" type="info" show-icon />
        </a-col>
      </a-row>
      <a-row :gutter="12" style="margin-top:12px">
        <a-col :span="12"><a-input placeholder="粘贴 API Key" v-model:value="quickKey" /></a-col>
        <a-col :span="6"><a-select v-model:value="quickProvider" placeholder="选择提供商">
          <a-select-option value="openai">OpenAI</a-select-option>
          <a-select-option value="deepseek">DeepSeek</a-select-option>
          <a-select-option value="nvidia">NVIDIA</a-select-option>
          <a-select-option value="anthropic">Anthropic</a-select-option>
          <a-select-option value="gemini">Gemini</a-select-option>
        </a-select></a-col>
        <a-col :span="6"><a-button type="primary" block @click="autoConfig">自动测试连接</a-button></a-col>
      </a-row>
    </div>

    <div class="panel">
      <h3 class="panel-title">模型池</h3>
      <a-table :columns="mCols" :data-source="models" row-key="id" :pagination="false" size="small">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key==='active'"><a-switch :checked="record.active" size="small" @change="(v:any)=>toggleModel(record.id,!!v)" /></template>
        </template>
      </a-table>
    </div>

    <a-modal v-model:open="showProvModal" title="添加提供商" @ok="saveProvider">
      <a-form layout="vertical" :model="pf">
        <a-form-item label="名称"><a-input v-model:value="pf.name" /></a-form-item>
        <a-form-item label="类型"><a-select v-model:value="pf.provider_type">
          <a-select-option value="openai">OpenAI</a-select-option>
          <a-select-option value="deepseek">DeepSeek</a-select-option>
          <a-select-option value="nvidia">NVIDIA</a-select-option>
          <a-select-option value="anthropic">Anthropic</a-select-option>
          <a-select-option value="gemini">Gemini</a-select-option>
        </a-select></a-form-item>
        <a-form-item label="API Key"><a-input-password v-model:value="pf.api_key" /></a-form-item>
        <a-form-item label="Base URL"><a-input v-model:value="pf.base_url" /></a-form-item>
        <a-form-item label="默认模型"><a-input v-model:value="pf.default_model" /></a-form-item>
      </a-form>
    </a-modal>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import { apiGet, apiPost, apiPut, apiDelete } from '@/utils/api';
import {
  apiErrorMessage,
  buildProviderStatusMap,
  providerConfiguredLabel,
  providerConfiguredTagColor,
} from '@/utils/aiConfigHelpers';

const providers = ref<any[]>([]);
const models = ref<any[]>([]);
const showProvModal = ref(false);
const editId = ref<string | null>(null);
const pf = ref({ name:'', provider_type:'openai', api_key:'', base_url:'', default_model:'' });
const quickKey = ref('');
const quickProvider = ref('openai');

const links: Record<string,string> = {
  OpenAI:'https://platform.openai.com/api-keys',
  DeepSeek:'https://platform.deepseek.com/api_keys',
  'NVIDIA NIM':'https://build.nvidia.com/explore/discover',
  Anthropic:'https://console.anthropic.com/settings/keys',
  Google:'https://aistudio.google.com/apikey',
  '硅基流动':'https://siliconflow.cn',
};
const linkList = ['OpenAI','DeepSeek','NVIDIA NIM','Anthropic','Google','硅基流动'].map(n=>({name:n, icon:n.charAt(0), url:links[n]||'#'}));
const steps = ['注册对应平台账号','创建 API Key 并复制','在下方面板粘贴 Key 完成配置'];

const stats = computed(()=>[
  { label:'活跃供应商', value:providers.value.filter(p=>p.enabled).length, suffix:'个', color:'#1890ff' },
  { label:'模型总数', value:models.value.length, suffix:'个', color:'#52c41a' },
  { label:'今日调用', value:'--', suffix:'次', color:'#faad14' },
  { label:'成功率', value:'--', suffix:'%', color:'#722ed1' },
]);

const providerStatus = computed(() => buildProviderStatusMap(providers.value));

const mCols = [
  { title:'提供商', dataIndex:'provider_name', width:120 },
  { title:'模型名', dataIndex:'model_name', width:180 },
  { title:'类型', dataIndex:'model_type', width:100 },
  { title:'Temperature', dataIndex:'temperature', width:110 },
  { title:'Max Tokens', dataIndex:'max_tokens', width:110 },
  { title:'启用', key:'active', width:80 },
];

async function loadAll() { try { providers.value = await apiGet('/super-admin/ai-config/providers'); models.value = await apiGet('/super-admin/ai-config/models'); } catch {} }
async function toggle(id:string, v:boolean) {
  try {
    await apiPut(`/super-admin/ai-config/providers/${id}`,{enabled:v});
    message.success('已更新');
    loadAll();
  } catch (e: unknown) { message.error(apiErrorMessage(e, '切换失败')); }
}
async function toggleModel(id:string, v:boolean) {
  try {
    await apiPut(`/super-admin/ai-config/models/${id}`,{active:v});
    message.success('已更新');
    loadAll();
  } catch (e: unknown) { message.error(apiErrorMessage(e, '切换失败')); }
}
async function saveProvider() {
  try {
    const payload = { ...pf.value, enabled: true };
    if(editId.value) await apiPut(`/super-admin/ai-config/providers/${editId.value}`, payload);
    else await apiPost('/super-admin/ai-config/providers', payload);
    showProvModal.value = false; editId.value = null; pf.value = { name:'', provider_type:'openai', api_key:'', base_url:'', default_model:'' };
    message.success('保存成功'); loadAll();
  } catch (e: unknown) { message.error(apiErrorMessage(e, '保存失败')); }
}
function editProvider(p:any) {
  editId.value = p.id; pf.value = { name:p.name, provider_type:p.provider_type, api_key:'', base_url:p.base_url||'', default_model:p.default_model||'' };
  showProvModal.value = true;
}
async function delProvider(id:string) { try { await apiDelete(`/super-admin/ai-config/providers/${id}`); loadAll(); } catch{message.error('删除失败');} }
function openLink(url:string) { window.open(url, '_blank'); }
async function autoConfig() {
  if(!quickKey.value) { message.warn('请先粘贴 API Key'); return; }
  try {
    await apiPost('/super-admin/ai-config/providers', { name:quickProvider.value, provider_type:quickProvider.value, api_key:quickKey.value, enabled:true });
    quickKey.value=''; message.success('配置完成'); loadAll();
  } catch (e: unknown) { message.error(apiErrorMessage(e, '自动配置失败')); }
}
onMounted(loadAll);
</script>

<style scoped lang="scss">
.ai-overview { padding: 24px; }
.page-header { margin-bottom: 20px; .page-title { font-size:22px; font-weight:700; color:#1f2937; } .page-desc { color:#6b7280; font-size:14px; margin-top:4px; } }
.stats-row { display: grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:20px; }
.panel { background:#fff; border-radius:12px; padding:18px; box-shadow:0 2px 8px rgba(0,0,0,.06); margin-bottom:18px; .panel-title { font-size:15px; font-weight:600; margin-bottom:12px; } }
.pc { margin-bottom:10px; }
.cm { font-size:.78rem; color:#94a3b8; }
.action-link { font-size:.78rem; color:#1890ff; }
.link-card { text-align:center; cursor:pointer; .lc-icon { font-size:24px; font-weight:700; margin-bottom:4px; } .lc-name { font-size:13px; font-weight:500; margin-bottom:6px; } }
@media(max-width:1024px) { .stats-row { grid-template-columns:repeat(2,1fr); } }
</style>
