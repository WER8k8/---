<template>
  <YdPage title="AI 控制台" subtitle="AI 提供商与模型池总览 — 快速接入15大第三方大模型" surface="elevated">
  <div class="ai-overview">
    <!-- AI引擎状态横幅 -->
    <div class="ai-engine-status-banner">
      <button
        type="button"
        class="banner-card banner-card-link"
        @click="openPage('/admin/ai-center/models')"
      >
        <div class="banner-icon-wrap" style="background:#f0fdf4">
          <CheckCircleFilled style="color:#10b981;font-size:20px" />
        </div>
        <div class="banner-info">
          <span class="banner-label">可用模型</span>
          <span class="banner-value">{{ configuredModels }}</span>
          <span class="banner-hint">点击查看模型池</span>
        </div>
      </button>
      <button
        type="button"
        class="banner-card banner-card-link"
        @click="openPage('/admin/ai-center/provider-setup')"
      >
        <div class="banner-icon-wrap" :style="{background: configuredProviders > 0 ? '#f0fdf4' : '#fef3c7'}">
          <component :is="configuredProviders > 0 ? CheckCircleFilled : ExclamationCircleFilled"
            :style="{color: configuredProviders > 0 ? '#10b981' : '#f59e0b',fontSize:'20px'}" />
        </div>
        <div class="banner-info">
          <span class="banner-label">已配置提供商</span>
          <span class="banner-value">{{ configuredProviders }} / 15</span>
          <span class="banner-hint">点击进入模型配置</span>
        </div>
      </button>
      <button
        v-if="unconfiguredProviders > 0"
        type="button"
        class="banner-card banner-card-link banner-card-warn"
        @click="openPage('/admin/ai-center/provider-setup')"
      >
        <div class="banner-icon-wrap" style="background:#fef2f2">
          <InfoCircleFilled style="color:#ef4444;font-size:20px" />
        </div>
        <div class="banner-info">
          <span class="banner-label">待接入平台</span>
          <span class="banner-value banner-value-warn">{{ unconfiguredProviders }} 个</span>
          <span class="banner-hint">点击进入模型配置，粘贴 API Key 完成接入</span>
        </div>
      </button>
      <div class="banner-card" v-else>
        <div class="banner-icon-wrap" style="background:#f0fdf4">
          <CheckCircleFilled style="color:#10b981;font-size:20px" />
        </div>
        <div class="banner-info">
          <span class="banner-label">引擎状态</span>
          <span class="banner-value banner-value-ok">全部就绪</span>
        </div>
      </div>
    </div>

    <div class="stats-row">
      <a-card
        size="small"
        v-for="s in stats"
        :key="s.label"
        class="stat-card-link"
        :hoverable="Boolean(s.path)"
        @click="s.path && openPage(s.path)"
      >
        <a-statistic :title="s.label" :value="s.value" :suffix="s.suffix" :value-style="{color:s.color}" />
      </a-card>
    </div>

    <!-- 场景健康快照 -->
    <div class="panel health-panel">
      <div class="health-panel-head">
        <h3 class="panel-title" style="margin:0">场景模型健康</h3>
        <a-space>
          <a-button size="small" :loading="healthLoading" @click="runHealthCheck">立即巡检</a-button>
          <a-button size="small" type="link" @click="openPage('/admin/ai-center/scenario-models')">场景配置</a-button>
        </a-space>
      </div>
      <a-alert
        v-if="healthSnapshot"
        :type="healthSnapshot.unhealthy_count === 0 ? 'success' : 'warning'"
        show-icon
        :message="healthSnapshotMessage"
      />
      <a-alert v-else type="info" show-icon message="尚无巡检快照" description="点击「立即巡检」或等待定时任务写入快照。" />
      <div v-if="healthSnapshot?.scenarios?.length" class="health-tags">
        <a-tag
          v-for="row in unhealthyScenarios"
          :key="row.scenario"
          color="error"
        >
          {{ row.scenario }} 异常
        </a-tag>
      </div>
    </div>

    <!-- Token 用量摘要（真实库统计，无调用时为 0） -->
    <div class="usage-summary">
      <div class="summary-left">
        <span class="summary-title">Token 用量摘要</span>
        <div class="summary-ring-wrap">
          <div class="summary-ring">
            <svg width="100" height="100" viewBox="0 0 120 120">
              <circle cx="60" cy="60" r="50" fill="none" stroke="#f0f0f0" stroke-width="10" />
              <circle cx="60" cy="60" r="50" fill="none"
                :stroke="usageRingColor"
                stroke-width="10"
                stroke-linecap="round"
                :stroke-dasharray="`${usagePercent * 3.14} ${314 - usagePercent * 3.14}`"
                transform="rotate(-90 60 60)"
                style="transition: stroke-dasharray 0.6s ease"
              />
            </svg>
            <div class="ring-center">
              <span class="ring-pct">{{ usagePercent }}%</span>
              <span class="ring-label">已使用</span>
            </div>
          </div>
        </div>
      </div>
      <div
        v-if="usageLoaded && usageStats.monthly_tokens === 0 && usageStats.today_calls === 0"
        class="summary-empty"
      >
        <a-empty description="尚无 AI 调用记录，配置提供商并开始调用后此处会显示真实用量" />
      </div>
      <div
        v-else
        class="summary-details"
      >
        <div class="summary-stat">
          <span class="summary-stat-label">本月已用</span>
          <span class="summary-stat-value">{{ usageStats.monthly_tokens }}K</span>
        </div>
        <div class="summary-stat">
          <span class="summary-stat-label">剩余配额</span>
          <span class="summary-stat-value" :class="{ 'text-danger': usageStats.remaining < 2000 }">{{ usageStats.remaining }}K</span>
        </div>
        <div class="summary-stat">
          <span class="summary-stat-label">总额度</span>
          <span class="summary-stat-value">{{ usageStats.total_quota }}K</span>
        </div>
        <div class="summary-progress">
          <a-progress
            :percent="usagePercent"
            :stroke-color="usageRingColor"
            size="small"
            :show-info="false"
          />
          <div v-if="usagePercent > 80" class="usage-warning">
            <WarningOutlined style="color:#ef4444" /> 配额即将耗尽！
          </div>
        </div>
        <a-button type="link" class="summary-link" @click="openPage('/admin/ai-center/usage')">
          查看详细用量 <RightOutlined />
        </a-button>
      </div>
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
          <a-card size="small" :hoverable="true" class="link-card" @click="openProviderSetup(l.name)">
            <div class="lc-icon">{{ l.icon }}</div>
            <div class="lc-name">{{ l.name }}</div>
            <a-tag :color="providerStatus[l.name] ? 'green' : 'red'" size="small">{{ providerStatus[l.name] ? '已配置' : '未配置' }}</a-tag>
            <a-button size="small" type="link" block @click.stop="openLink(l.url)">去官网获取 Key</a-button>
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
          <a-select-option value="nvidia">NVIDIA NIM</a-select-option>
          <a-select-option value="deepseek">DeepSeek</a-select-option>
          <a-select-option value="openai">OpenAI</a-select-option>
          <a-select-option value="baidu">百度文心一言</a-select-option>
          <a-select-option value="aliyun">阿里通义千问</a-select-option>
          <a-select-option value="byte">字节豆包</a-select-option>
          <a-select-option value="zhipu">智谱GLM</a-select-option>
          <a-select-option value="kimi">Kimi</a-select-option>
          <a-select-option value="01wanwu">零一万物</a-select-option>
          <a-select-option value="siliconflow">硅基流动</a-select-option>
          <a-select-option value="minimax">MiniMax</a-select-option>
          <a-select-option value="xunfei">讯飞星火</a-select-option>
          <a-select-option value="anthropic">Anthropic</a-select-option>
          <a-select-option value="google">Google Gemini</a-select-option>
          <a-select-option value="meta">Meta Llama</a-select-option>
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
          <a-select-option value="nvidia">NVIDIA NIM</a-select-option>
          <a-select-option value="deepseek">DeepSeek</a-select-option>
          <a-select-option value="openai">OpenAI</a-select-option>
          <a-select-option value="baidu">百度文心一言</a-select-option>
          <a-select-option value="aliyun">阿里通义千问</a-select-option>
          <a-select-option value="byte">字节豆包</a-select-option>
          <a-select-option value="zhipu">智谱GLM</a-select-option>
          <a-select-option value="kimi">Kimi</a-select-option>
          <a-select-option value="01wanwu">零一万物</a-select-option>
          <a-select-option value="siliconflow">硅基流动</a-select-option>
          <a-select-option value="minimax">MiniMax</a-select-option>
          <a-select-option value="xunfei">讯飞星火</a-select-option>
          <a-select-option value="anthropic">Anthropic</a-select-option>
          <a-select-option value="google">Google Gemini</a-select-option>
          <a-select-option value="meta">Meta Llama</a-select-option>
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
import { useWorkTabNavigation } from '@/composables/useWorkTabNavigation';
import { apiGet, apiPost, apiPut, apiDelete } from '@/utils/api';
import {
  apiErrorMessage,
  buildProviderStatusMap,
  providerConfiguredLabel,
  providerConfiguredTagColor,
} from '@/utils/aiConfigHelpers';
import { WarningOutlined, RightOutlined, CheckCircleFilled, ExclamationCircleFilled, InfoCircleFilled } from '@ant-design/icons-vue';

const { go: openPage } = useWorkTabNavigation();

const providers = ref<any[]>([]);
const models = ref<any[]>([]);
const showProvModal = ref(false);
const editId = ref<string | null>(null);
const pf = ref({ name:'', provider_type:'openai', api_key:'', base_url:'', default_model:'' });
const quickKey = ref('');
const quickProvider = ref('openai');
const healthLoading = ref(false);
const healthSnapshot = ref<{
  healthy_count?: number;
  unhealthy_count?: number;
  total?: number;
  saved_at?: string;
  scenarios?: Array<{ scenario: string; healthy: boolean; latency_ms?: number }>;
} | null>(null);

const healthSnapshotMessage = computed(() => {
  const h = healthSnapshot.value;
  if (!h) return '';
  const base = `健康 ${h.healthy_count || 0}/${h.total || 0} · 异常 ${h.unhealthy_count || 0}`;
  if (!h.saved_at) return base;
  try {
    return `${base} · 更新于 ${new Date(h.saved_at).toLocaleString()}`;
  } catch {
    return `${base} · 更新于 ${h.saved_at}`;
  }
});

const unhealthyScenarios = computed(() =>
  (healthSnapshot.value?.scenarios || []).filter(s => !s.healthy),
);

const links: Record<string,string> = {
  OpenAI:'https://platform.openai.com/api-keys',
  DeepSeek:'https://platform.deepseek.com/api_keys',
  'NVIDIA NIM':'https://build.nvidia.com/explore/discover',
  Anthropic:'https://console.anthropic.com/settings/keys',
  Google:'https://aistudio.google.com/apikey',
  '百度文心一言':'https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application',
  '阿里通义千问':'https://dashscope.console.aliyun.com/apiKey',
  '字节豆包':'https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey',
  '智谱GLM':'https://open.bigmodel.cn/usercenter/apikeys',
  'Kimi':'https://platform.moonshot.cn/console/api-keys',
  '零一万物':'https://platform.lingyiwanwu.com/apikeys',
  '硅基流动':'https://cloud.siliconflow.cn/account/ak',
  'MiniMax':'https://platform.minimaxi.com/user-center/basic-information/interface-key',
  '讯飞星火':'https://console.xfyun.cn/services/cbm',
  'Meta Llama':'https://build.nvidia.com/meta',
};
const linkList = [
  'NVIDIA NIM','DeepSeek','OpenAI','百度文心一言','阿里通义千问','字节豆包',
  '智谱GLM','Kimi','零一万物','硅基流动','MiniMax','讯飞星火','Anthropic','Google','Meta Llama'
].map(n=>({name:n, icon:n.charAt(0), url:links[n]||'#'}));
const steps = ['注册对应平台账号','创建 API Key 并复制','在下方面板粘贴 Key 完成配置'];

const usageLoaded = ref(false);
const usageStats = ref({
  monthly_tokens: 0,
  today_calls: 0,
  today_success_rate: 0,
  remaining: 0,
  total_quota: 10000,
  quota_percent: 0,
});
const usagePercent = computed(() => usageStats.value.quota_percent);
const usageRingColor = computed(() => {
  if (usagePercent.value > 80) return '#ef4444';
  if (usagePercent.value > 50) return '#f59e0b';
  return '#10b981';
});

const stats = computed(() => [
  {
    label: '活跃供应商',
    value: providers.value.filter(p => p.enabled).length,
    suffix: '个',
    color: '#1890ff',
    path: '/admin/ai-center/provider-setup',
  },
  {
    label: '模型总数',
    value: models.value.length,
    suffix: '个',
    color: '#52c41a',
    path: '/admin/ai-center/models',
  },
  {
    label: '今日调用',
    value: usageStats.value.today_calls.toLocaleString('zh-CN'),
    suffix: '次',
    color: '#faad14',
    path: '/admin/ai-center/logs',
  },
  {
    label: '成功率',
    value: usageStats.value.today_calls > 0 ? String(usageStats.value.today_success_rate) : '—',
    suffix: usageStats.value.today_calls > 0 ? '%' : '',
    color: '#722ed1',
    path: '/admin/ai-center/logs',
  },
]);

// AI引擎状态横幅计算属性
const allProviderNames = [
  'NVIDIA NIM', 'DeepSeek', 'OpenAI', '百度文心一言', '阿里通义千问',
  '字节豆包', '智谱GLM', 'Kimi', '零一万物', '硅基流动',
  'MiniMax', '讯飞星火', 'Anthropic', 'Google', 'Meta Llama'
];
const configuredProviders = computed(() => {
  const configured = new Set<string>();
  providers.value.forEach((p: any) => {
    if (p.is_active !== false && (p.api_key_masked || p.provider_type === 'nvidia')) {
      configured.add(p.name || p.provider_type);
    }
  });
  return configured.size;
});
const unconfiguredProviders = computed(() => Math.max(0, 15 - configuredProviders.value));
const configuredModels = computed(() =>
  models.value.filter((m: any) => m.is_active !== false).length,
);

const providerStatus = computed(() => buildProviderStatusMap(providers.value));

const mCols = [
  { title:'提供商', dataIndex:'provider_name', width:120 },
  { title:'模型名', dataIndex:'model_name', width:180 },
  { title:'类型', dataIndex:'model_type', width:100 },
  { title:'Temperature', dataIndex:'temperature', width:110 },
  { title:'Max Tokens', dataIndex:'max_tokens', width:110 },
  { title:'启用', key:'active', width:80 },
];

async function loadAll() {
  try {
    providers.value = await apiGet('/super-admin/ai-config/providers');
    models.value = await apiGet('/super-admin/ai-config/models');
  } catch { /* 空状态 */ }
}

async function loadUsageStats() {
  usageLoaded.value = false;
  try {
    const overview = await apiGet<{
      monthly_tokens?: number;
      remaining_quota?: number;
      total_quota?: number;
      quota_percent?: number;
    }>('/ai-usage/overview');
    usageStats.value.monthly_tokens = overview?.monthly_tokens ?? 0;
    usageStats.value.remaining = overview?.remaining_quota ?? 0;
    usageStats.value.total_quota = overview?.total_quota ?? 10000;
    usageStats.value.quota_percent = overview?.quota_percent ?? 0;
  } catch { /* 保持 0 */ }

  try {
    const aiUsage = await apiGet<{
      today_calls?: number;
      today_success_rate?: number;
    }>('/super-admin/dashboard/ai-usage');
    usageStats.value.today_calls = aiUsage?.today_calls ?? 0;
    usageStats.value.today_success_rate = aiUsage?.today_success_rate ?? 0;
  } catch { /* 保持 0 */ }

  usageLoaded.value = true;
}

async function loadHealthSnapshot() {
  try {
    healthSnapshot.value = await apiGet('/super-admin/ai-config/nvidia/scenarios/health/latest');
  } catch {
    healthSnapshot.value = null;
  }
}

async function runHealthCheck() {
  healthLoading.value = true;
  try {
    const report = await apiPost('/super-admin/ai-config/nvidia/scenarios/health/run', {});
    healthSnapshot.value = report;
    message.success('场景健康巡检已完成');
  } catch {
    message.error('巡检失败');
  } finally {
    healthLoading.value = false;
  }
}
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
function openLink(url: string) { window.open(url, '_blank'); }

function openProviderSetup(_name?: string) {
  openPage('/admin/ai-center/provider-setup');
}
async function autoConfig() {
  if(!quickKey.value) { message.warn('请先粘贴 API Key'); return; }
  try {
    await apiPost('/super-admin/ai-config/providers', { name:quickProvider.value, provider_type:quickProvider.value, api_key:quickKey.value, enabled:true });
    quickKey.value=''; message.success('配置完成'); loadAll();
  } catch (e: unknown) { message.error(apiErrorMessage(e, '自动配置失败')); }
}
onMounted(() => {
  loadAll();
  loadUsageStats();
  loadHealthSnapshot();
});
</script>

<style scoped lang="scss">
.ai-overview { padding: 0; }
.stats-row { display: grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:20px; }

/* AI引擎状态横幅 */
.ai-engine-status-banner {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 14px;
  margin-bottom: 20px;
}
.banner-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fff;
  border-radius: 12px;
  padding: 16px 18px;
  box-shadow: 0 2px 8px rgba(0,0,0,.06);
  border: 1px solid #e5e7eb;
}
.banner-card-link {
  width: 100%;
  text-align: left;
  font: inherit;
  color: inherit;
  appearance: none;
  background: #fff;
  border: 1px solid #e5e7eb;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s, transform 0.15s;
}
.banner-card-link:hover {
  border-color: #c7d2fe;
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.1);
  transform: translateY(-1px);
}
.banner-card-warn:hover {
  border-color: #fca5a5;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.12);
}
.stat-card-link {
  cursor: pointer;
}
.banner-icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.banner-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.banner-label {
  font-size: 12px;
  color: #9ca3af;
  font-weight: 500;
}
.banner-value {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1.2;
}
.banner-value-warn {
  color: #ef4444;
}
.banner-value-ok {
  color: #10b981;
}
.banner-hint {
  font-size: 11px;
  color: #6b7280;
  margin-top: 2px;
}
.panel { background:#fff; border-radius:12px; padding:18px; box-shadow:0 2px 8px rgba(0,0,0,.06); margin-bottom:18px; .panel-title { font-size:15px; font-weight:600; margin-bottom:12px; } }
.health-panel-head { display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:12px; }
.health-tags { margin-top:12px; display:flex; flex-wrap:wrap; gap:6px; }
.pc { margin-bottom:10px; }
.cm { font-size:.78rem; color:#94a3b8; }
.action-link { font-size:.78rem; color:#1890ff; }
.link-card { text-align:center; cursor:pointer; .lc-icon { font-size:24px; font-weight:700; margin-bottom:4px; } .lc-name { font-size:13px; font-weight:500; margin-bottom:6px; } }

/* 用量摘要 */
.usage-summary {
  display: flex;
  gap: 24px;
  background: #fff;
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,.06);
  margin-bottom: 18px;
  align-items: center;
}
.summary-left {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}
.summary-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}
.summary-ring-wrap {
  display: flex;
  justify-content: center;
}
.summary-ring {
  position: relative;
  width: 100px;
  height: 100px;
}
.ring-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.ring-pct {
  font-size: 22px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1;
}
.ring-label {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 2px;
}
.summary-empty {
  flex: 1;
  padding: 8px 0;
}
.summary-details {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.summary-stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 14px;
  background: #f8fafc;
  border-radius: 10px;
}
.summary-stat-label {
  font-size: 12px;
  color: #94a3b8;
}
.summary-stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
}
.summary-stat-value.text-danger {
  color: #ef4444;
}
.summary-progress {
  grid-column: 1 / -1;
  margin-top: 4px;
}
.usage-warning {
  font-size: 12px;
  color: #ef4444;
  margin-top: 6px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.summary-link {
  grid-column: 1 / -1;
  font-size: 13px;
  color: #1890ff;
  text-align: right;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
}

@media(max-width:1024px) { .stats-row { grid-template-columns:repeat(2,1fr); } .usage-summary { flex-direction: column; } }
</style>
