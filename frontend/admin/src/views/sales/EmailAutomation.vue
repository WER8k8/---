/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <YdPage surface="elevated">
    <template #actions>
      <a-button type="primary" :disabled="!tenantApiAvailable" @click="showComposeModal = true">
        <PlusOutlined />
        写开发信
      </a-button>
      <a-button :disabled="!tenantApiAvailable" @click="showCampaignModal = true">
        <RocketOutlined />
        创建活动
      </a-button>
    </template>
  <div class="email-automation">
        <a-alert v-if="!tenantApiAvailable" type="warning" show-icon message="邮件功能受限：租户后端接口未开放或权限不足，请联系管理员开启。" />
      <!-- 统计卡片 -->
      <div class="stats-cards">
        <a-card class="stat-card">
          <a-statistic
            title="已发送"
            :value="stats.totalSent"
            :value-style="{ color: '#1890ff' }"
          >
            <template #prefix><SendOutlined /></template>
          </a-statistic>
        </a-card>
        <a-card class="stat-card">
          <a-statistic
            title="打开率"
            :value="stats.openRate"
            :precision="1"
            suffix="%"
            :value-style="{ color: '#52c41a' }"
          >
            <template #prefix><EyeOutlined /></template>
          </a-statistic>
        </a-card>
        <a-card class="stat-card">
          <a-statistic
            title="回复率"
            :value="stats.replyRate"
            :precision="1"
            suffix="%"
            :value-style="{ color: '#faad14' }"
          >
            <template #prefix><MessageOutlined /></template>
          </a-statistic>
        </a-card>
        <a-card class="stat-card">
          <a-statistic
            title="进行中活动"
            :value="stats.activeCampaigns"
            :value-style="{ color: '#722ed1' }"
          >
            <template #prefix><ThunderboltOutlined /></template>
          </a-statistic>
        </a-card>
      </div>

      <!-- 标签页 -->
      <a-tabs v-model:activeKey="activeTab" class="main-tabs">
        <!-- 邮件活动 -->
        <a-tab-pane key="campaigns" tab="邮件活动">
          <a-card>
            <a-table
              :columns="campaignColumns"
              :data-source="campaigns"
              :loading="loadingCampaigns"
              :pagination="{ pageSize: 10 }"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'name'">
                  <div class="campaign-name">
                    <div class="name">{{ record.name }}</div>
                    <div class="meta">
                      创建于 {{ formatDate(record.createdAt) }}
                    </div>
                  </div>
                </template>
                <template v-else-if="column.key === 'progress'">
                  <a-progress
                    :percent="Math.round((record.sent / record.total) * 100)"
                    :status="record.status === 'active' ? 'active' : 'normal'"
                    size="small"
                  />
                  <div class="progress-text">
                    {{ record.sent }} / {{ record.total }}
                  </div>
                </template>
                <template v-else-if="column.key === 'stats'">
                  <div class="stats-mini">
                    <span class="stat-item">
                      <EyeOutlined /> {{ record.openRate }}%
                    </span>
                    <span class="stat-item">
                      <MessageOutlined /> {{ record.replyRate }}%
                    </span>
                  </div>
                </template>
                <template v-else-if="column.key === 'status'">
                  <a-tag :color="getCampaignStatusColor(record.status)">
                    {{ getCampaignStatusText(record.status) }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'actions'">
                  <a-space>
                    <a-button type="link" size="small" @click="viewCampaign(record)">
                      查看
                    </a-button>
                    <a-button
                      type="link"
                      size="small"
                      @click="pauseCampaign(record)"
                      v-if="record.status === 'active'"
                    >
                      暂停
                    </a-button>
                    <a-button
                      type="link"
                      size="small"
                      @click="resumeCampaign(record)"
                      v-if="record.status === 'paused'"
                    >
                      继续
                    </a-button>
                    <a-dropdown>
                      <a-button type="link" size="small">
                        更多 <DownOutlined />
                      </a-button>
                      <template #overlay>
                        <a-menu @click="({ key }) => handleCampaignAction(key, record)">
                          <a-menu-item key="duplicate">复制活动</a-menu-item>
                          <a-menu-item key="export">导出数据</a-menu-item>
                          <a-menu-divider />
                          <a-menu-item key="delete" danger>删除</a-menu-item>
                        </a-menu>
                      </template>
                    </a-dropdown>
                  </a-space>
                </template>
              </template>
            </a-table>
          </a-card>
        </a-tab-pane>

        <!-- 邮件列表 -->
        <a-tab-pane key="emails" tab="邮件列表">
          <a-card>
            <template #extra>
              <a-space>
                <a-select
                  v-model:value="emailFilter.status"
                  placeholder="状态筛选"
                  style="width: 120px"
                  :options="emailStatusOptions"
                />
                <a-select
                  v-model:value="emailFilter.type"
                  placeholder="类型筛选"
                  style="width: 120px"
                  :options="emailTypeOptions"
                />
              </a-space>
            </template>
            <a-table
              :columns="emailColumns"
              :data-source="filteredEmails"
              :loading="loadingEmails"
              :pagination="{ pageSize: 15 }"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'recipient'">
                  <div class="recipient-info">
                    <div class="name">{{ record.recipientName }}</div>
                    <div class="email">{{ record.recipientEmail }}</div>
                  </div>
                </template>
                <template v-else-if="column.key === 'subject'">
                  <div class="email-subject">
                    {{ record.subject }}
                  </div>
                </template>
                <template v-else-if="column.key === 'type'">
                  <a-tag :color="getEmailTypeColor(record.type)">
                    {{ getEmailTypeText(record.type) }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'status'">
                  <a-badge
                    :status="getEmailStatusBadge(record.status)"
                    :text="getEmailStatusText(record.status)"
                  />
                </template>
                <template v-else-if="column.key === 'sentAt'">
                  {{ record.sentAt ? formatDate(record.sentAt) : '-' }}
                </template>
                <template v-else-if="column.key === 'actions'">
                  <a-space>
                    <a-button type="link" size="small" @click="viewEmail(record)">
                      查看
                    </a-button>
                    <a-button
                      type="link"
                      size="small"
                      @click="resendEmail(record)"
                      v-if="record.status === 'failed'"
                    >
                      重发
                    </a-button>
                  </a-space>
                </template>
              </template>
            </a-table>
          </a-card>
        </a-tab-pane>

        <!-- 邮件模板 -->
        <a-tab-pane key="templates" tab="邮件模板">
          <div class="templates-grid">
            <a-card
              v-for="template in templates"
              :key="template.id"
              class="template-card"
              hoverable
            >
              <template #cover>
                <div class="template-cover" :style="{ backgroundColor: template.color }">
                  <MailOutlined />
                </div>
              </template>
              <a-card-meta>
                <template #title>
                  <div class="template-title">
                    {{ template.name }}
                    <a-tag v-if="template.isDefault" color="blue" size="small">默认</a-tag>
                  </div>
                </template>
                <template #description>
                  <div class="template-desc">{{ template.description }}</div>
                  <div class="template-meta">
                    <span>{{ template.usageCount }} 次使用</span>
                    <span>{{ template.language.toUpperCase() }}</span>
                  </div>
                </template>
              </a-card-meta>
              <template #actions>
                <EditOutlined key="edit" @click="editTemplate(template)" />
                <CopyOutlined key="copy" @click="duplicateTemplate(template)" />
                <DeleteOutlined key="delete" @click="deleteTemplate(template)" />
              </template>
            </a-card>

            <!-- 新建模板卡片 -->
            <a-card class="template-card new-template" hoverable @click="createTemplate">
              <div class="new-template-content">
                <PlusOutlined />
                <div class="text">新建模板</div>
              </div>
            </a-card>
          </div>
        </a-tab-pane>

        <!-- 效果分析 -->
        <a-tab-pane key="analytics" tab="效果分析">
          <a-row :gutter="24">
            <a-col :span="12">
              <a-card title="邮件送达趋势">
                <div class="email-stats-panel">
                  <a-empty description="图表加载中..." />
                </div>
              </a-card>
            </a-col>
            <a-col :span="12">
              <a-card title="打开率/回复率趋势">
                <div class="email-stats-panel">
                  <a-empty description="图表加载中..." />
                </div>
              </a-card>
            </a-col>
          </a-row>
          <a-row :gutter="24" style="margin-top: 24px">
            <a-col :span="8">
              <a-card title="邮件类型分布">
                <div class="email-stats-panel">
                  <a-empty description="图表加载中..." />
                </div>
              </a-card>
            </a-col>
            <a-col :span="8">
              <a-card title="地区分布">
                <div class="email-stats-panel">
                  <a-empty description="图表加载中..." />
                </div>
              </a-card>
            </a-col>
            <a-col :span="8">
              <a-card title="最佳发送时间">
                <div class="email-stats-panel">
                  <a-empty description="图表加载中..." />
                </div>
              </a-card>
            </a-col>
          </a-row>
        </a-tab-pane>
      </a-tabs>

      <!-- 写开发信弹窗 -->
      <a-modal
        v-model:open="showComposeModal"
        title="写开发信"
        width="800px"
        :footer="null"
      >
        <a-form :model="composeForm" layout="vertical">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="收件人">
                <a-select
                  v-model:value="composeForm.recipients"
                  mode="multiple"
                  placeholder="选择客户"
                  :options="customerOptions"
                  show-search
                />
              </a-form-item>
            </a-col>
            <a-col :span="6">
              <a-form-item label="邮件类型">
                <a-select
                  v-model:value="composeForm.type"
                  :options="emailTypeOptions"
                />
              </a-form-item>
            </a-col>
            <a-col :span="6">
              <a-form-item label="语言">
                <a-select
                  v-model:value="composeForm.language"
                  :options="languageOptions"
                />
              </a-form-item>
            </a-col>
          </a-row>
          <a-form-item label="邮件主题">
            <a-input v-model:value="composeForm.subject" placeholder="输入邮件主题" />
          </a-form-item>
          <a-form-item label="邮件内容">
            <a-textarea
              v-model:value="composeForm.content"
              :rows="12"
              placeholder="输入邮件内容，或点击'AI生成'自动创建"
            />
          </a-form-item>
          <a-form-item>
            <a-space>
              <a-button @click="generateWithAI">
                <RobotOutlined />
                AI生成
              </a-button>
              <a-button @click="previewEmail">预览</a-button>
              <a-button type="primary" @click="sendEmails" :loading="sending">
                <SendOutlined />
                发送
              </a-button>
              <a-button @click="() => scheduleEmail()">定时发送</a-button>
            </a-space>
          </a-form-item>
        </a-form>
      </a-modal>

      <!-- 创建活动弹窗 -->
      <a-modal
        v-model:open="showCampaignModal"
        title="创建邮件活动"
        width="700px"
        @ok="createCampaign"
      >
        <a-form :model="campaignForm" layout="vertical">
          <a-form-item label="活动名称">
            <a-input v-model:value="campaignForm.name" placeholder="输入活动名称" />
          </a-form-item>
          <a-form-item label="选择客户列表">
            <a-transfer
              v-model:target-keys="campaignForm.customerIds"
              :data-source="transferData"
              :titles="['可选客户', '已选客户']"
              :render="item => item.title"
              show-search
            />
          </a-form-item>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="邮件类型">
                <a-select
                  v-model:value="campaignForm.emailType"
                  :options="emailTypeOptions"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="语言">
                <a-select
                  v-model:value="campaignForm.language"
                  :options="languageOptions"
                />
              </a-form-item>
            </a-col>
          </a-row>
          <a-form-item label="发送计划">
            <a-radio-group v-model:value="campaignForm.scheduleType">
              <a-radio value="immediate">立即发送</a-radio>
              <a-radio value="scheduled">定时发送</a-radio>
              <a-radio value="drip">渐进发送（每天50封）</a-radio>
            </a-radio-group>
          </a-form-item>
          <a-form-item v-if="campaignForm.scheduleType === 'scheduled'" label="发送时间">
            <a-date-picker
              v-model:value="campaignForm.scheduledAt"
              show-time
              style="width: 100%"
            />
          </a-form-item>
          <a-form-item label="自动跟进">
            <a-switch v-model:checked="campaignForm.autoFollowUp" />
            <span class="switch-label">未回复时自动发送跟进邮件</span>
          </a-form-item>
          <a-form-item v-if="campaignForm.autoFollowUp" label="跟进序列">
            <a-card size="small">
              <div class="followup-sequence">
                <div class="sequence-item">
                  <a-tag color="blue">第1封</a-tag>
                  <span>3天后发送第一次跟进</span>
                </div>
                <div class="sequence-item">
                  <a-tag color="blue">第2封</a-tag>
                  <span>7天后发送第二次跟进</span>
                </div>
                <div class="sequence-item">
                  <a-tag color="blue">第3封</a-tag>
                  <span>14天后发送最终跟进</span>
                </div>
              </div>
            </a-card>
          </a-form-item>
        </a-form>
      </a-modal>

      <!-- 邮件详情抽屉 -->
      <a-drawer
        v-model:open="showEmailDrawer"
        title="邮件详情"
        width="600"
        placement="right"
      >
        <EmailDetail
          v-if="selectedEmail"
          :email="selectedEmail"
          @resend="resendEmail"
          @reply="replyToEmail"
        />
      </a-drawer>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import type { Dayjs } from 'dayjs';
import { message } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import {
  MailOutlined,
  PlusOutlined,
  RocketOutlined,
  SendOutlined,
  EyeOutlined,
  MessageOutlined,
  ThunderboltOutlined,
  DownOutlined,
  EditOutlined,
  CopyOutlined,
  DeleteOutlined,
  RobotOutlined,
} from '@ant-design/icons-vue';
import EmailDetail from '@/components/sales/EmailDetail.vue';
import { apiGet, apiPost, apiPut, apiDelete, authHeaders } from '@/utils/api';
import { getCampaigns, getEmails, getEmailTemplates, generateEmail } from '@/api/ubrain/sales';
import type { EmailCampaign, Email, EmailTemplate } from '@/types/sales';

// 统计数据（由 API 加载后更新）
const stats = reactive({
  totalSent: 0,
  openRate: 0,
  replyRate: 0,
  activeCampaigns: 0,
});

// 状态
const activeTab = ref('campaigns');
const loadingCampaigns = ref(false);
const loadingEmails = ref(false);
const sending = ref(false);
const showComposeModal = ref(false);
const showCampaignModal = ref(false);
const showEmailDrawer = ref(false);
const selectedEmail = ref<Email | null>(null);
// 后端能力检测：租户是否有可用的邮件 API（防止在 client shell 渲染失败）
const tenantApiAvailable = ref(true);

// 数据
const campaigns = ref<EmailCampaign[]>([]);
const emails = ref<Email[]>([]);
const templates = ref<EmailTemplate[]>([]);

// 筛选器
const emailFilter = reactive({
  status: undefined,
  type: undefined,
});

// 表单
const composeForm = reactive({
  recipients: [] as string[],
  type: 'cold_outreach',
  language: 'en',
  subject: '',
  content: '',
});

const campaignForm = reactive({
  name: '',
  customerIds: [],
  emailType: 'cold_outreach',
  language: 'en',
  scheduleType: 'immediate',
  scheduledAt: undefined as string | Dayjs | undefined,
  autoFollowUp: true,
});

// 表格列定义
const campaignColumns = [
  { title: '活动名称', key: 'name', width: 250 },
  { title: '进度', key: 'progress', width: 150 },
  { title: '效果', key: 'stats', width: 120 },
  { title: '状态', key: 'status', width: 100 },
  { title: '创建时间', dataIndex: 'createdAt', key: 'createdAt', width: 120 },
  { title: '操作', key: 'actions', width: 200, fixed: 'right' as const },
];

const emailColumns = [
  { title: '收件人', key: 'recipient', width: 200 },
  { title: '主题', key: 'subject', dataIndex: 'subject' },
  { title: '类型', key: 'type', width: 100 },
  { title: '状态', key: 'status', width: 120 },
  { title: '发送时间', key: 'sentAt', width: 150 },
  { title: '操作', key: 'actions', width: 120, fixed: 'right' as const },
];

// 选项
const emailStatusOptions = [
  { label: '全部', value: undefined },
  { label: '草稿', value: 'draft' },
  { label: '已发送', value: 'sent' },
  { label: '已送达', value: 'delivered' },
  { label: '已打开', value: 'opened' },
  { label: '已回复', value: 'replied' },
  { label: '失败', value: 'failed' },
];

const emailTypeOptions = [
  { label: '冷开发信', value: 'cold_outreach' },
  { label: '跟进邮件', value: 'follow_up' },
  { label: '报价邮件', value: 'quote' },
  { label: '欢迎邮件', value: 'welcome' },
  { label: '营销邮件', value: 'marketing' },
];

const languageOptions = [
  { label: 'English', value: 'en' },
  { label: 'Deutsch', value: 'de' },
  { label: 'Français', value: 'fr' },
  { label: 'Español', value: 'es' },
  { label: '中文', value: 'zh' },
];

const customerOptions = [
  { label: 'ABC Construction (USA)', value: '1' },
  { label: 'Deutsche Baustoffe (Germany)', value: '2' },
  { label: 'BuildRight UK', value: '3' },
  { label: 'Matériaux Paris (France)', value: '4' },
];

const transferData = computed(() => {
  return customerOptions.map(opt => ({
    key: opt.value,
    title: opt.label,
  }));
});

// 计算属性
const filteredEmails = computed(() => {
  let result = emails.value;
  if (emailFilter.status) {
    result = result.filter(e => e.status === emailFilter.status);
  }
  if (emailFilter.type) {
    result = result.filter(e => e.type === emailFilter.type);
  }
  return result;
});

// 方法
function getCampaignStatusColor(status: string): string {
  const colors: Record<string, string> = {
    active: 'green',
    paused: 'orange',
    completed: 'blue',
    draft: 'default',
  };
  return colors[status] || 'default';
}

function getCampaignStatusText(status: string): string {
  const texts: Record<string, string> = {
    active: '进行中',
    paused: '已暂停',
    completed: '已完成',
    draft: '草稿',
  };
  return texts[status] || status;
}

function getEmailTypeColor(type: string): string {
  const colors: Record<string, string> = {
    cold_outreach: 'blue',
    follow_up: 'orange',
    quote: 'green',
    welcome: 'purple',
    marketing: 'cyan',
  };
  return colors[type] || 'default';
}

function getEmailTypeText(type: string): string {
  const texts: Record<string, string> = {
    cold_outreach: '冷开发',
    follow_up: '跟进',
    quote: '报价',
    welcome: '欢迎',
    marketing: '营销',
  };
  return texts[type] || type;
}

function getEmailStatusBadge(status: string): 'success' | 'processing' | 'default' | 'error' | 'warning' {
  const badges: Record<string, 'success' | 'processing' | 'default' | 'error' | 'warning'> = {
    sent: 'processing',
    delivered: 'success',
    opened: 'success',
    clicked: 'success',
    replied: 'success',
    failed: 'error',
    draft: 'default',
  };
  return badges[status] || 'default';
}

function getEmailStatusText(status: string): string {
  const texts: Record<string, string> = {
    draft: '草稿',
    sent: '已发送',
    delivered: '已送达',
    opened: '已打开',
    clicked: '已点击',
    replied: '已回复',
    failed: '失败',
  };
  return texts[status] || status;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('zh-CN');
}

function updateStatsFromData() {
  const sent = emails.value.length;
  const opened = emails.value.filter((e) => ['opened', 'clicked', 'replied'].includes(e.status)).length;
  const replied = emails.value.filter((e) => e.status === 'replied').length;
  stats.totalSent = sent;
  stats.openRate = sent > 0 ? +(opened / sent * 100).toFixed(1) : 0;
  stats.replyRate = sent > 0 ? +(replied / sent * 100).toFixed(1) : 0;
  stats.activeCampaigns = campaigns.value.filter((c) => c.status === 'active').length;
}

function mapCampaign(raw: Record<string, unknown>): EmailCampaign {
  return {
    id: String(raw.campaign_id || raw.id || ''),
    name: String(raw.name || ''),
    total: Number(raw.total_emails ?? raw.total ?? 0),
    sent: Number(raw.sent ?? 0),
    status: (raw.status as EmailCampaign['status']) || 'active',
    openRate: Number(raw.open_rate ?? raw.openRate ?? 0),
    replyRate: Number(raw.reply_rate ?? raw.replyRate ?? 0),
    createdAt: String(raw.created_at ?? raw.createdAt ?? ''),
  };
}

async function loadCampaigns() {
  loadingCampaigns.value = true;
  try {
    const data = await getCampaigns({ limit: 50 });
    campaigns.value = (data.campaigns || []).map((c) => mapCampaign(c as unknown as Record<string, unknown>));
    updateStatsFromData();
    tenantApiAvailable.value = true;
  } catch (err: any) {
    campaigns.value = [];
    // 如果请求失败（网络、CORS、403/404 等），视为租户接口不可用，显示受限提示
    tenantApiAvailable.value = false;
  } finally {
    loadingCampaigns.value = false;
  }
}

async function loadEmails() {
  loadingEmails.value = true;
  try {
    const data = await getEmails({ limit: 50 });
    emails.value = data.emails || [];
    updateStatsFromData();
    tenantApiAvailable.value = true;
  } catch (err: any) {
    emails.value = [];
    // 请求失败时（包括网络错误或 403/404），标记租户 API 不可用
    tenantApiAvailable.value = false;
  } finally {
    loadingEmails.value = false;
  }
}

async function loadTemplates() {
  try {
    const data = await getEmailTemplates();
    templates.value = Array.isArray(data) ? data : [];
    tenantApiAvailable.value = true;
  } catch (err: any) {
    templates.value = [];
    // 请求失败也视为租户接口未开放
    tenantApiAvailable.value = false;
  }
}

async function loadAll() {
  await Promise.all([loadCampaigns(), loadEmails(), loadTemplates()]);
}

async function viewCampaign(campaign: any) {
  try {
    const data = await apiGet(`/email/campaigns/${campaign.id}`);
    selectedEmail.value = data;
    showEmailDrawer.value = true;
  } catch (e) {
    message.error('加载活动详情失败');
  }
}

async function pauseCampaign(campaign: any) {
  try {
    await apiPut(`/email/campaigns/${campaign.id}/pause`);
    campaign.status = 'paused';
    message.success('活动已暂停');
  } catch (e) {
    message.error('暂停活动失败');
  }
}

async function resumeCampaign(campaign: any) {
  try {
    await apiPut(`/email/campaigns/${campaign.id}/resume`);
    campaign.status = 'active';
    message.success('活动已继续');
  } catch (e) {
    message.error('继续活动失败');
  }
}

function handleCampaignAction(key: string | number, campaign: any) {
  const action = String(key);
  switch (action) {
    case 'duplicate':
      message.success('活动已复制');
      break;
    case 'export':
      message.success('数据导出中...');
      break;
    case 'delete':
      message.success('活动已删除');
      break;
  }
}

function viewEmail(email: any) {
  selectedEmail.value = email;
  showEmailDrawer.value = true;
}

async function resendEmail(email: any) {
  try {
    await apiPost(`/email/resend/${email.id}`);
    message.success('邮件已重新发送');
  } catch (e) {
    message.error('重发邮件失败');
  }
}

async function replyToEmail(email: any) {
  try {
    await apiPost(`/email/reply/${email.id}`, { content: composeForm.content });
  } catch (e) {
    // 回复操作失败时仍打开弹窗让用户手动处理
    message.warning('自动回复失败，请手动发送');
  }
  composeForm.recipients = [email.recipientEmail];
  composeForm.type = 'follow_up';
  showComposeModal.value = true;
}

function editTemplate(template: EmailTemplate) {
  composeForm.subject = template.name;
  composeForm.content = template.content || template.description || '';
  composeForm.type = template.type;
  composeForm.language = template.language;
  showComposeModal.value = true;
  message.success(`已加载模板: ${template.name}`);
}

async function duplicateTemplate(template: EmailTemplate) {
  try {
    await apiPost(`/email/templates/${template.id}/copy`);
    message.success('模板已复制');
  } catch (e) {
    message.error('复制模板失败');
  }
}

async function deleteTemplate(template: EmailTemplate) {
  try {
    await apiDelete(`/email/templates/${template.id}`);
    templates.value = templates.value.filter(t => t.id !== template.id);
    message.success('模板已删除');
  } catch (e) {
    message.error('删除模板失败');
  }
}

async function createTemplate() {
  try {
    const data = await apiPost('/email/templates');
    templates.value.push(data);
    message.success('模板已创建');
  } catch (e) {
    message.error('创建模板失败');
  }
}

async function generateWithAI() {
  try {
    const data = await generateEmail({
      customer_data: {},
      email_type: composeForm.type,
      language: composeForm.language,
    });
    composeForm.subject = data.subject || '';
    composeForm.content = data.body || '';
    message.success('AI已生成邮件内容');
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : 'AI生成失败，请稍后重试');
  }
}

async function previewEmail() {
  try {
    await apiPost('/email/preview', {
      subject: composeForm.subject,
      content: composeForm.content,
      type: composeForm.type,
      language: composeForm.language,
    });
    message.success('邮件预览已生成');
  } catch (e) {
    message.error('预览生成失败');
  }
}

async function sendEmails() {
  if (composeForm.recipients.length === 0) {
    message.warning('请选择收件人');
    return;
  }

  sending.value = true;
  try {
    const response = await fetch('/api/v1/super-agent/sales/email-automation', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        action: 'send_emails',
        recipients: composeForm.recipients,
        email_type: composeForm.type,
        language: composeForm.language,
        subject: composeForm.subject,
        content: composeForm.content,
      }),
    });
    const result = await response.json();
    
    if (result.code === 0) {
      message.success(`已向 ${composeForm.recipients.length} 个收件人发送邮件`);
      showComposeModal.value = false;
      // 清空表单
      composeForm.recipients = [];
      composeForm.subject = '';
      composeForm.content = '';
    } else {
      message.error(result.message || '发送失败');
    }
  } catch (error) {
    console.error('发送邮件失败:', error);
    message.error('发送失败，请重试');
  } finally {
    sending.value = false;
  }
}

async function scheduleEmail(campaignId?: string) {
  try {
    const id = campaignId || composeForm.recipients;
    await apiPost(`/email/campaigns/${id}/schedule`, {
      subject: composeForm.subject,
      content: composeForm.content,
      recipients: composeForm.recipients,
      type: composeForm.type,
      language: composeForm.language,
    });
    message.success('定时发送已设置');
  } catch (e) {
    message.error('定时发送设置失败');
  }
}

async function createCampaign() {
  if (!campaignForm.name) {
    message.warning('请输入活动名称');
    return;
  }

  if (campaignForm.customerIds.length === 0) {
    message.warning('请选择客户');
    return;
  }

  try {
    const response = await fetch('/api/v1/super-agent/sales/email-automation', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        action: 'create_campaign',
        campaign_name: campaignForm.name,
        customer_ids: campaignForm.customerIds,
        email_type: campaignForm.emailType,
        language: campaignForm.language,
        schedule_type: campaignForm.scheduleType,
        scheduled_at: campaignForm.scheduledAt,
        auto_follow_up: campaignForm.autoFollowUp,
      }),
    });
    const result = await response.json();
    
    if (result.code === 0) {
      message.success('活动已创建');
      showCampaignModal.value = false;
      campaignForm.name = '';
      campaignForm.customerIds = [];
      await loadCampaigns();
    } else {
      message.error(result.message || '创建失败');
    }
  } catch (error) {
    console.error('创建活动失败:', error);
    message.error('创建失败，请重试');
  }
}

onMounted(() => {
  loadAll();
  const prefill = (history.state as { emailPrefill?: Partial<typeof composeForm> })?.emailPrefill;
  if (prefill) {
    if (prefill.recipients?.length) composeForm.recipients = prefill.recipients as string[];
    if (prefill.subject) composeForm.subject = prefill.subject;
    if (prefill.type) composeForm.type = prefill.type;
    if (prefill.language) composeForm.language = prefill.language;
    showComposeModal.value = true;
    message.success('已填入客户信息，请编辑后发送');
  }
});
</script>

<style scoped>
.email-automation {
  padding: 24px;
  background: #f5f5f5;
  min-height: calc(100vh - 64px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding: 24px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}

.header-content {
  flex: 1;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-description {
  margin: 0;
  font-size: 14px;
  color: #8c8c8c;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  border-radius: 8px;
}

.main-tabs {
  background: #fff;
  padding: 24px;
  border-radius: 8px;
}

.campaign-name .name {
  font-weight: 500;
}

.campaign-name .meta {
  font-size: 12px;
  color: #8c8c8c;
}

.progress-text {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 4px;
}

.stats-mini {
  display: flex;
  gap: 12px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #8c8c8c;
}

.recipient-info .name {
  font-weight: 500;
}

.recipient-info .email {
  font-size: 12px;
  color: #8c8c8c;
}

.email-subject {
  max-width: 400px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.templates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

.template-card {
  border-radius: 8px;
}

.template-cover {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  color: #fff;
}

.template-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.template-desc {
  font-size: 12px;
  color: #8c8c8c;
  margin-bottom: 8px;
}

.template-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #bfbfbf;
}

.new-template {
  border-style: dashed;
  border-color: #d9d9d9;
}

.new-template-content {
  height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #8c8c8c;
}

.new-template-content :deep(.anticon) {
  font-size: 48px;
  margin-bottom: 16px;
}

.email-stats-panel {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.switch-label {
  margin-left: 8px;
  color: #8c8c8c;
}

.followup-sequence {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sequence-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

@media (max-width: 1200px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .email-automation {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
    padding: 16px;
  }

  .stats-cards {
    grid-template-columns: 1fr;
  }

  .templates-grid {
    grid-template-columns: 1fr;
  }
}
</style>
