﻿﻿﻿﻿﻿﻿﻿﻿<template>
  <YdPage title="模型管理" subtitle="管理35大AI模型平台 — 配置API Key即可启用对应模型" surface="elevated">
    <template #actions>
      <a-button type="primary" @click="showAddModal = true">
        <PlusOutlined />
        添加模型
      </a-button>
      <a-button
        v-if="configuredCount > 0"
        type="default"
        size="small"
        :loading="batchTesting"
        @click="batchTestAll"
        style="margin-left: 8px;"
      >
        <template #icon><ApiOutlined /></template>
        全部检测
      </a-button>
    </template>
  <div class="models-page">

    <!-- AI引擎状态横幅 -->
    <div class="ai-status-banner">
      <div class="banner-item">
        <CheckCircleFilled v-if="configuredCount > 0" class="banner-icon banner-icon-success" />
        <ExclamationCircleFilled v-else class="banner-icon banner-icon-warning" />
        <span class="banner-text">已配置 <strong>{{ configuredCount }}</strong> / {{ platformList.length }} 个平台</span>
      </div>
      <div class="banner-item">
        <span class="banner-text">可用模型 <strong>{{ configuredModels }}</strong> 个</span>
      </div>
      <div class="banner-item" v-if="unconfiguredCount > 0">
        <span class="banner-text banner-text-warn">还有 <strong>{{ unconfiguredCount }}</strong> 个平台未配置API Key</span>
      </div>
      <div class="banner-item" v-else>
        <span class="banner-text banner-text-all">全部平台已配置</span>
      </div>
    </div>

    <!-- 35大平台模型卡片 -->
    <div class="section-title">全部模型平台（35家）</div>
    <div class="model-grid">
      <div
        class="model-card"
        v-for="platform in platformList"
        :key="platform.id"
        :class="{ 'card-configured': platform.configured }"
      >
        <div class="card-header">
          <div class="model-icon" :class="{ 'icon-configured': platform.configured }">
            <component :is="platform.icon" />
          </div>
          <div class="model-header-info">
            <h3 class="model-name">{{ platform.name }}</h3>
            <span class="model-type">{{ platform.provider }}</span>
          </div>
          <a-tooltip v-if="platform.configured && platform.healthCheck !== undefined" :title="healthTooltip(platform)">
            <a-badge
              :status="platform.healthCheck?.healthy ? 'success' : 'error'"
              :text="platform.healthCheck?.healthy ? '正常' : '异常'"
            />
          </a-tooltip>
          <a-badge
            v-else
            :status="platform.configured ? 'success' : 'default'"
            :text="platform.configured ? '已配置' : '未配置'"
          />
        </div>
        <div class="card-body">
          <p class="model-desc">{{ platform.description }}</p>
          <div class="model-meta">
            <span class="meta-item">模型: {{ platform.models }}</span>
            <span class="meta-item">上下文: {{ platform.contextLength }}</span>
            <span class="meta-item">价格: {{ platform.price }}</span>
          </div>
        </div>
        <div class="card-footer">
          <a-button
            v-if="platform.configured"
            size="small"
            :loading="platform._testing"
            @click="testPlatform(platform)"
          >
            <template #icon><ApiOutlined /></template>
            检测
          </a-button>
          <a-button
            size="small"
            type="link"
            @click="openGetKeyLink(platform.getKeyUrl)"
          >
            获取Key
            <LinkOutlined />
          </a-button>
          <a-button
            size="small"
            :disabled="!platform.configured"
            @click="editModel(platform)"
          >
            配置
          </a-button>
          <a-button
            size="small"
            :type="platform.enabled ? 'default' : 'primary'"
            :disabled="!platform.configured"
            @click="toggleModel(platform)"
          >
            {{ platform.enabled ? '禁用' : '启用' }}
          </a-button>
        </div>
      </div>
    </div>

    <a-modal
      v-model:open="showAddModal"
      title="添加AI模型"
      :footer="null"
    >
      <a-form
        :model="modelForm"
        :rules="modelRules"
        ref="modelFormRef"
      >
        <a-form-item label="模型名称" name="name">
          <a-input
            v-model:value="modelForm.name"
            placeholder="请输入模型名称"
          />
        </a-form-item>
        <a-form-item label="平台" name="provider">
          <a-select v-model:value="modelForm.provider" placeholder="选择模型平台">
            <a-select-option value="nvidia">NVIDIA NIM</a-select-option>
            <a-select-option value="openai">OpenAI</a-select-option>
            <a-select-option value="deepseek">DeepSeek</a-select-option>
            <a-select-option value="baidu">百度文心一言</a-select-option>
            <a-select-option value="baidu_qianfan">ERNIE百度千帆</a-select-option>
            <a-select-option value="aliyun">阿里通义千问</a-select-option>
            <a-select-option value="aliyun_qwen">Qwen阿里百炼</a-select-option>
            <a-select-option value="byte">字节豆包</a-select-option>
            <a-select-option value="byteplus">BytePlus</a-select-option>
            <a-select-option value="volcengine">火山引擎</a-select-option>
            <a-select-option value="zhipu">智谱GLM</a-select-option>
            <a-select-option value="zai">Z.ai</a-select-option>
            <a-select-option value="kimi">Kimi</a-select-option>
            <a-select-option value="kimi_global">Kimi Global</a-select-option>
            <a-select-option value="01wanwu">零一万物</a-select-option>
            <a-select-option value="siliconflow">硅基流动</a-select-option>
            <a-select-option value="minimax">MiniMax</a-select-option>
            <a-select-option value="minimax_cn">MiniMax CN</a-select-option>
            <a-select-option value="minimax_en">MiniMax EN</a-select-option>
            <a-select-option value="xunfei">讯飞星火</a-select-option>
            <a-select-option value="anthropic">Anthropic</a-select-option>
            <a-select-option value="google">Google Gemini</a-select-option>
            <a-select-option value="meta">Meta Llama</a-select-option>
            <a-select-option value="meta_ai">Meta AI</a-select-option>
            <a-select-option value="xiaomi">Xiaomi</a-select-option>
            <a-select-option value="tencent_hunyuan">Hunyuan腾讯混元</a-select-option>
            <a-select-option value="stepfun">Stepfun阶跃星辰</a-select-option>
            <a-select-option value="ucloud">UCloud优云智算</a-select-option>
            <a-select-option value="xai">xAI Grok</a-select-option>
            <a-select-option value="perplexity">Perplexity</a-select-option>
            <a-select-option value="mistral">Mistral AI</a-select-option>
            <a-select-option value="cohere">Cohere</a-select-option>
            <a-select-option value="groq">Groq</a-select-option>
            <a-select-option value="together">Together AI</a-select-option>
            <a-select-option value="agnes">Agnes AI</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="模型类型" name="type">
          <a-select v-model:value="modelForm.type">
            <a-select-option value="chat">对话模型</a-select-option>
            <a-select-option value="completion">补全模型</a-select-option>
            <a-select-option value="embedding">嵌入模型</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="版本号" name="version">
          <a-input
            v-model:value="modelForm.version"
            placeholder="请输入版本号"
          />
        </a-form-item>
        <a-form-item label="最大Token" name="maxTokens">
          <a-input-number
            v-model:value="modelForm.maxTokens"
            :min="100"
            :max="2000000"
          />
        </a-form-item>
        <a-form-item label="模型描述" name="description">
          <a-textarea
            v-model:value="modelForm.description"
            placeholder="请输入模型描述"
            :rows="3"
          />
        </a-form-item>
        <div class="modal-footer">
          <a-button @click="showAddModal = false">取消</a-button>
          <a-button type="primary" @click="submitModelForm">确定</a-button>
        </div>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="showConfigModal"
      :title="`配置 ${configPlatform?.name || ''}`"
      ok-text="保存并启用"
      :confirm-loading="configSaving"
      @ok="handleConfigOk"
    >
      <p class="config-modal-tip">
        在对应平台获取 API Key 后粘贴保存，即可启用该模型平台。
      </p>
      <a-form layout="vertical">
        <a-form-item label="API Key" required>
          <a-input-password v-model:value="configApiKey" placeholder="粘贴 API Key" />
        </a-form-item>
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
          <a-button
            type="default"
            size="small"
            :loading="configTesting"
            :disabled="!configApiKey.trim()"
            @click="testConfigConnection"
          >
            <template #icon><ApiOutlined /></template>
            测试连接
          </a-button>
          <span v-if="configTestResult" :style="{ color: configTestResult.healthy ? '#10b981' : '#ef4444', fontSize: '13px' }">
            {{ configTestResult.healthy ? `连接正常 (${configTestResult.latency_ms}ms)` : `连接失败: ${configTestResult.message}` }}
          </span>
        </div>
        <a-button type="link" size="small" @click="openGetKeyLink(configPlatform?.getKeyUrl || '')">
          前往平台获取 Key
          <LinkOutlined />
        </a-button>
      </a-form>
    </a-modal>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import { apiGet, apiPost } from '@/utils/api';
import {
  PlusOutlined,
  ExperimentOutlined,
  LinkOutlined,
  CheckCircleFilled,
  ExclamationCircleFilled,
  ThunderboltOutlined,
  RocketOutlined,
  FireOutlined,
  BulbOutlined,
  GlobalOutlined,
  CloudOutlined,
  ApiOutlined,
  StarOutlined,
  AimOutlined,
  CodeOutlined,
  SearchOutlined,
  DatabaseOutlined,
  BellOutlined,
  MessageOutlined,
  BankOutlined,
  AlertOutlined,
  ShakeOutlined,
  CompassOutlined,
  BookOutlined,
  LockOutlined,
  IeOutlined,
  CrownOutlined,
  DownOutlined,
  LeftOutlined,
  TrophyOutlined,
  WalletOutlined,
  GiftOutlined,
  TagOutlined,
  HeartOutlined,
  ThunderboltFilled,
  RocketFilled,
  FireFilled,
  BulbFilled,
  GoldFilled,
  CloudFilled,
  StarFilled,
  DatabaseFilled,
} from '@ant-design/icons-vue';
import FingerprintOutlined from '@ant-design/icons-vue';
import SparklesFilled from '@ant-design/icons-vue';
import SparklesOutlined from '@ant-design/icons-vue';

interface HealthCheckResult {
  healthy: boolean;
  latency_ms?: number;
  message?: string;
}

interface ModelPlatform {
  id: number;
  name: string;
  provider: string;
  models: string;
  contextLength: string;
  price: string;
  description: string;
  configured: boolean;
  enabled: boolean;
  icon: any;
  getKeyUrl: string;
  healthCheck?: HealthCheckResult;
  _testing?: boolean;
}

const showAddModal = ref(false);
const showConfigModal = ref(false);
const configPlatform = ref<ModelPlatform | null>(null);
const configApiKey = ref('');
const configSaving = ref(false);
const configTesting = ref(false);
const configTestResult = ref<HealthCheckResult | null>(null);
const batchTesting = ref(false);

const providerTypeByName: Record<string, string> = {
  'NVIDIA NIM': 'nvidia',
  DeepSeek: 'deepseek',
  OpenAI: 'openai',
  '百度文心一言': 'baidu',
  '阿里通义千问': 'aliyun',
  '字节豆包': 'byte',
  '智谱GLM': 'zhipu',
  Kimi: 'kimi',
  '零一万物': '01wanwu',
  '硅基流动': 'siliconflow',
  MiniMax: 'minimax',
  '讯飞星火': 'xunfei',
  Anthropic: 'anthropic',
  'Google Gemini': 'google',
  'Meta Llama': 'meta',
  Xiaomi: 'xiaomi',
  'MiniMax CN': 'minimax_cn',
  'MiniMax EN': 'minimax_en',
  'GLM智谱': 'zhipu',
  'Kimi Global': 'kimi_global',
  '火山引擎': 'volcengine',
  'ERNIE百度千帆': 'baidu_qianfan',
  'Qwen阿里百炼': 'aliyun_qwen',
  'Hunyuan腾讯混元': 'tencent_hunyuan',
  'Stepfun阶跃星辰': 'stepfun',
  'UCloud优云智算': 'ucloud',
  'Z.ai': 'zai',
  'BytePlus': 'byteplus',
  'xAI Grok': 'xai',
  'Meta AI': 'meta_ai',
  Perplexity: 'perplexity',
  'Mistral AI': 'mistral',
  Cohere: 'cohere',
  Groq: 'groq',
  'Together AI': 'together',
  'Agnes AI': 'agnes',
};

const modelForm = reactive({
  name: '',
  provider: 'openai',
  type: 'chat',
  version: '',
  maxTokens: 4096,
  description: '',
});

const modelRules = {
  name: [{ required: true, message: '请输入模型名称' }],
  type: [{ required: true, message: '请选择模型类型' }],
};

// 15大模型平台数据
const platformList = ref<ModelPlatform[]>([
  {
    id: 1,
    name: 'NVIDIA NIM',
    provider: 'NVIDIA',
    models: 'Claude/Llama/Mistral/GLM/Qwen + Cosmos 视频（123+）',
    contextLength: '128K+',
    price: '免费额度以 NVIDIA 控制台为准',
    description: 'NVIDIA NIM：118 个对话/嵌入模型 + Cosmos 文生视频/图生视频/风格转换，按场景分类见模型配置页',
    configured: true,
    enabled: true,
    icon: ThunderboltFilled,
    getKeyUrl: 'https://build.nvidia.com/explore/discover',
  },
  {
    id: 2,
    name: 'DeepSeek',
    provider: '深度求索',
    models: 'DeepSeek-V3, DeepSeek-R1, DeepSeek-Coder',
    contextLength: '64K',
    price: '￥0.001/1K tokens',
    description: 'DeepSeek自研大模型，国内API访问快速稳定，Chat/Reasoner/Coder三模型覆盖全场景',
    configured: false,
    enabled: false,
    icon: RocketFilled,
    getKeyUrl: 'https://platform.deepseek.com/api_keys',
  },
  {
    id: 3,
    name: 'OpenAI',
    provider: 'OpenAI',
    models: 'GPT-4o, GPT-4 Turbo, GPT-3.5',
    contextLength: '128K',
    price: '$0.01/1K tokens',
    description: 'OpenAI最新一代大语言模型，支持多模态输入，生态系统最为完善',
    configured: false,
    enabled: false,
    icon: SparklesFilled,
    getKeyUrl: 'https://platform.openai.com/api-keys',
  },
  {
    id: 4,
    name: '百度文心一言',
    provider: '百度',
    models: 'ERNIE 4.0, ERNIE Speed, ERNIE Lite',
    contextLength: '128K',
    price: '￥0.008/1K tokens',
    description: '百度文心大模型，中文理解能力出色，千帆平台生态丰富',
    configured: false,
    enabled: false,
    icon: GlobalOutlined,
    getKeyUrl: 'https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application',
  },
  {
    id: 5,
    name: '阿里通义千问',
    provider: '阿里巴巴',
    models: 'Qwen-Max, Qwen-Plus, Qwen-Turbo',
    contextLength: '128K',
    price: '￥0.006/1K tokens',
    description: '阿里自研通义千问大模型，开源Qwen系列，多语言能力优秀',
    configured: false,
    enabled: false,
    icon: DownOutlined,
    getKeyUrl: 'https://dashscope.console.aliyun.com/apiKey',
  },
  {
    id: 6,
    name: '字节豆包',
    provider: '字节跳动',
    models: 'Doubao-Pro, Doubao-Lite, Seed 2.0',
    contextLength: '64K',
    price: '￥0.005/1K tokens',
    description: '字节跳动自研大模型，中文能力优秀，火山引擎生态接入便捷',
    configured: false,
    enabled: false,
    icon: MessageOutlined,
    getKeyUrl: 'https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey',
  },
  {
    id: 7,
    name: '智谱GLM',
    provider: '智谱AI',
    models: 'GLM-4-Plus, GLM-4-Flash, GLM-4-Long',
    contextLength: '128K',
    price: '￥0.005/1K tokens',
    description: '智谱AI大模型，数学推理能力强，支持超长上下文，API生态完善',
    configured: false,
    enabled: false,
    icon: BankOutlined,
    getKeyUrl: 'https://open.bigmodel.cn/usercenter/apikeys',
  },
  {
    id: 8,
    name: 'Kimi',
    provider: '月之暗面',
    models: 'Moonshot-v1-8k, Moonshot-v1-32k, Moonshot-v1-128k',
    contextLength: '128K',
    price: '￥0.012/1K tokens',
    description: '月之暗面Kimi大模型，超长上下文处理能力，文件理解能力突出',
    configured: false,
    enabled: false,
    icon: FireFilled,
    getKeyUrl: 'https://platform.moonshot.cn/console/api-keys',
  },
  {
    id: 9,
    name: '零一万物',
    provider: '零一万物',
    models: 'Yi-Large, Yi-Medium, Yi-Vision',
    contextLength: '32K',
    price: '￥0.004/1K tokens',
    description: '零一万物李开复团队打造，中文和英文能力均衡，性价比高',
    configured: false,
    enabled: false,
    icon: FingerprintOutlined,
    getKeyUrl: 'https://platform.lingyiwanwu.com/apikeys',
  },
  {
    id: 10,
    name: '硅基流动',
    provider: 'SiliconFlow',
    models: 'DeepSeek-V3, Qwen2.5, Yi-1.5, Llama 3.1',
    contextLength: '128K',
    price: '￥0.001/1K tokens',
    description: '硅基流动一站式模型托管平台，聚合多厂商模型，统一API接入，性价比极高',
    configured: false,
    enabled: false,
    icon: DatabaseOutlined,
    getKeyUrl: 'https://cloud.siliconflow.cn/account/ak',
  },
  {
    id: 11,
    name: 'MiniMax',
    provider: 'MiniMax',
    models: 'abab6.5s, abab6.5, abab5.5',
    contextLength: '128K',
    price: '￥0.005/1K tokens',
    description: 'MiniMax海螺AI，多模态理解能力强，语音合成能力出色',
    configured: false,
    enabled: false,
    icon: AlertOutlined,
    getKeyUrl: 'https://platform.minimaxi.com/user-center/basic-information/interface-key',
  },
  {
    id: 12,
    name: '讯飞星火',
    provider: '科大讯飞',
    models: 'Spark 4.0 Ultra, Spark Max, Spark Lite',
    contextLength: '32K',
    price: '￥0.03/1K tokens',
    description: '科大讯飞星火大模型，语音交互能力领先，多模态理解能力强',
    configured: false,
    enabled: false,
    icon: BellOutlined,
    getKeyUrl: 'https://console.xfyun.cn/services/cbm',
  },
  {
    id: 13,
    name: 'Anthropic',
    provider: 'Anthropic',
    models: 'Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku',
    contextLength: '200K',
    price: '$0.015/1K tokens',
    description: 'Anthropic Claude系列，安全性行业领先，长上下文推理能力极强',
    configured: false,
    enabled: false,
    icon: IeOutlined,
    getKeyUrl: 'https://console.anthropic.com/settings/keys',
  },
  {
    id: 14,
    name: 'Google Gemini',
    provider: 'Google',
    models: 'Gemini 2.0 Flash, Gemini 1.5 Pro, Gemini 1.5 Flash',
    contextLength: '1000K',
    price: '$0.007/1K tokens',
    description: 'Google Gemini多模态大模型，超长上下文，原生多模态能力',
    configured: false,
    enabled: false,
    icon: CloudFilled,
    getKeyUrl: 'https://aistudio.google.com/apikey',
  },
  {
    id: 15,
    name: 'Meta Llama',
    provider: 'Meta',
    models: 'Llama 3.1 70B, Llama 3.1 8B, Llama 3 405B',
    contextLength: '128K',
    price: '免费（开源）',
    description: 'Meta开源大模型，可通过NVIDIA NIM、硅基流动、Ollama等平台托管使用',
    configured: false,
    enabled: false,
    icon: StarFilled,
    getKeyUrl: 'https://build.nvidia.com/meta',
  },
  {
    id: 16,
    name: 'Xiaomi',
    provider: '小米',
    models: 'Xiaomi AI, XiaoAI',
    contextLength: '64K',
    price: '免费额度以平台为准',
    description: '小米自研大模型，中文能力优秀，智能家居场景深度整合',
    configured: false,
    enabled: false,
    icon: GiftOutlined,
    getKeyUrl: 'https://platform.xiaomimimo.com',
  },
  {
    id: 17,
    name: '火山引擎',
    provider: '字节跳动',
    models: 'Doubao-Pro, Doubao-Lite, Seed 2.0',
    contextLength: '64K',
    price: '首月9.9元',
    description: '字节跳动火山引擎AI平台，接入豆包系列大模型，性价比高',
    configured: false,
    enabled: false,
    icon: ApiOutlined,
    getKeyUrl: 'https://www.volcengine.com',
  },
  {
    id: 18,
    name: 'ERNIE百度千帆',
    provider: '百度',
    models: 'ERNIE 4.0, ERNIE Speed, ERNIE Lite',
    contextLength: '128K',
    price: '￥0.008/1K tokens',
    description: '百度千帆大模型平台，ERNIE系列模型，中文理解能力出色',
    configured: false,
    enabled: false,
    icon: BookOutlined,
    getKeyUrl: 'https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application',
  },
  {
    id: 19,
    name: 'Qwen阿里百炼',
    provider: '阿里巴巴',
    models: 'Qwen-Max, Qwen-Plus, Qwen-Turbo',
    contextLength: '128K',
    price: '￥0.006/1K tokens',
    description: '阿里百炼大模型平台，Qwen系列模型，多语言能力优秀',
    configured: false,
    enabled: false,
    icon: WalletOutlined,
    getKeyUrl: 'https://bailian.console.aliyun.com',
  },
  {
    id: 20,
    name: 'Hunyuan腾讯混元',
    provider: '腾讯',
    models: 'Hunyuan-Lite, Hunyuan-Standard, Hunyuan-Pro',
    contextLength: '128K',
    price: '￥0.005/1K tokens',
    description: '腾讯混元大模型，中文能力优秀，企业级服务完善',
    configured: false,
    enabled: false,
    icon: LeftOutlined,
    getKeyUrl: 'https://console.cloud.tencent.com',
  },
  {
    id: 21,
    name: 'Stepfun阶跃星辰',
    provider: '阶跃星辰',
    models: 'Step-1, Step-2, Step-Coder',
    contextLength: '64K',
    price: '￥0.003/1K tokens',
    description: '阶跃星辰自研大模型，代码能力强，性价比极高',
    configured: false,
    enabled: false,
    icon: ShakeOutlined,
    getKeyUrl: 'https://www.stepfun.com',
  },
  {
    id: 22,
    name: 'UCloud优云智算',
    provider: '优云智算',
    models: 'UCloud-LLM, UCloud-Coder, UCloud-Embedding',
    contextLength: '64K',
    price: '按需计费',
    description: 'UCloud优云智算平台，一站式AI算力服务',
    configured: false,
    enabled: false,
    icon: DatabaseFilled,
    getKeyUrl: 'https://passport.compshare.cn',
  },
  {
    id: 23,
    name: 'Z.ai',
    provider: 'Z.ai',
    models: 'GLM-5.1, GLM-4-Flash',
    contextLength: '128K',
    price: '￥0.005/1K tokens',
    description: 'Z.ai智谱开放平台，GLM系列大模型，数学推理能力强',
    configured: false,
    enabled: false,
    icon: BankOutlined,
    getKeyUrl: 'https://api.z.ai',
  },
  {
    id: 24,
    name: 'MiniMax CN',
    provider: 'MiniMax',
    models: 'abab6.5s, abab6.5, abab5.5',
    contextLength: '128K',
    price: '￥0.005/1K tokens',
    description: 'MiniMax海螺AI中国版，多模态理解能力强',
    configured: false,
    enabled: false,
    icon: SparklesOutlined,
    getKeyUrl: 'https://www.minimax.cn',
  },
  {
    id: 25,
    name: 'MiniMax EN',
    provider: 'MiniMax',
    models: 'abab6.5s, abab6.5',
    contextLength: '128K',
    price: '$0.008/1K tokens',
    description: 'MiniMax国际版，英文能力优秀',
    configured: false,
    enabled: false,
    icon: BulbOutlined,
    getKeyUrl: 'https://www.minimax.io',
  },
  {
    id: 26,
    name: 'Kimi Global',
    provider: '月之暗面',
    models: 'Moonshot-v1-8k, Moonshot-v1-32k',
    contextLength: '128K',
    price: '$0.01/1K tokens',
    description: 'Kimi国际版，超长上下文处理能力',
    configured: false,
    enabled: false,
    icon: LockOutlined,
    getKeyUrl: 'https://platform.kimi.ai',
  },
  {
    id: 27,
    name: 'xAI Grok',
    provider: 'xAI',
    models: 'Grok-1, Grok-2',
    contextLength: '128K',
    price: '$0.015/1K tokens',
    description: '马斯克旗下xAI的Grok模型，实时信息能力强',
    configured: false,
    enabled: false,
    icon: ApiOutlined,
    getKeyUrl: 'https://console.x.ai',
  },
  {
    id: 28,
    name: 'Meta AI',
    provider: 'Meta',
    models: 'Meta AI, Llama 3.1',
    contextLength: '128K',
    price: '免费',
    description: 'Meta官方AI服务，直接调用Llama系列模型',
    configured: false,
    enabled: false,
    icon: RocketFilled,
    getKeyUrl: 'https://ai.meta.com',
  },
  {
    id: 29,
    name: 'Perplexity',
    provider: 'Perplexity',
    models: 'pplx-7b, pplx-70b, pplx-online',
    contextLength: '64K',
    price: '$0.02/1K tokens',
    description: 'Perplexity AI，实时搜索+大模型，信息获取能力强',
    configured: false,
    enabled: false,
    icon: CompassOutlined,
    getKeyUrl: 'https://www.perplexity.ai',
  },
  {
    id: 30,
    name: 'Mistral AI',
    provider: 'Mistral',
    models: 'Mistral Large 3, Mistral 7B, Mistral 8x7B',
    contextLength: '128K',
    price: '$0.01/1K tokens',
    description: 'Mistral AI，欧洲领先大模型公司，高性能低延迟',
    configured: false,
    enabled: false,
    icon: TrophyOutlined,
    getKeyUrl: 'https://mistral.ai',
  },
  {
    id: 31,
    name: 'Cohere',
    provider: 'Cohere',
    models: 'Command R+, Command R, Embed',
    contextLength: '128K',
    price: '$0.015/1K tokens',
    description: 'Cohere大模型，企业级AI解决方案，RAG能力优秀',
    configured: false,
    enabled: false,
    icon: CrownOutlined,
    getKeyUrl: 'https://cohere.com',
  },
  {
    id: 32,
    name: 'Groq',
    provider: 'Groq',
    models: 'Llama 3.1, Mixtral, Gemma',
    contextLength: '128K',
    price: '$0.005/1K tokens',
    description: 'Groq超快推理引擎，LLM推理速度行业领先',
    configured: false,
    enabled: false,
    icon: TagOutlined,
    getKeyUrl: 'https://groq.com',
  },
  {
    id: 33,
    name: 'Together AI',
    provider: 'Together',
    models: 'Llama 3.1, Mixtral, Qwen',
    contextLength: '128K',
    price: '$0.008/1K tokens',
    description: 'Together AI，开源模型托管平台，性价比高',
    configured: false,
    enabled: false,
    icon: GoldFilled,
    getKeyUrl: 'https://www.together.ai',
  },
  {
    id: 34,
    name: 'Agnes AI',
    provider: 'Agnes',
    models: 'Agnes-7B, Agnes-70B',
    contextLength: '64K',
    price: '￥0.004/1K tokens',
    description: 'Agnes AI，中文大模型，专注垂直领域应用',
    configured: false,
    enabled: false,
    icon: HeartOutlined,
    getKeyUrl: 'https://platform.agnes-ai.com',
  },
  {
    id: 35,
    name: 'BytePlus',
    provider: '字节跳动',
    models: 'Doubao-Pro, Doubao-Lite',
    contextLength: '64K',
    price: '按需计费',
    description: 'BytePlus字节跳动海外云服务，接入豆包模型',
    configured: false,
    enabled: false,
    icon: GlobalOutlined,
    getKeyUrl: 'https://www.byteplus.com',
  },
]);

const configuredCount = computed(() => platformList.value.filter(p => p.configured).length);
const unconfiguredCount = computed(() => platformList.value.length - configuredCount.value);
const configuredModels = computed(() => platformList.value.filter(p => p.configured).length * 3);

const editModel = (platform: ModelPlatform) => {
  configPlatform.value = platform;
  configApiKey.value = '';
  configTestResult.value = null;
  showConfigModal.value = true;
};

async function handleConfigOk() {
  const platform = configPlatform.value;
  const key = configApiKey.value.trim();
  if (!platform) return Promise.reject();
  if (!key) {
    message.warning('请填写 API Key');
    return Promise.reject();
  }
  await savePlatformConfig();
}

async function savePlatformConfig() {
  const platform = configPlatform.value;
  const key = configApiKey.value.trim();
  if (!platform || !key) return;
  configSaving.value = true;
  try {
    await apiPost('/super-admin/ai-config/providers', {
      name: platform.name,
      provider_type: providerTypeByName[platform.name] || platform.name.toLowerCase(),
      api_key: key,
      enabled: true,
    });
    platform.configured = true;
    platform.enabled = true;
    showConfigModal.value = false;
    message.success(`${platform.name} 已配置并启用`);
  } catch {
    message.error('保存失败，请检查 API Key 或权限');
    return Promise.reject();
  } finally {
    configSaving.value = false;
  }
}

const toggleModel = (platform: ModelPlatform) => {
  if (!platform.configured) {
    message.warn('请先配置API Key');
    return;
  }
  platform.enabled = !platform.enabled;
  message.success(`${platform.name} 已${platform.enabled ? '启用' : '禁用'}`);
};

/** 获取平台对应的 base_url（从后端 config 映射） */
function getBaseUrlForPlatform(platformName: string): string {
  const urlMap: Record<string, string> = {
    'NVIDIA NIM': 'https://integrate.api.nvidia.com/v1',
    'DeepSeek': 'https://api.deepseek.com/v1',
    'OpenAI': 'https://api.openai.com/v1',
    '百度文心一言': 'https://aip.baidubce.com/rpc/2.0/ai_custom',
    '阿里通义千问': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    '字节豆包': 'https://ark.cn-beijing.volces.com/api/v3',
    '智谱GLM': 'https://open.bigmodel.cn/api/paas/v4',
    'Kimi': 'https://api.moonshot.cn/v1',
    '零一万物': 'https://api.01.ai/v1',
    '硅基流动': 'https://api.siliconflow.cn/v1',
    'MiniMax': 'https://api.minimax.chat/v1',
    '讯飞星火': 'https://spark-api-open.xf-yun.com/v1',
  };
  return urlMap[platformName] || '';
}

/** 获取平台默认测试模型 */
function getTestModel(platformName: string): string {
  const modelMap: Record<string, string> = {
    'NVIDIA NIM': 'meta/llama-3.1-8b-instruct',
    'DeepSeek': 'deepseek-chat',
    'OpenAI': 'gpt-3.5-turbo',
    '百度文心一言': 'ernie-speed-128k',
    '阿里通义千问': 'qwen-turbo',
    '字节豆包': 'doubao-pro-4k',
    '智谱GLM': 'glm-4-flash',
    'Kimi': 'moonshot-v1-8k',
    '零一万物': 'yi-lightning',
    '硅基流动': 'Qwen/Qwen2.5-7B-Instruct',
    'MiniMax': 'MiniMax-Text-01',
    '讯飞星火': 'generalv3.5',
  };
  return modelMap[platformName] || 'default';
}

/** 卡片上的"检测"按钮：调用后端 probe 接口 */
async function testPlatform(platform: ModelPlatform) {
  platform._testing = true;
  platform.healthCheck = undefined;
  try {
    const res = await apiPost('/super-admin/ai-config/test', {
      platform: providerTypeByName[platform.name] || platform.name.toLowerCase(),
      base_url: getBaseUrlForPlatform(platform.name),
      model: getTestModel(platform.name),
    });
    platform.healthCheck = {
      healthy: !!res.data?.healthy,
      latency_ms: res.data?.latency_ms,
      message: res.message,
    };
    if (res.data?.healthy) {
      message.success(`${platform.name}: 连接正常 (${res.data.latency_ms}ms)`);
    } else {
      message.warning(`${platform.name}: 连接异常 — ${res.message}`);
    }
  } catch {
    platform.healthCheck = { healthy: false, message: '请求失败' };
    message.error(`${platform.name}: 检测请求失败`);
  } finally {
    platform._testing = false;
  }
}

/** 配置弹窗中的"测试连接"按钮：使用用户输入的 Key */
async function testConfigConnection() {
  const platform = configPlatform.value;
  const key = configApiKey.value.trim();
  if (!platform || !key) return;
  configTesting.value = true;
  configTestResult.value = null;
  try {
    const res = await apiPost('/super-admin/ai-config/test', {
      api_key: key,
      platform: providerTypeByName[platform.name] || platform.name.toLowerCase(),
      base_url: getBaseUrlForPlatform(platform.name),
      model: getTestModel(platform.name),
    });
    configTestResult.value = {
      healthy: !!res.data?.healthy,
      latency_ms: res.data?.latency_ms,
      message: res.message,
    };
  } catch {
    configTestResult.value = { healthy: false, message: '请求失败' };
  } finally {
    configTesting.value = false;
  }
}

/** 生成健康状态 tooltip 文案 */
function healthTooltip(platform: ModelPlatform): string {
  const h = platform.healthCheck;
  if (!h) return '';
  if (h.healthy) return `连接正常 · 延迟 ${h.latency_ms ?? '?'}ms`;
  return `连接异常: ${h.message || '未知错误'}`;
}

/** 批量检测所有已配置平台 */
async function batchTestAll() {
  const configured = platformList.value.filter(p => p.configured);
  if (!configured.length) return;
  batchTesting.value = true;
  let ok = 0;
  let fail = 0;
  // 逐个检测（串行，避免并发打到后端）
  for (const p of configured) {
    await testPlatform(p);
    if (p.healthCheck?.healthy) ok++; else fail++;
  }
  batchTesting.value = false;
  message.info(`检测完成: ${ok} 个正常, ${fail} 个异常`);
}

const openGetKeyLink = (url: string) => {
  window.open(url, '_blank');
};

const submitModelForm = () => {
  showAddModal.value = false;
  message.success('模型已添加');
  Object.assign(modelForm, { name: '', provider: 'openai', type: 'chat', version: '', maxTokens: 4096, description: '' });
};

onMounted(async () => {
  try {
    const res = await apiGet('/super-admin/ai-config/providers');
    if (res.data && Array.isArray(res.data)) {
      res.data.forEach((p: { name: string; provider_type: string; [key: string]: unknown }) => {
        const platform = platformList.value.find(pl => pl.name === p.name || pl.provider.toLowerCase() === p.provider_type);
        if (platform) {
          platform.configured = true;
          platform.enabled = p.enabled !== false;
        }
      });
    }
  } catch { /* 空状态 */ }
});
</script>

<style scoped lang="scss">
.models-page {
  padding: 0;
}

.config-modal-tip {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 16px;
}

/* AI引擎状态横幅 */
.ai-status-banner {
  display: flex;
  align-items: center;
  gap: 24px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 1px solid #bae6fd;
  border-radius: 12px;
  padding: 14px 20px;
  margin-bottom: 24px;

  .banner-item {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .banner-icon {
    font-size: 18px;
  }

  .banner-icon-success {
    color: #10b981;
  }

  .banner-icon-warning {
    color: #f59e0b;
  }

  .banner-text {
    font-size: 14px;
    color: #374151;

    strong {
      font-weight: 700;
      color: #1f2937;
    }
  }

  .banner-text-warn {
    color: #b45309;
    font-weight: 500;
  }

  .banner-text-all {
    color: #10b981;
  }
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 16px;
}

.model-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.model-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02);
  border: 1px solid #e5e7eb;
  transition:
    box-shadow 0.2s ease,
    border-color 0.2s ease;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04);
    border-color: #d1d5db;
  }

  .card-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 14px;

    .model-icon {
      width: 44px;
      height: 44px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      color: #374151;
      background: #f3f4f6;
      flex-shrink: 0;
      transition: all 0.2s ease;
    }

    .icon-configured {
      color: #10b981;
      background: #ecfdf5;
    }

    .model-header-info {
      flex: 1;
      min-width: 0;

      .model-name {
        font-size: 15px;
        font-weight: 600;
        color: #111827;
        margin: 0;
        margin-bottom: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .model-type {
        font-size: 12px;
        color: #4b5563;
        background: #f3f4f6;
        padding: 1px 6px;
        border-radius: 3px;
      }
    }
  }

  .card-body {
    .model-desc {
      font-size: 13px;
      color: #4b5563;
      line-height: 1.6;
      margin: 0;
      margin-bottom: 10px;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .model-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;

      .meta-item {
        font-size: 11px;
        color: #6b7280;
        background: #f3f4f6;
        padding: 3px 6px;
        border-radius: 3px;
      }
    }
  }

  .card-footer {
    display: flex;
    justify-content: flex-end;
    gap: 6px;
    margin-top: 14px;
    padding-top: 14px;
    border-top: 1px solid #f3f4f6;

    // 确保所有按钮文字在当前背景上可读
    :deep(.ant-btn) {
      color: #1f2937;
      border-color: #9ca3af;

      &:hover:not(:disabled) {
        color: #0f766e;
        border-color: #0f766e;
      }

      // link 类型按钮（获取Key）使用主题色
      &.ant-btn-link {
        color: #0f766e;

        &:hover {
          color: #115e59;
        }
      }

      // primary 类型按钮（启用）
      &.ant-btn-primary {
        color: #ffffff;
      }

      // disabled 状态文字仍然清晰可读
      &:disabled {
        color: #9ca3af !important;
        border-color: #e5e7eb !important;
        background: #f9fafb !important;
      }
    }
  }
}

.card-configured {
  border-color: #10b981;
  background: #ffffff;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

@media (max-width: 1200px) {
  .model-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .model-grid {
    grid-template-columns: 1fr;
  }

  .ai-status-banner {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>

