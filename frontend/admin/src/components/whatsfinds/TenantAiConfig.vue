<template>
  <a-card class="tenant-ai-config" :bordered="false">
    <template #title>
      <div class="config-title">
        <SettingOutlined />
        <span>我的 AI 模型配置</span>
      </div>
    </template>

    <a-alert type="info" show-icon class="mb-4">
      <template #message>
        <span>配置您自己的 API Key、模型和邮箱，数据完全属于您。</span>
      </template>
    </a-alert>

    <!-- 配置列表 -->
    <div class="config-list">
      <a-spin :spinning="loading">
        <div v-for="config in configs" :key="config.id" class="config-item">
          <div class="config-header">
            <div class="config-info">
              <div class="config-name">
                <component :is="getProviderIcon(config.providerId)" class="provider-icon" />
                <span>{{ config.name }}</span>
              </div>
              <a-tag :color="config.enabled ? 'green' : 'default'">
                {{ config.enabled ? '已启用' : '未启用' }}
              </a-tag>
            </div>
            <div class="config-actions">
              <a-button size="small" @click="testConfig(config)">
                <template #icon><ApiOutlined /></template>
                测试
              </a-button>
              <a-button size="small" @click="editConfig(config)">
                <template #icon><EditOutlined /></template>
                编辑
              </a-button>
              <a-popconfirm title="确定删除此配置？" @confirm="deleteConfig(config)">
                <a-button size="small" danger>
                  <template #icon><DeleteOutlined /></template>
                  删除
                </a-button>
              </a-popconfirm>
            </div>
          </div>

          <div class="config-detail">
            <a-row :gutter="16">
              <a-col :span="8">
                <div class="detail-item">
                  <span class="detail-label">供应商</span>
                  <span class="detail-value">{{ getProviderName(config.providerId) }}</span>
                </div>
              </a-col>
              <a-col :span="8">
                <div class="detail-item">
                  <span class="detail-label">模型</span>
                  <span class="detail-value">{{ config.modelName }}</span>
                </div>
              </a-col>
              <a-col :span="8">
                <div class="detail-item">
                  <span class="detail-label">状态</span>
                  <a-badge
                    :status="config.testStatus === 'success' ? 'success' : config.testStatus === 'failed' ? 'error' : 'default'"
                    :text="getTestStatusText(config.testStatus)"
                  />
                </div>
              </a-col>
            </a-row>
          </div>
        </div>

        <a-empty v-if="configs.length === 0" description="暂无配置，点击下方按钮添加">
          <a-button type="primary" @click="showAddModal = true">
            <PlusOutlined />
            添加配置
          </a-button>
        </a-empty>
      </a-spin>
    </div>

    <!-- 添加按钮 -->
    <div v-if="configs.length > 0" class="add-btn">
      <a-button type="primary" @click="showAddModal = true">
        <PlusOutlined />
        添加新配置
      </a-button>
    </div>

    <!-- 添加/编辑弹窗 -->
    <a-modal
      v-model:open="showAddModal"
      :title="editingConfig ? '编辑配置' : '添加配置'"
      width="700px"
      :footer="null"
      @cancel="resetForm"
    >
      <a-form :model="form" layout="vertical" @submit="saveConfig">
        <!-- 供应商选择 -->
        <a-form-item label="选择供应商">
          <a-select
            v-model:value="form.providerId"
            placeholder="选择AI模型供应商"
            @change="onProviderChange"
          >
            <a-select-option v-for="p in providers" :key="p.id" :value="p.id">
              {{ p.name }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <!-- 配置名称 -->
        <a-form-item label="配置名称">
          <a-input v-model:value="form.name" placeholder="例如：官网商机解析模型" />
        </a-form-item>

        <!-- 协议类型 -->
        <a-form-item label="协议类型">
          <a-select v-model:value="form.protocol" placeholder="选择协议">
            <a-select-option value="openai_compatible">OpenAI 兼容</a-select-option>
            <a-select-option value="claude_messages">Claude Messages</a-select-option>
            <a-select-option value="gemini_generate">Gemini Generate</a-select-option>
          </a-select>
        </a-form-item>

        <!-- 模型名称 -->
        <a-form-item label="模型名称">
          <a-input v-model:value="form.modelName" placeholder="例如 gpt-4o-mini / deepseek-chat" />
        </a-form-item>

        <!-- Base URL -->
        <a-form-item label="Base URL">
          <a-input v-model:value="form.baseUrl" placeholder="例如 https://api.openai.com/v1" />
        </a-form-item>

        <!-- API Key -->
        <a-form-item label="API Key">
          <a-input-password v-model:value="form.apiKey" placeholder="留空不会覆盖原 Key" />
          <div class="form-help">留空不会覆盖原 Key；页面不会明文回显已保存密钥。</div>
        </a-form-item>

        <!-- 启用状态 -->
        <a-form-item label="启用状态">
          <a-switch v-model:checked="form.enabled" />
        </a-form-item>

        <!-- 温度 -->
        <a-form-item label="温度">
          <a-slider v-model:value="form.temperature" :min="0" :max="2" :step="0.1" />
        </a-form-item>

        <!-- 应用范围 -->
        <a-form-item label="应用范围">
          <a-checkbox-group v-model:value="form.scopes">
            <a-checkbox value="auto_prospect">自动获客</a-checkbox>
            <a-checkbox value="website_parse">官网解析</a-checkbox>
            <a-checkbox value="lead_score">线索评分</a-checkbox>
            <a-checkbox value="email_draft">开发信草稿</a-checkbox>
            <a-checkbox value="material_exam">资料/考试</a-checkbox>
          </a-checkbox-group>
        </a-form-item>

        <!-- 操作按钮 -->
        <a-form-item>
          <a-space>
            <a-button type="primary" :loading="saving" @click="saveConfig">
              保存配置
            </a-button>
            <a-button @click="resetForm">取消</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-modal>
  </a-card>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, type Component } from 'vue'
import { message } from 'ant-design-vue'
import {
  SettingOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ApiOutlined,
  SearchOutlined,
  CodeOutlined,
  GlobalOutlined,
  RobotOutlined,
  MailOutlined
} from '@ant-design/icons-vue'
import { apiGet, apiPost, apiPut, apiDelete } from '@/utils/api'

// 类型定义
interface AiProviderConfig {
  id: string
  name: string
  providerId: string
  protocol: string
  modelName: string
  baseUrl: string
  apiKey: string
  enabled: boolean
  temperature: number
  scopes: string[]
  testStatus: 'pending' | 'success' | 'failed'
  lastTestTime?: string
}

interface AiProvider {
  id: string
  name: string
  icon: string
  defaultBaseUrl: string
  defaultModel: string
}

// 状态
const loading = ref(false)
const saving = ref(false)
const configs = ref<AiProviderConfig[]>([])
const providers = ref<AiProvider[]>([])
const showAddModal = ref(false)
const editingConfig = ref<AiProviderConfig | null>(null)

const form = reactive({
  providerId: '',
  name: '',
  protocol: 'openai_compatible',
  modelName: '',
  baseUrl: '',
  apiKey: '',
  enabled: false,
  temperature: 0.1,
  scopes: [] as string[]
})

// 初始化
onMounted(() => {
  loadConfigs()
  loadProviders()
})

// 加载配置列表
async function loadConfigs() {
  loading.value = true
  try {
    const res = await apiGet('/tenant-ai-config/my-configs')
    configs.value = res.items || []
  } catch (error) {
    console.error('加载配置失败:', error)
  } finally {
    loading.value = false
  }
}

// 加载供应商列表
async function loadProviders() {
  try {
    const res = await apiGet('/tenant-ai-config/providers')
    providers.value = res.items || []
  } catch (error) {
    console.error('加载供应商失败:', error)
  }
}

// 供应商变化
function onProviderChange(value: unknown) {
  const providerId = String(value)
  const provider = providers.value.find(p => p.id === providerId)
  if (provider) {
    form.baseUrl = provider.defaultBaseUrl
    form.modelName = provider.defaultModel
    form.name = `${provider.defaultModel} 模型`
  }
}

// 测试配置
async function testConfig(config: AiProviderConfig) {
  message.loading({ content: '正在测试连接...', key: 'test' })
  try {
    await apiPost(`/tenant-ai-config/test-config/${config.id}`)
    config.testStatus = 'success'
    message.success({ content: '测试成功', key: 'test' })
  } catch (error) {
    config.testStatus = 'failed'
    message.error({ content: '测试失败', key: 'test' })
  }
}

// 编辑配置
function editConfig(config: AiProviderConfig) {
  editingConfig.value = config
  Object.assign(form, {
    providerId: config.providerId,
    name: config.name,
    protocol: config.protocol,
    modelName: config.modelName,
    baseUrl: config.baseUrl,
    apiKey: '',
    enabled: config.enabled,
    temperature: config.temperature,
    scopes: config.scopes
  })
  showAddModal.value = true
}

// 删除配置
async function deleteConfig(config: AiProviderConfig) {
  try {
    await apiDelete(`/tenant-ai-config/my-configs/${config.id}`)
    configs.value = configs.value.filter(c => c.id !== config.id)
    message.success('删除成功')
  } catch (error) {
    message.error('删除失败')
  }
}

// 保存配置
async function saveConfig() {
  if (!form.providerId || !form.modelName) {
    message.warning('请选择供应商并填写模型名称')
    return
  }

  saving.value = true
  try {
    if (editingConfig.value) {
      await apiPut(`/tenant-ai-config/my-configs/${editingConfig.value.id}`, form)
      message.success('更新成功')
    } else {
      await apiPost('/tenant-ai-config/my-configs', form)
      message.success('添加成功')
    }
    showAddModal.value = false
    resetForm()
    loadConfigs()
  } catch (error) {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 重置表单
function resetForm() {
  editingConfig.value = null
  Object.assign(form, {
    providerId: '',
    name: '',
    protocol: 'openai_compatible',
    modelName: '',
    baseUrl: '',
    apiKey: '',
    enabled: false,
    temperature: 0.1,
    scopes: []
  })
}

// 获取供应商图标
function getProviderIcon(providerId: string) {
  const icons: Record<string, Component> = {
    'openai': SearchOutlined,
    'deepseek': CodeOutlined,
    'qwen': GlobalOutlined,
    'claude': RobotOutlined,
    'gemini': MailOutlined
  }
  return icons[providerId] || CodeOutlined
}

// 获取供应商名称
function getProviderName(providerId: string) {
  const provider = providers.value.find(p => p.id === providerId)
  return provider?.name || providerId
}

// 获取测试状态文本
function getTestStatusText(status?: string) {
  const map: Record<string, string> = {
    'pending': '待测试',
    'success': '连接正常',
    'failed': '连接失败'
  }
  return map[status || 'pending'] || '待测试'
}
</script>

<style scoped lang="scss">
.tenant-ai-config {
  .config-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 600;
  }

  .config-list {
    margin-bottom: 16px;
  }

  .config-item {
    border: 1px solid #f0f0f0;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
    background: #fafafa;

    .config-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;

      .config-info {
        display: flex;
        align-items: center;
        gap: 12px;

        .config-name {
          display: flex;
          align-items: center;
          gap: 8px;
          font-weight: 500;
          font-size: 14px;

          .provider-icon {
            font-size: 18px;
            color: #1890ff;
          }
        }
      }

      .config-actions {
        display: flex;
        gap: 8px;
      }
    }

    .config-detail {
      background: #fff;
      border-radius: 4px;
      padding: 12px;

      .detail-item {
        .detail-label {
          display: block;
          font-size: 12px;
          color: #888;
          margin-bottom: 4px;
        }
        .detail-value {
          font-size: 14px;
          color: #333;
        }
      }
    }
  }

  .add-btn {
    text-align: center;
    padding: 16px;
  }

  .form-help {
    font-size: 12px;
    color: #888;
    margin-top: 4px;
  }
}
</style>
