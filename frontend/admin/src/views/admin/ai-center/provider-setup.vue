/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="AI 平台接入" subtitle="选择大模型平台、配置 API Key 并完成连接测试" surface="elevated">
  <div class="provider-setup">
    <!-- 步骤条 -->
    <a-steps :current="currentStep" class="setup-steps">
      <a-step title="选择平台" description="选择要接入的AI大模型" />
      <a-step title="配置密钥" description="填写API Key等信息" />
      <a-step title="完成配置" description="确认配置并启用" />
    </a-steps>

    <!-- 步骤1：选择平台 -->
    <div v-if="currentStep === 0" class="step-panel">
      <h2 class="step-title">选择AI大模型平台</h2>
      <p class="step-desc">选择你想要接入的大模型平台，共 {{ allPlatforms.length }} 个主流平台可选。</p>

      <!-- 国内平台 -->
      <div class="platform-section">
        <h3 class="section-label">
          <SafetyCertificateOutlined class="section-icon" />
          国内平台
        </h3>
        <div class="platform-grid">
          <div
            v-for="p in domesticPlatforms"
            :key="p.id"
            class="platform-card"
            :class="{ selected: selectedPlatform?.id === p.id, configured: p.status === 'configured' }"
            @click="selectPlatform(p)"
          >
            <div class="pc-icon-wrap">
              <YdReliefIcon :icon="resolveAntIcon(aiProviderIconName(p.id))" size="sm" />
            </div>
            <div class="pc-info">
              <div class="pc-name">{{ p.name }}</div>
              <div class="pc-status">
                <a-tag v-if="p.status === 'configured'" color="success">已配置</a-tag>
                <a-tag v-else-if="p.status === 'guiding'" color="processing">引导中</a-tag>
                <a-tag v-else color="default">未配置</a-tag>
              </div>
            </div>
            <a-button type="link" size="small" class="pc-register" :href="p.registerUrl" target="_blank">
              去注册 <ExportOutlined />
            </a-button>
          </div>
        </div>
      </div>

      <!-- 国外平台 -->
      <div class="platform-section">
        <h3 class="section-label">
          <GlobalOutlined class="section-icon" />
          国外平台
        </h3>
        <div class="platform-grid">
          <div
            v-for="p in foreignPlatforms"
            :key="p.id"
            class="platform-card"
            :class="{ selected: selectedPlatform?.id === p.id, configured: p.status === 'configured' }"
            @click="selectPlatform(p)"
          >
            <div class="pc-icon-wrap">
              <YdReliefIcon :icon="resolveAntIcon(aiProviderIconName(p.id))" size="sm" />
            </div>
            <div class="pc-info">
              <div class="pc-name">{{ p.name }}</div>
              <div class="pc-status">
                <a-tag v-if="p.status === 'configured'" color="success">已配置</a-tag>
                <a-tag v-else-if="p.status === 'guiding'" color="processing">引导中</a-tag>
                <a-tag v-else color="default">未配置</a-tag>
              </div>
            </div>
            <a-button type="link" size="small" class="pc-register" :href="p.registerUrl" target="_blank">
              去注册 <ExportOutlined />
            </a-button>
          </div>
        </div>
      </div>

      <div class="step-actions">
        <a-button type="primary" size="large" :disabled="!selectedPlatform" @click="goStep(1)">
          我已注册，获取Key
        </a-button>
      </div>
    </div>

    <!-- 步骤2：填写API Key -->
    <div v-if="currentStep === 1" class="step-panel">
      <div class="config-header">
        <a-button type="text" @click="goStep(0)">
          <ArrowLeftOutlined /> 返回选择平台
        </a-button>
        <h2 class="step-title" style="margin-top: 12px">
          配置 {{ selectedPlatform?.name }}
          <YdReliefIcon
            v-if="selectedPlatform"
            :icon="resolveAntIcon(aiProviderIconName(selectedPlatform.id))"
            size="sm"
            class="config-icon"
          />
        </h2>
      </div>

      <a-card class="config-form-card" :bordered="false">
        <a-form :model="formData" layout="vertical" :label-col="{ span: 24 }" style="max-width: 600px">
          <a-form-item label="API Key" required>
            <a-input-password
              v-model:value="formData.apiKey"
              placeholder="请输入 API Key"
              :visibilityToggle="true"
            />
            <div class="form-tip">通常可以在平台的控制台 -> API 管理页面获取</div>
          </a-form-item>

          <a-form-item label="Base URL">
            <a-input v-model:value="formData.baseUrl" placeholder="自动填充默认值" />
            <div class="form-tip">如需使用代理或中转地址，请修改此地址</div>
          </a-form-item>

          <a-form-item label="选择模型" required>
            <template v-if="selectedPlatform?.id === 'nvidia' && nvidiaCategories.length">
              <a-select
                v-model:value="formData.modelCategory"
                placeholder="先选使用场景"
                style="width: 100%; margin-bottom: 8px"
                @change="(v) => onNvidiaCategoryChange(v as string)"
              >
                <a-select-option v-for="c in nvidiaCategories" :key="c.id" :value="c.id">
                  {{ c.label }}（{{ c.count }}）
                </a-select-option>
              </a-select>
              <a-select
                v-model:value="formData.model"
                placeholder="请选择模型"
                style="width: 100%"
                show-search
                :filter-option="filterModelOption"
              >
                <a-select-option
                  v-for="m in nvidiaModelsInCategory"
                  :key="m.id"
                  :value="m.id"
                >
                  {{ m.id }}
                </a-select-option>
              </a-select>
              <div v-if="selectedNvidiaModel" class="form-tip">
                {{ selectedNvidiaModel.description || selectedNvidiaModel.endpoint }}
                · 接口 {{ selectedNvidiaModel.endpoint }}
              </div>
              <a-collapse v-if="nvidiaCatalogNote" ghost style="margin-top: 12px">
                <a-collapse-panel key="all" :header="`查看全部 ${nvidiaTotalModels} 个 NVIDIA 模型（${nvidiaCategories.length} 类）`">
                  <div v-for="c in nvidiaCategories" :key="c.id" class="nvidia-cat-block">
                    <div class="nvidia-cat-title">{{ c.label }} · {{ c.count }}</div>
                    <div class="nvidia-cat-desc">{{ c.description }}</div>
                    <a-tag v-for="m in c.models" :key="m.id" class="nvidia-model-tag">{{ m.id }}</a-tag>
                  </div>
                  <p class="form-tip" style="margin-top: 8px">{{ nvidiaCatalogNote }}</p>
                </a-collapse-panel>
              </a-collapse>
            </template>
            <a-select
              v-else
              v-model:value="formData.model"
              placeholder="请选择要使用的模型"
              style="width: 100%"
            >
              <a-select-option
                v-for="m in availableModels"
                :key="m"
                :value="m"
              >{{ m }}</a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item>
            <div class="form-actions">
              <a-button
                type="primary"
                :loading="testing"
                :disabled="!formData.apiKey"
                @click="testConnection"
              >
                <ApiOutlined /> 测试连接
              </a-button>
              <a-button
                type="primary"
                ghost
                :loading="saving"
                :disabled="!formData.apiKey || !formData.model || testing"
                @click="saveConfig"
                style="margin-left: 12px"
              >
                <SaveOutlined /> 保存配置
              </a-button>
            </div>
          </a-form-item>
        </a-form>

        <!-- 测试结果 -->
        <a-alert
          v-if="testResult"
          :type="testResult.success ? 'success' : 'error'"
          :message="testResult.message"
          show-icon
          style="margin-top: 16px"
        />
      </a-card>
    </div>

    <!-- 步骤3：配置完成 -->
    <div v-if="currentStep === 2" class="step-panel">
      <a-result
        status="success"
        :title="`${selectedPlatform?.name} 配置成功！`"
        sub-title="AI大模型平台已成功接入，现在可以使用该平台的模型能力了。"
      >
        <template #icon>
          <CheckCircleFilled style="color: #722ed1; font-size: 72px" />
        </template>

        <template #extra>
          <div class="result-models">
            <h4>可用模型列表</h4>
            <a-table
              :dataSource="resultModels"
              :columns="modelColumns"
              :pagination="false"
              size="small"
              bordered
            />
          </div>
          <div class="result-actions">
            <a-button
              v-if="selectedPlatform?.id === 'nvidia'"
              type="primary"
              size="large"
              @click="goScenarioSwitch"
            >
              按场景切换模型
            </a-button>
            <a-button type="primary" size="large" @click="setDefaultModel">
              <StarOutlined /> 设为默认模型
            </a-button>
            <a-button size="large" @click="resetForm" style="margin-left: 12px">
              <PlusOutlined /> 继续添加其他平台
            </a-button>
            <a-button size="large" @click="goBackCenter" style="margin-left: 12px">
              <HomeOutlined /> 返回控制台
            </a-button>
          </div>
        </template>
      </a-result>
    </div>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { YdPage, YdReliefIcon } from '@/components/youding'
import { resolveAntIcon } from '@/constants/antIconMap'
import { aiProviderIconName } from '@/constants/iconCatalog'
import { apiGet, apiPost } from '@/utils/api'
import {
  SafetyCertificateOutlined,
  GlobalOutlined,
  ExportOutlined,
  ArrowLeftOutlined,
  ApiOutlined,
  SaveOutlined,
  CheckCircleFilled,
  StarOutlined,
  PlusOutlined,
  HomeOutlined,
} from '@ant-design/icons-vue'

const router = useRouter()
const currentStep = ref(0)

interface NvidiaModel {
  id: string
  endpoint?: string
  description?: string
  input_modes?: string[]
  role?: string
}

interface NvidiaCategory {
  id: string
  label: string
  description: string
  count: number
  models: NvidiaModel[]
}

interface Platform {
  id: string
  name: string
  region: 'domestic' | 'foreign'
  status: 'unconfigured' | 'configured' | 'guiding'
  registerUrl: string
  defaultBaseUrl: string
  models: string[]
}

const allPlatforms: Platform[] = [
  { id: 'deepseek', name: 'DeepSeek', region: 'domestic', status: 'unconfigured', registerUrl: 'https://platform.deepseek.com', defaultBaseUrl: 'https://api.deepseek.com', models: ['deepseek-chat', 'deepseek-coder', 'deepseek-reasoner'] },
  { id: 'baidu', name: '百度文心', region: 'domestic', status: 'unconfigured', registerUrl: 'https://yiyan.baidu.com', defaultBaseUrl: 'https://aip.baidubce.com', models: ['ERNIE-4.0', 'ERNIE-3.5', 'ERNIE-Speed'] },
  { id: 'aliyun', name: '阿里通义', region: 'domestic', status: 'unconfigured', registerUrl: 'https://tongyi.aliyun.com', defaultBaseUrl: 'https://dashscope.aliyuncs.com', models: ['qwen-max', 'qwen-plus', 'qwen-turbo'] },
  { id: 'bytedance', name: '字节豆包', region: 'domestic', status: 'unconfigured', registerUrl: 'https://www.volcengine.com/product/doubao', defaultBaseUrl: 'https://ark.cn-beijing.volces.com', models: ['doubao-pro-32k', 'doubao-lite-32k'] },
  { id: 'zhipu', name: '智谱GLM', region: 'domestic', status: 'unconfigured', registerUrl: 'https://open.bigmodel.cn', defaultBaseUrl: 'https://open.bigmodel.cn/api/paas', models: ['glm-4', 'glm-4v', 'glm-3-turbo'] },
  { id: 'moonshot', name: '月之暗面Kimi', region: 'domestic', status: 'unconfigured', registerUrl: 'https://kimi.moonshot.cn', defaultBaseUrl: 'https://api.moonshot.cn', models: ['moonshot-v1-8k', 'moonshot-v1-32k', 'moonshot-v1-128k'] },
  { id: 'lingyi', name: '零一万物', region: 'domestic', status: 'unconfigured', registerUrl: 'https://www.lingyiwanwu.com', defaultBaseUrl: 'https://api.lingyiwanwu.com', models: ['yi-34b-chat', 'yi-vl-plus'] },
  { id: 'siliconflow', name: '硅基流动', region: 'domestic', status: 'unconfigured', registerUrl: 'https://cloud.siliconflow.cn', defaultBaseUrl: 'https://api.siliconflow.cn', models: ['Qwen2-72B', 'DeepSeek-V3', 'glm-4-9b-chat'] },
  { id: 'minimax', name: 'MiniMax', region: 'domestic', status: 'unconfigured', registerUrl: 'https://www.minimax.com', defaultBaseUrl: 'https://api.minimax.chat', models: ['abab6.5s', 'abab5.5s'] },
  { id: 'iflytek', name: '讯飞星火', region: 'domestic', status: 'unconfigured', registerUrl: 'https://xinghuo.xfyun.cn', defaultBaseUrl: 'https://spark-api.xf-yun.com', models: ['spark-4.0', 'spark-3.5', 'spark-3.0'] },
  { id: 'openai', name: 'OpenAI', region: 'foreign', status: 'unconfigured', registerUrl: 'https://platform.openai.com', defaultBaseUrl: 'https://api.openai.com', models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'] },
  { id: 'anthropic', name: 'Anthropic Claude', region: 'foreign', status: 'unconfigured', registerUrl: 'https://console.anthropic.com', defaultBaseUrl: 'https://api.anthropic.com', models: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'] },
  { id: 'google', name: 'Google Gemini', region: 'foreign', status: 'unconfigured', registerUrl: 'https://ai.google.dev', defaultBaseUrl: 'https://generativelanguage.googleapis.com', models: ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-1.0-pro'] },
  { id: 'nvidia', name: 'NVIDIA NIM', region: 'foreign', status: 'unconfigured', registerUrl: 'https://build.nvidia.com/explore/discover', defaultBaseUrl: 'https://integrate.api.nvidia.com/v1', models: [] },
  { id: 'meta', name: 'Meta Llama', region: 'foreign', status: 'unconfigured', registerUrl: 'https://llama.meta.com', defaultBaseUrl: 'https://api.meta.ai', models: ['llama-3-70b', 'llama-3-8b'] },
]

const domesticPlatforms = computed(() => allPlatforms.filter(p => p.region === 'domestic'))
const foreignPlatforms = computed(() => allPlatforms.filter(p => p.region === 'foreign'))

const selectedPlatform = ref<Platform | null>(null)

const formData = ref({
  apiKey: '',
  baseUrl: '',
  model: '',
  modelCategory: 'article',
})

const nvidiaCategories = ref<NvidiaCategory[]>([])
const nvidiaCatalogNote = ref('')
const nvidiaTotalModels = ref(0)
const nvidiaDefaults = ref<Record<string, string>>({})
const nvidiaCatalogLoading = ref(false)

const nvidiaModelsInCategory = computed(() => {
  const cat = nvidiaCategories.value.find(c => c.id === formData.value.modelCategory)
  return cat?.models || []
})

const selectedNvidiaModel = computed(() =>
  nvidiaModelsInCategory.value.find(m => m.id === formData.value.model) || null,
)

function filterModelOption(input: string, option: any) {
  return String(option?.value || '').toLowerCase().includes(input.toLowerCase())
}

function onNvidiaCategoryChange(catId: string) {
  const def = nvidiaDefaults.value[catId]
  const cat = nvidiaCategories.value.find(c => c.id === catId)
  formData.value.model = def || cat?.models?.[0]?.id || ''
}

async function loadNvidiaCatalog() {
  nvidiaCatalogLoading.value = true
  try {
    const data = await apiGet<{ categories: NvidiaCategory[]; note?: string; total_models?: number; defaults?: Record<string, string> }>(
      '/super-admin/ai-config/nvidia/catalog',
    )
    nvidiaCategories.value = data?.categories || []
    nvidiaCatalogNote.value = data?.note || ''
    nvidiaTotalModels.value = data?.total_models || 0
    nvidiaDefaults.value = data?.defaults || {}
    onNvidiaCategoryChange(formData.value.modelCategory || 'article')
  } catch {
    message.warning('未能加载 NVIDIA 模型目录，请确认后端已配置 AI_NVIDIA_API_KEY')
  } finally {
    nvidiaCatalogLoading.value = false
  }
}

watch(selectedPlatform, (p) => {
  if (p?.id === 'nvidia') loadNvidiaCatalog()
})

const testing = ref(false)
const saving = ref(false)
const testResult = ref<{ success: boolean; message: string } | null>(null)

async function saveConfig() {
  if (!selectedPlatform.value) return
  const key = (formData.value.apiKey || '').trim()
  const base = (formData.value.baseUrl || selectedPlatform.value.defaultBaseUrl).trim()
  const model = (formData.value.model || '').trim()
  if (!key || !model) {
    message.error('请填写 API Key 并选择模型')
    return
  }
  saving.value = true
  try {
    await apiPost('/super-admin/ai-config/providers', {
      name: selectedPlatform.value.name,
      provider_type: selectedPlatform.value.id,
      api_key: key,
      base_url: base,
      default_model: model,
      is_active: true,
      is_default: selectedPlatform.value.id === 'nvidia',
    })
    selectedPlatform.value.status = 'configured'
    message.success(`${selectedPlatform.value.name} 已保存`)
    goStep(2)
  } catch (err: any) {
    message.error(err?.message || '保存失败，请检查权限或网络')
  } finally {
    saving.value = false
  }
}

function goScenarioSwitch() {
  router.push('/admin/ai-center/scenario-models')
}

function selectPlatform(p: Platform) {
  selectedPlatform.value = p
  formData.value = { apiKey: '', baseUrl: p.defaultBaseUrl, model: '', modelCategory: 'article' }
  testResult.value = null
  if (p.id === 'nvidia') loadNvidiaCatalog()
}

const availableModels = computed(() => selectedPlatform.value?.models || [])

function goStep(step: number) {
  currentStep.value = step
  if (step === 0) {
    testResult.value = null
  }
}

function testConnection() {
  testing.value = true
  testResult.value = null
  const key = (formData.value.apiKey || '').trim()
  const base = (formData.value.baseUrl || '').trim()
  if (!key || !base) {
    testing.value = false
    testResult.value = { success: false, message: '请先填写 API Key 与 Base URL' }
    return
  }
  fetch('/api/v1/super-admin/ai-config/test', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('token') || ''}` },
    body: JSON.stringify({
      platform: selectedPlatform.value?.id,
      api_key: key,
      base_url: base,
      model: (formData.value.model || availableModels.value[0] || '').trim(),
    }),
  })
    .then(async (r) => {
      const j = await r.json().catch(() => ({}))
      const healthy = j?.data?.healthy === true
      testResult.value = r.ok && (j.code === 0 || j.success) && healthy
        ? { success: true, message: `连接成功：${selectedPlatform.value?.name} API 响应正常（${j?.data?.latency_ms ?? '?'}ms）。` }
        : { success: false, message: j.message || j?.data?.message || '连接失败，请检查 API Key 和 Base URL' }
    })
    .catch(() => {
      testResult.value = { success: false, message: '网络错误或测试接口不可用' }
    })
    .finally(() => { testing.value = false })
}

const resultModels = computed(() => {
  if (!selectedPlatform.value) return []
  if (selectedPlatform.value.id === 'nvidia' && nvidiaCategories.value.length) {
    return nvidiaCategories.value.flatMap(c =>
      c.models.map((m, i) => ({
        key: `${c.id}-${m.id}`,
        category: c.label,
        name: m.id,
        status: m.id === formData.value.model ? '已选默认' : '可用',
        latency: m.endpoint || '/v1/chat/completions',
      })),
    )
  }
  return selectedPlatform.value.models.map((m, i) => ({
    key: i,
    category: '—',
    name: m,
    status: i === 0 ? '已启用' : '可用',
    latency: '—',
  }))
})

const modelColumns = [
  { title: '场景', dataIndex: 'category', key: 'category', width: 140 },
  { title: '模型 ID', dataIndex: 'name', key: 'name' },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '接口', dataIndex: 'latency', key: 'latency', width: 160 },
]

function setDefaultModel() {
  // mock
}

function resetForm() {
  selectedPlatform.value = null
  formData.value = { apiKey: '', baseUrl: '', model: '', modelCategory: 'article' }
  nvidiaCategories.value = []
  testResult.value = null
  currentStep.value = 0
}

function goBackCenter() {
  router.push('/admin/ai-center')
}
</script>

<style scoped>
.provider-setup {
  max-width: 960px;
  margin: 0 auto;
  padding: 8px 0;
}
.setup-steps {
  margin-bottom: 36px;
}
:deep(.ant-steps-item-title) {
  font-weight: 500;
}
:deep(.ant-steps-item-active .ant-steps-item-title) {
  color: #722ed1;
}

.step-panel {
  animation: fadeIn 0.35s ease;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.step-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 6px;
}
.step-desc {
  color: #6b7280;
  font-size: 0.9rem;
  margin-bottom: 28px;
}

/* Platform sections */
.platform-section {
  margin-bottom: 32px;
}
.section-label {
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.section-icon {
  color: #722ed1;
}

.platform-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}
.platform-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 12px;
  border: 1.5px solid #e5e7eb;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}
.platform-card:hover {
  border-color: #a78bfa;
  box-shadow: 0 4px 16px rgba(114, 46, 209, 0.1);
}
.platform-card.selected {
  border-color: #722ed1;
  background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
  box-shadow: 0 4px 20px rgba(114, 46, 209, 0.15);
}
.platform-card.configured {
  border-color: #52c41a;
  background: #f6ffed;
}
.pc-icon-wrap,
.config-icon {
  font-size: 2rem;
  line-height: 1;
  flex-shrink: 0;
}
.pc-info {
  flex: 1;
  min-width: 0;
}
.pc-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}
.pc-status {
  line-height: 1;
}
.pc-register {
  position: absolute;
  top: 6px;
  right: 6px;
  font-size: 0.7rem;
  padding: 0;
  height: auto;
}

/* Config form */
.config-header {
  margin-bottom: 24px;
}
.config-icon-inline {
  margin-left: 8px;
}
.config-form-card {
  border-radius: 12px;
  background: #fafafa;
}
.form-tip {
  font-size: 0.75rem;
  color: #9ca3af;
  margin-top: 4px;
}
.nvidia-cat-block {
  margin-bottom: 16px;
}
.nvidia-cat-title {
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 4px;
}
.nvidia-cat-desc {
  font-size: 12px;
  color: #888;
  margin-bottom: 8px;
}
.nvidia-model-tag {
  margin: 0 6px 6px 0;
  font-size: 11px;
}
.form-actions {
  display: flex;
  align-items: center;
}

/* Result */
.result-models {
  max-width: 500px;
  margin: 0 auto 24px;
  text-align: left;
}
.result-models h4 {
  font-size: 0.95rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 12px;
}
.result-actions {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 12px;
}

@media (max-width: 1200px) {
  .platform-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
@media (max-width: 768px) {
  .platform-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .step-title {
    font-size: 1.15rem;
  }
}
@media (max-width: 480px) {
  .platform-grid {
    grid-template-columns: 1fr;
  }
}
</style>
