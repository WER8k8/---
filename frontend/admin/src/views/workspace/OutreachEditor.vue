/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage title="AI 写信工作台" subtitle="根据客户画像和企业优势生成开发信" surface="elevated">
    <template #actions>
      <a-space>
        <a-button @click="saveDraft" :loading="saving">
          <SaveOutlined />
          保存草稿
        </a-button>
        <a-button type="primary" @click="sendEmail" :loading="sending">
          <SendOutlined />
          发送邮件
        </a-button>
      </a-space>
    </template>

    <div class="outreach-editor">
      <a-row :gutter="24">
        <!-- 左侧：画像摘要 -->
        <a-col :span="8">
          <a-card title="客户画像" size="small" class="profile-card">
            <div v-if="lead" class="profile-info">
              <div class="profile-header">
                <h4>{{ lead.companyName }}</h4>
                <a-tag :color="getScoreColor(lead.overallScore)">{{ lead.overallScore }} 分</a-tag>
              </div>

              <a-divider style="margin: 12px 0" />

              <div class="profile-details">
                <div class="detail-item">
                  <span class="label">国家</span>
                  <span class="value">{{ lead.country || '-' }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">行业</span>
                  <span class="value">{{ lead.industry || '-' }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">邮箱</span>
                  <span class="value">{{ lead.email || '-' }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">联系人</span>
                  <span class="value">{{ lead.contactName || '-' }}</span>
                </div>
              </div>

              <a-divider style="margin: 12px 0" />

              <ScoreRadar :scores="lead.scoreBreakdown" />

              <a-divider style="margin: 12px 0" />

              <EvidenceChain :evidences="lead.evidenceChain || []" />
            </div>
            <a-empty v-else description="请选择线索" />
          </a-card>
        </a-col>

        <!-- 右侧：邮件编辑器 -->
        <a-col :span="16">
          <!-- A/B 版本切换 -->
          <a-card size="small" class="version-card">
            <template #title>
              <div class="version-header">
                <span>邮件版本</span>
                <a-radio-group v-model:value="currentVersion" size="small">
                  <a-radio-button value="a">版本 A</a-radio-button>
                  <a-radio-button value="b">版本 B</a-radio-button>
                </a-radio-group>
                <a-button size="small" @click="aiGenerate" :loading="generating">
                  <RobotOutlined />
                  AI 生成
                </a-button>
              </div>
            </template>

            <!-- 收件人 -->
            <a-form-item label="收件人">
              <a-input v-model:value="form.to" placeholder="收件人邮箱" />
            </a-form-item>

            <!-- 主题 -->
            <a-form-item label="主题">
              <a-input v-model:value="form.subject" placeholder="邮件主题">
                <template #suffix>
                  <a-tooltip title="插入变量">
                    <NumberOutlined @click="showVariablePicker = !showVariablePicker" style="cursor: pointer" />
                  </a-tooltip>
                </template>
              </a-input>
            </a-form-item>

            <!-- 变量插入器 -->
            <div v-if="showVariablePicker" class="variable-picker">
              <div class="picker-title">插入变量</div>
              <div class="picker-list">
                <a-tag
                  v-for="v in variables"
                  :key="v.key"
                  class="variable-tag"
                  @click="insertVariable(v.key)"
                >
                  {{ v.label }}
                </a-tag>
              </div>
            </div>

            <!-- 正文 -->
            <a-form-item label="正文">
              <div class="editor-toolbar">
                <a-space>
                  <a-tooltip title="加粗">
                    <a-button size="small" @click="insertFormat('bold')">
                      <BoldOutlined />
                    </a-button>
                  </a-tooltip>
                  <a-tooltip title="斜体">
                    <a-button size="small" @click="insertFormat('italic')">
                      <ItalicOutlined />
                    </a-button>
                  </a-tooltip>
                  <a-divider type="vertical" />
                  <a-tooltip title="插入变量">
                    <a-button size="small" @click="showVariablePicker = !showVariablePicker">
                      <NumberOutlined />
                    </a-button>
                  </a-tooltip>
                </a-space>
              </div>
              <a-textarea
                v-model:value="form.body"
                :rows="12"
                placeholder="邮件正文，支持变量插入"
                class="email-body"
              />
            </a-form-item>

            <!-- 追踪选项 -->
            <a-form-item>
              <a-space>
                <a-checkbox v-model:checked="form.trackOpens">追踪打开</a-checkbox>
                <a-checkbox v-model:checked="form.trackClicks">追踪点击</a-checkbox>
              </a-space>
            </a-form-item>
          </a-card>

          <!-- 预览区 -->
          <a-card title="预览" size="small" class="preview-card">
            <a-tabs v-model:activeKey="previewMode">
              <a-tab-pane key="desktop" tab="桌面端">
                <div class="preview-desktop" v-html="previewHtml" />
              </a-tab-pane>
              <a-tab-pane key="mobile" tab="移动端">
                <div class="preview-mobile" v-html="previewHtml" />
              </a-tab-pane>
              <a-tab-pane key="raw" tab="源码">
                <pre class="preview-raw">{{ previewHtml }}</pre>
              </a-tab-pane>
            </a-tabs>
          </a-card>
        </a-col>
      </a-row>
    </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  SaveOutlined,
  SendOutlined,
  RobotOutlined,
  BoldOutlined,
  ItalicOutlined,
  NumberOutlined
} from '@ant-design/icons-vue'
import { YdPage } from '@/components/youding'
import ScoreRadar from '@/components/whatsfinds/ScoreRadar.vue'
import EvidenceChain from '@/components/whatsfinds/EvidenceChain.vue'
import { apiGet, apiPost } from '@/utils/api'

const route = useRoute()
const router = useRouter()

// 状态
const saving = ref(false)
const sending = ref(false)
const generating = ref(false)
const showVariablePicker = ref(false)
const currentVersion = ref('a')
const previewMode = ref('desktop')

// 线索数据
const lead = ref<any>(null)

// 表单
const form = reactive({
  to: '',
  subject: '',
  body: '',
  trackOpens: true,
  trackClicks: true
})

// 变量列表
const variables = [
  { key: '{{company_name}}', label: '公司名' },
  { key: '{{contact_name}}', label: '联系人' },
  { key: '{{country}}', label: '国家' },
  { key: '{{industry}}', label: '行业' },
  { key: '{{evidence_1}}', label: '证据1' },
  { key: '{{evidence_2}}', label: '证据2' },
  { key: '{{product_advantage}}', label: '产品优势' },
  { key: '{{sender_name}}', label: '发件人' },
  { key: '{{sender_company}}', label: '发件公司' },
  { key: '{{unsubscribe_link}}', label: '退订链接' }
]

// HTML 转义（防 XSS）
function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

// 预览 HTML
const previewHtml = computed(() => {
  let html = escapeHtml(form.body)
    .replace(/\n/g, '<br>')
    .replace(/\{\{company_name\}\}/g, escapeHtml(lead.value?.companyName || '[公司名]'))
    .replace(/\{\{contact_name\}\}/g, escapeHtml(lead.value?.contactName || '[联系人]'))
    .replace(/\{\{country\}\}/g, escapeHtml(lead.value?.country || '[国家]'))
    .replace(/\{\{industry\}\}/g, escapeHtml(lead.value?.industry || '[行业]'))
    .replace(/\{\{evidence_1\}\}/g, escapeHtml(lead.value?.evidenceChain?.[0]?.content || '[证据1]'))
    .replace(/\{\{evidence_2\}\}/g, escapeHtml(lead.value?.evidenceChain?.[1]?.content || '[证据2]'))
    .replace(/\{\{product_advantage\}\}/g, escapeHtml('[产品优势]'))
    .replace(/\{\{sender_name\}\}/g, escapeHtml('[发件人]'))
    .replace(/\{\{sender_company\}\}/g, escapeHtml('[发件公司]'))
    .replace(/\{\{unsubscribe_link\}\}/g, '<a href="#">退订</a>')

  if (form.trackOpens) {
    html += '<img src="/api/v1/tracking/pixel/{{message_id}}.png" width="1" height="1" style="display:none" />'
  }

  return html
})

// 插入变量
function insertVariable(key: string) {
  form.body += key
  showVariablePicker.value = false
}

function insertFormat(type: string) {
  // 简单格式化
  if (type === 'bold') {
    form.body += '**粗体文字**'
  } else if (type === 'italic') {
    form.body += '*斜体文字*'
  }
}

// AI 生成
async function aiGenerate() {
  if (!lead.value) {
    message.warning('请先选择线索')
    return
  }
  generating.value = true
  try {
    const res = await apiPost('/workspace/outreach/ai-generate', {
      lead_id: lead.value.id,
      version: currentVersion.value
    })
    form.subject = res.subject || form.subject
    form.body = res.body || form.body
    message.success('AI 生成成功')
  } catch (error) {
    message.error('AI 生成失败')
  } finally {
    generating.value = false
  }
}

// 保存草稿
async function saveDraft() {
  saving.value = true
  try {
    await apiPost('/workspace/outreach/drafts', {
      lead_id: lead.value?.id,
      version: currentVersion.value,
      ...form
    })
    message.success('草稿已保存')
  } catch (error) {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 发送邮件
async function sendEmail() {
  if (!form.to || !form.subject || !form.body) {
    message.warning('请填写完整的邮件信息')
    return
  }
  sending.value = true
  try {
    await apiPost('/workspace/outreach/send', {
      lead_id: lead.value?.id,
      version: currentVersion.value,
      ...form
    })
    message.success('邮件已发送')
    router.back()
  } catch (error) {
    message.error('发送失败')
  } finally {
    sending.value = false
  }
}

// 加载线索
async function loadLead() {
  const leadId = route.query.lead_id
  if (!leadId) return

  try {
    const res = await apiGet(`/workspace/prospecting/leads/${leadId}`)
    lead.value = res
    form.to = res.email || ''
    form.subject = `合作机会 - ${res.companyName || ''}`
  } catch (error) {
    console.error('加载线索失败:', error)
  }
}

// 加载草稿
async function loadDraft() {
  const leadId = route.query.lead_id
  if (!leadId) return

  try {
    const res = await apiGet(`/workspace/outreach/drafts?lead_id=${leadId}`)
    if (res.subject) form.subject = res.subject
    if (res.body) form.body = res.body
  } catch (error) {
    // 无草稿，忽略
  }
}

function getScoreColor(score: number): string {
  if (score >= 80) return '#52c41a'
  if (score >= 60) return '#1890ff'
  if (score >= 40) return '#faad14'
  return '#ff4d4f'
}

onMounted(() => {
  loadLead()
  loadDraft()
})
</script>

<style scoped lang="scss">
.outreach-editor {
  .profile-card {
    position: sticky;
    top: 24px;
  }

  .version-card {
    margin-bottom: 16px;

    .version-header {
      display: flex;
      align-items: center;
      gap: 12px;
    }
  }

  .variable-picker {
    background: #f6f8ff;
    border: 1px solid #d9d9d9;
    border-radius: 6px;
    padding: 12px;
    margin-bottom: 12px;

    .picker-title {
      font-size: 12px;
      color: #666;
      margin-bottom: 8px;
    }

    .picker-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .variable-tag {
      cursor: pointer;

      &:hover {
        color: #1890ff;
        border-color: #1890ff;
      }
    }
  }

  .editor-toolbar {
    margin-bottom: 8px;
    padding: 8px;
    background: #fafafa;
    border-radius: 4px;
  }

  .email-body {
    font-family: 'SF Mono', Monaco, Consolas, monospace;
  }

  .preview-card {
    .preview-desktop {
      background: #fff;
      border: 1px solid #d9d9d9;
      border-radius: 4px;
      padding: 20px;
      max-height: 400px;
      overflow-y: auto;
    }

    .preview-mobile {
      background: #fff;
      border: 1px solid #d9d9d9;
      border-radius: 4px;
      padding: 16px;
      max-width: 375px;
      margin: 0 auto;
      max-height: 400px;
      overflow-y: auto;
    }

    .preview-raw {
      background: #f5f5f5;
      padding: 12px;
      border-radius: 4px;
      font-size: 12px;
      overflow-x: auto;
      max-height: 400px;
    }
  }
}
</style>
