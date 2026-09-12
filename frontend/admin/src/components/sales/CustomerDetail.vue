<template>
  <div class="customer-detail">
    <!-- 客户基本信息 -->
    <div class="customer-header">
      <a-avatar size="large" :style="{ backgroundColor: getAvatarColor(customer.score) }">
        {{ customer.name.charAt(0) }}
      </a-avatar>
      <div class="customer-info">
        <h2 class="customer-name">{{ customer.name }}</h2>
        <div class="customer-company">{{ customer.company }}</div>
        <a-space class="customer-tags">
          <a-tag :color="getStatusColor(customer.status)">
            {{ getStatusText(customer.status) }}
          </a-tag>
          <a-tag color="blue">{{ customer.score }}分</a-tag>
        </a-space>
      </div>
    </div>

    <!-- 联系信息 -->
    <a-card title="联系信息" size="small" class="info-card">
      <a-descriptions :column="1" size="small">
        <a-descriptions-item label="邮箱">
          <a :href="`mailto:${customer.email}`">{{ customer.email }}</a>
        </a-descriptions-item>
        <a-descriptions-item label="电话">
          <a :href="`tel:${customer.phone}`">{{ customer.phone }}</a>
        </a-descriptions-item>
        <a-descriptions-item label="WhatsApp">
          <template v-if="customer.whatsappNumber">
            <a :href="`https://wa.me/${customer.whatsappNumber}`" target="_blank" class="whatsapp-link">
              <CommentOutlined /> {{ customer.whatsappNumber }}
            </a>
          </template>
          <span v-else class="text-muted">暂无 WhatsApp</span>
        </a-descriptions-item>
        <a-descriptions-item label="网站">
          <a :href="customer.website" target="_blank">{{ customer.website }}</a>
        </a-descriptions-item>
        <a-descriptions-item label="国家">
          {{ customer.country }}
        </a-descriptions-item>
        <a-descriptions-item label="行业">
          {{ customer.industry }}
        </a-descriptions-item>
      </a-descriptions>
    </a-card>

    <!-- 评分详情 -->
    <a-card title="评分详情" size="small" class="info-card">
      <div class="score-breakdown">
        <div class="score-item">
          <span class="score-label">关键词匹配</span>
          <a-progress :percent="customer.keywordScore || 85" size="small" />
        </div>
        <div class="score-item">
          <span class="score-label">目标国家</span>
          <a-progress :percent="customer.countryScore || 90" size="small" />
        </div>
        <div class="score-item">
          <span class="score-label">行业匹配</span>
          <a-progress :percent="customer.industryScore || 75" size="small" />
        </div>
        <div class="score-item">
          <span class="score-label">联系方式完整度</span>
          <a-progress :percent="customer.contactScore || 100" size="small" />
        </div>
        <div class="score-item">
          <span class="score-label">公司规模</span>
          <a-progress :percent="customer.sizeScore || 60" size="small" />
        </div>
      </div>
    </a-card>

    <!-- 联系历史 -->
    <a-card title="联系历史" size="small" class="info-card">
      <a-timeline>
        <a-timeline-item
          v-for="history in contactHistory"
          :key="history.id"
          :color="history.color"
        >
          <div class="history-item">
            <div class="history-title">{{ history.title }}</div>
            <div class="history-time">{{ history.time }}</div>
          </div>
        </a-timeline-item>
      </a-timeline>
    </a-card>

    <!-- 备注 -->
    <a-card title="备注" size="small" class="info-card">
      <a-textarea
        v-model:value="notes"
        :rows="3"
        placeholder="添加客户备注..."
        @blur="saveNotes"
      />
    </a-card>

    <!-- 操作按钮 -->
    <div class="actions">
      <a-button type="primary" block @click="handleSendEmail">
        <MailOutlined />
        发送开发信
      </a-button>
      <a-button type="primary" block @click="handleSendWhatsApp">
        <CommentOutlined />
        发送 WhatsApp
      </a-button>
      <a-button block @click="handleStartNegotiation">
        <MessageOutlined />
        开始谈判
      </a-button>
      <a-button block @click="handleUpdateStatus">
        <EditOutlined />
        更新状态
      </a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { MailOutlined, MessageOutlined, EditOutlined, CommentOutlined } from '@ant-design/icons-vue';
import type { Customer } from '@/types/sales';

const props = defineProps<{
  customer: Customer;
}>();

const emit = defineEmits<{
  (e: 'send-email', customer: Customer): void;
  (e: 'update-status', customer: Customer, status: string): void;
}>();

const notes = ref('');
const contactHistory = ref([
  {
    id: 1,
    title: '查看了公司网站',
    time: '2026-05-26 14:30',
    color: 'blue',
  },
  {
    id: 2,
    title: '打开了开发信邮件',
    time: '2026-05-25 10:15',
    color: 'green',
  },
  {
    id: 3,
    title: '首次采集入库',
    time: '2026-05-24 09:00',
    color: 'gray',
  },
]);

function getAvatarColor(score: number): string {
  if (score >= 80) return '#52c41a';
  if (score >= 60) return '#1890ff';
  if (score >= 40) return '#faad14';
  return '#d9d9d9';
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    new: 'blue',
    contacted: 'orange',
    qualified: 'green',
    converted: 'purple',
  };
  return colors[status] || 'default';
}

function getStatusText(status: string): string {
  const texts: Record<string, string> = {
    new: '新客户',
    contacted: '已联系',
    qualified: '已认证',
    converted: '已转化',
  };
  return texts[status] || status;
}

function handleSendEmail() {
  emit('send-email', props.customer);
}

function handleSendWhatsApp() {
  const whatsappNumber = props.customer.whatsappNumber || props.customer.phone;
  if (!whatsappNumber) {
    message.warning('该客户暂无 WhatsApp 号码');
    return;
  }
  const messageText = `Hi ${props.customer.name}! This is from your supplier. We are professional ${props.customer.industry || 'building materials'} manufacturer from China with 15+ years experience. Can I share our product catalog with you?`;
  const encodedMessage = encodeURIComponent(messageText);
  window.open(`https://wa.me/${whatsappNumber}?text=${encodedMessage}`, '_blank');
}

function handleStartNegotiation() {
  message.info('准备开始谈判...');
}

async function handleUpdateStatus() {
  try {
    const newStatus = props.customer.status === 'new' ? 'contacted' : props.customer.status === 'contacted' ? 'qualified' : 'converted';
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || '/api'}/v1/sales/customers/${props.customer.id}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus }),
    });
    if (!response.ok) throw new Error(`API error: ${response.status}`);
    message.success(`客户状态已更新为: ${newStatus}`);
    emit('update-status', props.customer, newStatus);
  } catch (error) {
    console.error('更新客户状态失败:', error);
    message.error('更新客户状态失败');
  }
}

function saveNotes() {
  if (notes.value) {
    message.success('备注已保存');
  }
}

onMounted(() => {
  notes.value = props.customer.notes || '';
});
</script>

<style scoped>
.customer-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.customer-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
}

.customer-info {
  flex: 1;
}

.customer-name {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
}

.customer-company {
  margin-bottom: 8px;
  font-size: 14px;
  color: #8c8c8c;
}

.customer-tags {
  display: flex;
  gap: 8px;
}

.info-card {
  border-radius: 8px;
}

.score-breakdown {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.score-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.score-label {
  min-width: 120px;
  font-size: 12px;
  color: #8c8c8c;
}

.history-item {
  display: flex;
  flex-direction: column;
}

.history-title {
  font-weight: 500;
}

.history-time {
  font-size: 12px;
  color: #8c8c8c;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 16px;
}
</style>
