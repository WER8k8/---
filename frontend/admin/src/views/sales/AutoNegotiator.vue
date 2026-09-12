<template>
  <YdPage surface="elevated">
    <template #actions>
      <a-badge :count="pendingInquiries" :offset="[-5, 5]">
        <a-button type="primary" @click="() => refreshInquiries()">
          <ReloadOutlined />
          刷新询盘
        </a-button>
      </a-badge>
      <a-button @click="showSettingsModal = true">
        <SettingOutlined />
        谈判设置
      </a-button>
    </template>
  <div class="auto-negotiator">
      <a-alert
        v-if="pageLoadError"
        type="error"
        show-icon
        class="mb-4"
        :message="pageLoadError"
        closable
        @close="pageLoadError = ''"
      />
      <a-card class="worker-setup-card" title="抖音评论怎么进来（5c）" size="small">
        <p class="text-sm text-gray-600 mb-2">
          先绑抖音并发视频，再点「拉取评论」；也可把导出文件放到运维 Inbox 目录。
        </p>
        <div class="flex flex-wrap gap-2 items-center">
          <a-button size="small" :loading="workerPulling" @click="pullDouyinComments">拉取评论</a-button>
          <a-button size="small" :loading="workerRehearsalLoading" @click="rehearsalIngestComments">投递测试评论（5c）</a-button>
          <a-button size="small" type="link" @click="$router.push('/inquiries/im-routing#wecom-push')">
            去配销售通知（5b）
          </a-button>
          <a-tag v-if="workerConfig?.secret_configured" color="success">Webhook 已配密钥</a-tag>
          <a-tag v-else color="warning">Webhook 密钥待运维配置</a-tag>
        </div>
      </a-card>

      <!-- 统计卡片 -->
      <div class="stats-cards">
        <a-card class="stat-card">
          <a-statistic
            title="进行中谈判"
            :value="stats.activeNegotiations"
            :value-style="{ color: '#1890ff' }"
          >
            <template #prefix><MessageOutlined /></template>
          </a-statistic>
        </a-card>
        <a-card class="stat-card">
          <a-statistic
            title="今日询盘"
            :value="stats.todayInquiries"
            :value-style="{ color: '#52c41a' }"
          >
            <template #prefix><InboxOutlined /></template>
          </a-statistic>
        </a-card>
        <a-card class="stat-card">
          <a-statistic
            title="待审批报价"
            :value="stats.pendingApproval"
            :value-style="{ color: '#faad14' }"
          >
            <template #prefix><ClockCircleOutlined /></template>
          </a-statistic>
        </a-card>
        <a-card class="stat-card">
          <a-statistic
            title="本月成交"
            :value="stats.monthlyDeals"
            :value-style="{ color: '#722ed1' }"
          >
            <template #prefix><TrophyOutlined /></template>
          </a-statistic>
        </a-card>
      </div>

      <!-- 主要内容区 -->
      <div class="main-content">
        <!-- 左侧：谈判列表 -->
        <div class="negotiation-list">
          <a-card class="list-card">
            <template #title>
              <a-tabs v-model:activeKey="activeTab" size="small">
                <a-tab-pane key="active" tab="进行中" />
                <a-tab-pane key="pending" tab="待处理" />
                <a-tab-pane key="completed" tab="已完成" />
              </a-tabs>
            </template>
            <template #extra>
              <a-input-search
                v-model:value="searchQuery"
                placeholder="搜索谈判..."
                style="width: 200px"
                @search="handleSearch"
              />
            </template>

            <a-list
              :data-source="filteredNegotiations"
              :loading="loading"
              class="negotiation-items"
            >
              <template #renderItem="{ item }">
                <a-list-item
                  :class="{ active: selectedNegotiation?.id === item.id }"
                  @click="selectNegotiation(item)"
                >
                  <a-list-item-meta>
                    <template #avatar>
                      <a-avatar :style="{ backgroundColor: getAvatarColor(item.status) }">
                        {{ item.customerName.charAt(0) }}
                      </a-avatar>
                    </template>
                    <template #title>
                      <div class="item-title">
                        <span class="customer-name">{{ item.customerName }}</span>
                        <a-tag :color="getStatusColor(item.status)" size="small">
                          {{ getStatusText(item.status) }}
                        </a-tag>
                      </div>
                    </template>
                    <template #description>
                      <div class="item-desc">
                        <div class="product">{{ item.product }}</div>
                        <div class="last-message">{{ item.lastMessage }}</div>
                        <div class="meta">
                          <span class="round">第{{ item.round }}轮</span>
                          <span class="time">{{ formatTime(item.updatedAt) }}</span>
                        </div>
                      </div>
                    </template>
                  </a-list-item-meta>
                  <template #actions>
                    <a-badge v-if="item.unread" :count="item.unread" />
                  </template>
                </a-list-item>
              </template>
            </a-list>
          </a-card>
        </div>

        <!-- 右侧：谈判详情 -->
        <div class="negotiation-detail">
          <a-card v-if="selectedNegotiation" class="detail-card">
            <!-- 谈判头部 -->
            <div class="detail-header">
              <div class="customer-info">
                <a-avatar size="large" :style="{ backgroundColor: '#1890ff' }">
                  {{ selectedNegotiation.customerName.charAt(0) }}
                </a-avatar>
                <div class="info-text">
                  <div class="name">{{ selectedNegotiation.customerName }}</div>
                  <div class="email">{{ selectedNegotiation.customerEmail }}</div>
                </div>
              </div>
              <div class="negotiation-meta">
                <a-descriptions :column="3" size="small">
                  <a-descriptions-item label="产品">
                    {{ selectedNegotiation.product }}
                  </a-descriptions-item>
                  <a-descriptions-item label="数量">
                    {{ selectedNegotiation.quantity }} {{ selectedNegotiation.unit }}
                  </a-descriptions-item>
                  <a-descriptions-item label="目的地">
                    {{ selectedNegotiation.destination }}
                  </a-descriptions-item>
                </a-descriptions>
              </div>
            </div>

            <!-- 对话区域 -->
            <div class="conversation-area">
              <div class="messages" ref="messagesContainer">
                <div
                  v-for="msg in selectedNegotiation.messages"
                  :key="msg.id"
                  :class="['message', msg.sender === 'customer' ? 'customer' : 'ai']"
                >
                  <div class="message-avatar">
                    <a-avatar
                      size="small"
                      :style="{ backgroundColor: msg.sender === 'customer' ? '#faad14' : '#1890ff' }"
                    >
                      {{ msg.sender === 'customer' ? '客' : 'AI' }}
                    </a-avatar>
                  </div>
                  <div class="message-content">
                    <div class="message-bubble">
                      <div class="message-text">{{ msg.content }}</div>
                      <div v-if="msg.quote" class="message-quote">
                        <a-descriptions :column="2" size="small">
                          <a-descriptions-item label="单价">
                            ${{ msg.quote.unitPrice }}
                          </a-descriptions-item>
                          <a-descriptions-item label="总价">
                            ${{ msg.quote.totalPrice }}
                          </a-descriptions-item>
                          <a-descriptions-item label="交货期">
                            {{ msg.quote.deliveryTime }}
                          </a-descriptions-item>
                          <a-descriptions-item label="有效期">
                            {{ msg.quote.validUntil }}
                          </a-descriptions-item>
                        </a-descriptions>
                      </div>
                    </div>
                    <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 操作区域 -->
            <div class="action-area">
              <div class="ai-suggestion" v-if="aiSuggestion">
                <div class="suggestion-header">
                  <RobotOutlined />
                  <span>AI建议回复</span>
                </div>
                <div class="suggestion-content">{{ aiSuggestion }}</div>
                <div class="suggestion-actions">
                  <a-button size="small" @click="useAISuggestion">使用此回复</a-button>
                  <a-button size="small" @click="regenerateSuggestion">重新生成</a-button>
                </div>
              </div>

              <div class="input-area">
                <a-textarea
                  v-model:value="replyContent"
                  placeholder="输入回复内容..."
                  :rows="3"
                  :disabled="selectedNegotiation.status === 'completed'"
                />
                <div class="input-actions">
                  <a-space>
                    <a-button @click="generateQuote">
                      <DollarOutlined />
                      生成报价
                    </a-button>
                    <a-button @click="askApproval" :disabled="!needsApproval">
                      <CheckCircleOutlined />
                      请求审批
                    </a-button>
                    <a-button type="primary" @click="sendReply" :loading="sending">
                      <SendOutlined />
                      发送回复
                    </a-button>
                  </a-space>
                </div>
              </div>
            </div>
          </a-card>

          <!-- 空状态 -->
          <a-empty v-else description="请选择一个谈判对话" />
        </div>
      </div>

      <!-- 设置弹窗 -->
      <a-modal
        v-model:open="showSettingsModal"
        title="自动谈单设置"
        width="600px"
        @ok="saveSettings"
      >
        <a-form :model="settings" layout="vertical">
          <a-form-item label="基础利润率 (%)">
            <a-slider v-model:value="settings.baseProfitMargin" :min="5" :max="50" />
          </a-form-item>
          <a-form-item label="最大谈判轮数">
            <a-input-number v-model:value="settings.maxRounds" :min="1" :max="10" />
          </a-form-item>
          <a-form-item label="自动回复">
            <a-switch v-model:checked="settings.autoReply" />
            <span class="switch-label">开启后AI将自动回复询盘</span>
          </a-form-item>
          <a-form-item label="需要人工审批">
            <a-switch v-model:checked="settings.requireApproval" />
            <span class="switch-label">最终报价需要人工确认</span>
          </a-form-item>
          <a-form-item label="工作时间">
            <a-time-range-picker v-model:value="settings.workingHours" format="HH:mm" />
          </a-form-item>
        </a-form>
      </a-modal>

      <!-- 报价生成弹窗 -->
      <a-modal
        v-model:open="showQuoteModal"
        title="生成报价"
        width="700px"
        @ok="submitQuote"
      >
        <a-form :model="quoteForm" layout="vertical">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="产品名称">
                <a-input v-model:value="quoteForm.productName" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="数量">
                <a-input-number v-model:value="quoteForm.quantity" :min="1" style="width: 100%" />
              </a-form-item>
            </a-col>
          </a-row>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="基础成本 (USD)">
                <a-input-number
                  v-model:value="quoteForm.baseCost"
                  :min="0"
                  :precision="2"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="利润率 (%)">
                <a-input-number
                  v-model:value="quoteForm.profitMargin"
                  :min="0"
                  :max="100"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
          </a-row>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="交货期">
                <a-select v-model:value="quoteForm.deliveryTime" :options="deliveryOptions" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="付款方式">
                <a-select v-model:value="quoteForm.paymentTerms" :options="paymentOptions" />
              </a-form-item>
            </a-col>
          </a-row>
          <a-form-item label="报价预览">
            <a-card size="small">
              <a-descriptions :column="2" size="small">
                <a-descriptions-item label="单价">
                  ${{ calculatedUnitPrice.toFixed(2) }}
                </a-descriptions-item>
                <a-descriptions-item label="总价">
                  ${{ calculatedTotalPrice.toFixed(2) }}
                </a-descriptions-item>
                <a-descriptions-item label="数量折扣">
                  {{ quantityDiscount }}%
                </a-descriptions-item>
                <a-descriptions-item label="最终报价">
                  ${{ finalPrice.toFixed(2) }}
                </a-descriptions-item>
              </a-descriptions>
            </a-card>
          </a-form-item>
        </a-form>
      </a-modal>
  </div>
  </YdPage>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue';
import { message, Modal } from 'ant-design-vue';
import { YdPage } from '@/components/youding';
import {
  MessageOutlined,
  ReloadOutlined,
  SettingOutlined,
  InboxOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  RobotOutlined,
  DollarOutlined,
  CheckCircleOutlined,
  SendOutlined,
} from '@ant-design/icons-vue';
import type { Negotiation, QuoteForm, NegotiationSettings } from '@/types/sales';
import { apiFetch } from '@/utils/api';

async function parseApiJson(response: Response): Promise<Record<string, unknown>> {
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  const text = await response.text();
  if (!text.trim()) {
    throw new Error('空响应');
  }
  return JSON.parse(text) as Record<string, unknown>;
}

// 统计数据（来自 social-interactions/summary，禁止硬编码假数）
const stats = reactive({
  activeNegotiations: 0,
  todayInquiries: 0,
  pendingApproval: 0,
  monthlyDeals: 0,
});

// 状态
const loading = ref(false);
const pageLoadError = ref('');
const workerPulling = ref(false);
const workerRehearsalLoading = ref(false);
const workerConfig = ref<{ secret_configured?: boolean; client_pull_url?: string } | null>(null);
const sending = ref(false);
const activeTab = ref('active');
const searchQuery = ref('');
const selectedNegotiation = ref<Negotiation | null>(null);
const showSettingsModal = ref(false);
const showQuoteModal = ref(false);
const replyContent = ref('');
const messagesContainer = ref<HTMLElement | null>(null);

// 谈判列表
const negotiations = ref<Negotiation[]>([]);

// 设置
const settings = reactive<NegotiationSettings>({
  baseProfitMargin: 15,
  maxRounds: 5,
  autoReply: true,
  requireApproval: true,
  workingHours: null,
});

// 报价表单
const quoteForm = reactive<QuoteForm>({
  productName: '',
  quantity: 1,
  baseCost: 0,
  profitMargin: 15,
  deliveryTime: '30天',
  paymentTerms: 'T/T 30%',
});

// 选项
const deliveryOptions = [
  { label: '15天', value: '15天' },
  { label: '30天', value: '30天' },
  { label: '45天', value: '45天' },
  { label: '60天', value: '60天' },
];

const paymentOptions = [
  { label: 'T/T 30%定金', value: 'T/T 30%' },
  { label: 'T/T 50%定金', value: 'T/T 50%' },
  { label: 'L/C 即期', value: 'L/C at sight' },
  { label: 'D/P 即期', value: 'D/P at sight' },
];

// 计算属性
const pendingInquiries = computed(() => {
  return negotiations.value.filter(n => n.status === 'pending').length;
});

const filteredNegotiations = computed(() => {
  let result = negotiations.value;

  // 按状态筛选
  if (activeTab.value === 'active') {
    result = result.filter(n => n.status === 'in_progress');
  } else if (activeTab.value === 'pending') {
    result = result.filter(n => n.status === 'pending');
  } else if (activeTab.value === 'completed') {
    result = result.filter(n => n.status === 'completed');
  }

  // 按搜索词筛选
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(
      n =>
        n.customerName.toLowerCase().includes(query) ||
        n.product.toLowerCase().includes(query)
    );
  }

  return result;
});

const aiSuggestion = ref<string | null>(null);

async function fetchAiSuggestion() {
  if (!selectedNegotiation.value) return;
  const draft = (selectedNegotiation.value as Negotiation & { draft_reply?: string }).draft_reply;
  if (draft) {
    aiSuggestion.value = draft;
    return;
  }
  aiSuggestion.value = null;
}

const needsApproval = ref(false);

async function checkApprovalStatus() {
  if (!selectedNegotiation.value) return;
  try {
    const response = await apiFetch(
      `/api/v1/negotiation/${selectedNegotiation.value.id}/approval-status`,
    );
    const result = await response.json();
    if (result.code === 0) {
      needsApproval.value = result.data.needs_approval;
    }
  } catch (error) {
    if (import.meta.env.DEV) console.error('检查审批状态失败:', error);
  }
}

const calculatedUnitPrice = computed(() => {
  return quoteForm.baseCost * (1 + quoteForm.profitMargin / 100);
});

const calculatedTotalPrice = computed(() => {
  return calculatedUnitPrice.value * quoteForm.quantity;
});

const quantityDiscount = computed(() => {
  if (quoteForm.quantity >= 50000) return 10;
  if (quoteForm.quantity >= 10000) return 8;
  if (quoteForm.quantity >= 5000) return 5;
  if (quoteForm.quantity >= 1000) return 2;
  return 0;
});

const finalPrice = computed(() => {
  return calculatedTotalPrice.value * (1 - quantityDiscount.value / 100);
});

// 方法
function getAvatarColor(status: string): string {
  const colors: Record<string, string> = {
    pending: '#faad14',
    in_progress: '#1890ff',
    completed: '#52c41a',
    failed: '#ff4d4f',
  };
  return colors[status] || '#d9d9d9';
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: 'orange',
    in_progress: 'blue',
    completed: 'green',
    failed: 'red',
  };
  return colors[status] || 'default';
}

function getStatusText(status: string): string {
  const texts: Record<string, string> = {
    pending: '待处理',
    in_progress: '进行中',
    completed: '已完成',
    failed: '已失败',
  };
  return texts[status] || status;
}

function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  if (diff < 60000) return '刚刚';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
  return date.toLocaleDateString('zh-CN');
}

function selectNegotiation(negotiation: Negotiation) {
  selectedNegotiation.value = negotiation;
  fetchAiSuggestion();
  checkApprovalStatus();
  nextTick(() => {
    scrollToBottom();
  });
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
}

async function loadSummary() {
  try {
    const response = await apiFetch('/api/v1/social-interactions/summary');
    const result = await parseApiJson(response);
    if (result.code === 0 && result.data && typeof result.data === 'object') {
      const data = result.data as Record<string, unknown>;
      stats.activeNegotiations = Number(data.active_negotiations ?? 0);
      stats.todayInquiries = Number(data.today_inquiries ?? 0);
      stats.pendingApproval = Number(data.pending_approval ?? 0);
      stats.monthlyDeals = Number(data.monthly_deals ?? 0);
    }
  } catch (error) {
    if (import.meta.env.DEV) console.error('加载统计失败:', error);
  }
}

async function refreshInquiries(options?: { silent?: boolean }) {
  loading.value = true;
  pageLoadError.value = '';
  try {
    const [listRes] = await Promise.all([
      apiFetch('/api/v1/social-interactions/negotiations'),
      loadSummary(),
    ]);
    const result = await parseApiJson(listRes);

    if (result.code === 0) {
      const data = (result.data || {}) as Record<string, unknown>;
      negotiations.value = ((data.negotiations as Record<string, unknown>[]) || []).map((n) => ({
        id: String(n.id),
        customerName: String(n.customerName || n.customer_name || '访客'),
        customerEmail: String(n.customerEmail || ''),
        product: String(n.product || ''),
        quantity: Number(n.quantity || 1),
        unit: String(n.unit || '批'),
        destination: String(n.destination || ''),
        status: n.status as Negotiation['status'],
        round: Number(n.round || 1),
        unread: Number(n.unread || 0),
        lastMessage: String(n.lastMessage || n.last_message || ''),
        updatedAt: String(n.updatedAt || n.updated_at || ''),
        messages: (n.messages as Negotiation['messages']) || [],
        draft_reply: n.draft_reply as string | undefined,
      }));
      if (!options?.silent) {
        message.success(`已加载 ${negotiations.value.length} 个谈判`);
      }
    } else {
      pageLoadError.value =
        result.code === 401
          ? '登录已失效，请重新登录后再试'
          : (typeof result.message === 'string' ? result.message : '加载失败');
    }
  } catch (error) {
    if (import.meta.env.DEV) console.error('加载谈判失败:', error);
    pageLoadError.value = '加载失败，请重试';
  } finally {
    loading.value = false;
  }
}

function handleSearch() {
  // 搜索逻辑已在 computed 中处理
}

function useAISuggestion() {
  replyContent.value = aiSuggestion.value || '';
}

async function regenerateSuggestion() {
  if (!selectedNegotiation.value) return;
  try {
    const response = await apiFetch(
      `/api/v1/social-interactions/${selectedNegotiation.value.id}/regenerate-draft`,
      { method: 'POST' },
    );
    const result = await response.json();
    if (result.code === 0) {
      aiSuggestion.value = result.data.draft_reply || '';
      (selectedNegotiation.value as Negotiation & { draft_reply?: string }).draft_reply =
        result.data.draft_reply;
      message.success('新建议已生成');
    } else {
      message.error(result.message || '重新生成建议失败');
    }
  } catch (error) {
    if (import.meta.env.DEV) console.error('重新生成AI建议失败:', error);
    message.error('重新生成失败，请重试');
  }
}

function generateQuote() {
  if (selectedNegotiation.value) {
    quoteForm.productName = selectedNegotiation.value.product;
    quoteForm.quantity = selectedNegotiation.value.quantity;
  }
  showQuoteModal.value = true;
}

async function submitQuote() {
  if (!selectedNegotiation.value) return;

  const quoteText = `报价详情：
- 产品：${quoteForm.productName}
- 数量：${quoteForm.quantity}
- 单价：$${calculatedUnitPrice.value.toFixed(2)}
- 总价：$${finalPrice.value.toFixed(2)}
- 交货期：${quoteForm.deliveryTime}
- 付款方式：${quoteForm.paymentTerms}`;

  try {
    const response = await apiFetch(
      `/api/v1/negotiation/${selectedNegotiation.value.id}/quote`,
      {
        method: 'POST',
        body: JSON.stringify({
          product_name: quoteForm.productName,
          quantity: quoteForm.quantity,
          base_cost: quoteForm.baseCost,
          profit_margin: quoteForm.profitMargin,
          delivery_time: quoteForm.deliveryTime,
          payment_terms: quoteForm.paymentTerms,
          unit_price: calculatedUnitPrice.value,
          total_price: finalPrice.value,
        }),
      }
    );
    const result = await response.json();
    if (result.code === 0) {
      replyContent.value = quoteText;
      showQuoteModal.value = false;
      message.success('报价已提交');
    } else {
      message.error(result.message || '报价提交失败');
    }
  } catch (error) {
    if (import.meta.env.DEV) console.error('提交报价失败:', error);
    message.error('提交失败，请重试');
  }
}

async function askApproval() {
  if (!selectedNegotiation.value) return;
  try {
    const response = await apiFetch(
      `/api/v1/negotiation/${selectedNegotiation.value.id}/request-approval`,
      {
        method: 'POST',
        body: JSON.stringify({
          negotiation_id: selectedNegotiation.value.id,
          round: selectedNegotiation.value.round,
        }),
      }
    );
    const result = await response.json();
    if (result.code === 0) {
      message.success('已提交审批请求');
    } else {
      message.error(result.message || '提交审批请求失败');
    }
  } catch (error) {
    if (import.meta.env.DEV) console.error('提交审批请求失败:', error);
    message.error('提交失败，请重试');
  }
}

async function sendReply() {
  if (!replyContent.value.trim()) {
    message.warning('请输入回复内容');
    return;
  }

  if (!selectedNegotiation.value) {
    message.warning('请先选择一个谈判');
    return;
  }

  sending.value = true;
  try {
    const id = selectedNegotiation.value.id;
    const approveRes = await apiFetch(`/api/v1/social-interactions/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ final_reply: replyContent.value }),
    });
    const approveResult = await approveRes.json();
    if (approveResult.code !== 0) {
      message.error(approveResult.message || '批准草稿失败');
      return;
    }

    message.info('请先在抖音侧发送回复，再填写平台回执 ID');

    Modal.confirm({
      title: '确认平台已发送',
      content: '请输入抖音返回的消息/任务 ID（无回执不能标记已发送）',
      okText: '提交回执',
      cancelText: '稍后',
      onOk: async () => {
        const receipt = window.prompt('平台回执 ID（必填）');
        if (!receipt?.trim()) {
          message.warning('未填写回执，状态保持为已批准');
          return;
        }
        const sentRes = await apiFetch(`/api/v1/social-interactions/${id}/mark-sent`, {
          method: 'POST',
          body: JSON.stringify({ platform_receipt_id: receipt.trim() }),
        });
        const sentResult = await sentRes.json();
        if (sentResult.code === 0) {
          selectedNegotiation.value?.messages.push({
            id: `msg_${Date.now()}`,
            sender: 'user',
            content: replyContent.value,
            timestamp: new Date().toISOString(),
          });
          replyContent.value = '';
          message.success('已记录平台发送回执');
          await refreshInquiries();
          nextTick(() => scrollToBottom());
        } else {
          message.error(sentResult.message || '回执提交失败');
        }
      },
    });
  } catch (error) {
    if (import.meta.env.DEV) console.error('发送回复失败:', error);
    message.error('发送失败，请重试');
  } finally {
    sending.value = false;
  }
}

async function saveSettings() {
  try {
    const response = await apiFetch('/api/v1/negotiation/settings', {
      method: 'PUT',
      body: JSON.stringify({
        base_profit_margin: settings.baseProfitMargin,
        max_rounds: settings.maxRounds,
        auto_reply: settings.autoReply,
        require_approval: settings.requireApproval,
        working_hours: settings.workingHours,
      }),
    });
    const result = await response.json();
    if (result.code === 0) {
      showSettingsModal.value = false;
      message.success('设置已保存');
    } else {
      message.error(result.message || '保存设置失败');
    }
  } catch (error) {
    if (import.meta.env.DEV) console.error('保存设置失败:', error);
    message.error('保存失败，请重试');
  }
}

async function loadWorkerConfig() {
  try {
    const response = await apiFetch('/api/v1/social-interactions/worker/config');
    const result = await response.json();
    if (result.code === 0 && result.data) {
      workerConfig.value = result.data;
    }
  } catch {
    workerConfig.value = null;
  }
}

async function pullDouyinComments() {
  workerPulling.value = true;
  try {
    const response = await apiFetch('/api/v1/client/douyin-comments/pull', {
      method: 'POST',
    });
    const result = await response.json();
    if (result.code === 0) {
      const n = result.data?.ingested ?? 0;
      message.success(
        n > 0
          ? `已拉取 ${n} 条评论`
          : (result.message || '暂无新评论；可点「投递测试评论」在开发环境彩排'),
      );
      await refreshInquiries();
    } else {
      message.warning(result.message || '拉取失败');
    }
  } catch {
    message.error('拉取失败，请稍后重试');
  } finally {
    workerPulling.value = false;
  }
}

async function rehearsalIngestComments() {
  workerRehearsalLoading.value = true;
  try {
    const response = await apiFetch('/api/v1/client/douyin-comments/rehearsal-ingest', {
      method: 'POST',
    });
    const result = await response.json();
    if (result.code === 0) {
      const n = result.data?.ingested ?? 0;
      message.success(n > 0 ? `已投递 ${n} 条测试评论` : (result.message || '未入库'));
      await refreshInquiries();
    } else {
      message.warning(result.message || '投递失败');
    }
  } catch {
    message.error('投递失败，请稍后重试');
  } finally {
    workerRehearsalLoading.value = false;
  }
}

onMounted(async () => {
  await loadWorkerConfig();
  await refreshInquiries({ silent: true });
  if (negotiations.value.length > 0) {
    selectNegotiation(negotiations.value[0]);
  }
});
</script>

<style scoped>
.auto-negotiator {
  padding: 24px;
  background: #f5f5f5;
  min-height: calc(100vh - 64px);
}

.worker-setup-card {
  margin-bottom: 16px;
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

.main-content {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 24px;
  height: calc(100vh - 350px);
  min-height: 500px;
}

.negotiation-list {
  height: 100%;
}

.list-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.list-card :deep(.ant-card-body) {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.negotiation-items {
  flex: 1;
  overflow-y: auto;
}

.negotiation-items .ant-list-item {
  cursor: pointer;
  transition: background-color 0.3s;
}

.negotiation-items .ant-list-item:hover {
  background-color: #f5f5f5;
}

.negotiation-items .ant-list-item.active {
  background-color: #e6f7ff;
}

.item-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.customer-name {
  font-weight: 500;
}

.item-desc {
  font-size: 12px;
}

.product {
  color: #1890ff;
  margin-bottom: 4px;
}

.last-message {
  color: #8c8c8c;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.meta {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  color: #bfbfbf;
}

.negotiation-detail {
  height: 100%;
}

.detail-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.detail-card :deep(.ant-card-body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.detail-header {
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 16px;
}

.customer-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.info-text .name {
  font-size: 16px;
  font-weight: 500;
}

.info-text .email {
  font-size: 12px;
  color: #8c8c8c;
}

.conversation-area {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.message.customer {
  flex-direction: row;
}

.message.ai {
  flex-direction: row-reverse;
}

.message-content {
  max-width: 70%;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  background: #fff;
}

.message.ai .message-bubble {
  background: #1890ff;
  color: #fff;
}

.message-text {
  line-height: 1.6;
}

.message-quote {
  margin-top: 12px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 8px;
}

.message-time {
  margin-top: 4px;
  font-size: 11px;
  color: #8c8c8c;
}

.action-area {
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.ai-suggestion {
  margin-bottom: 16px;
  padding: 12px;
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 8px;
}

.suggestion-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-weight: 500;
  color: #52c41a;
}

.suggestion-content {
  margin-bottom: 12px;
  font-size: 14px;
  color: #1a1a1a;
}

.suggestion-actions {
  display: flex;
  gap: 8px;
}

.input-area {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
}

.switch-label {
  margin-left: 8px;
  color: #8c8c8c;
}

@media (max-width: 1200px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }

  .main-content {
    grid-template-columns: 1fr;
    height: auto;
  }

  .negotiation-list {
    height: 400px;
  }

  .negotiation-detail {
    height: 600px;
  }
}

@media (max-width: 768px) {
  .auto-negotiator {
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
}
</style>
