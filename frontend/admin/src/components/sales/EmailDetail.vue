/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="email-detail">
    <!-- 邮件头部 -->
    <div class="email-header">
      <div class="email-subject">
        <h3>{{ email.subject }}</h3>
        <a-tag :color="getStatusColor(email.status)">
          {{ getStatusText(email.status) }}
        </a-tag>
      </div>
      <div class="email-meta">
        <div class="meta-item">
          <span class="label">收件人：</span>
          <span class="value">{{ email.recipientName }} &lt;{{ email.recipientEmail }}&gt;</span>
        </div>
        <div class="meta-item">
          <span class="label">发送时间：</span>
          <span class="value">{{ formatDate(email.sentAt) }}</span>
        </div>
        <div class="meta-item">
          <span class="label">邮件类型：</span>
          <a-tag>{{ getTypeText(email.type) }}</a-tag>
        </div>
      </div>
    </div>

    <!-- 邮件内容 -->
    <a-card title="邮件内容" size="small" class="content-card">
      <div class="email-body" v-html="sanitizeHtml(email.body || defaultBody)"></div>
    </a-card>

    <!-- 跟踪信息 -->
    <a-card title="跟踪信息" size="small" class="tracking-card">
      <a-timeline>
        <a-timeline-item
          v-for="event in trackingEvents"
          :key="event.id"
          :color="event.color"
        >
          <div class="event-item">
            <div class="event-title">{{ event.title }}</div>
            <div class="event-time">{{ event.time }}</div>
          </div>
        </a-timeline-item>
      </a-timeline>
    </a-card>

    <!-- 统计信息 -->
    <a-card title="统计信息" size="small" class="stats-card">
      <a-descriptions :column="2" size="small">
        <a-descriptions-item label="打开次数">
          {{ email.openCount || 0 }}
        </a-descriptions-item>
        <a-descriptions-item label="点击次数">
          {{ email.clickCount || 0 }}
        </a-descriptions-item>
        <a-descriptions-item label="首次打开">
          {{ formatDate(email.openedAt) || '-' }}
        </a-descriptions-item>
        <a-descriptions-item label="回复时间">
          {{ formatDate(email.repliedAt) || '-' }}
        </a-descriptions-item>
      </a-descriptions>
    </a-card>

    <!-- 操作按钮 -->
    <div class="actions">
      <a-button type="primary" block @click="handleReply">
        <MessageOutlined />
        回复
      </a-button>
      <a-button block @click="handleResend" v-if="email.status === 'failed'">
        <ReloadOutlined />
        重新发送
      </a-button>
      <a-button block @click="handleForward">
        <ForwardOutlined />
        转发
      </a-button>
      <a-button block @click="handleViewInThread">
        <BranchesOutlined />
        查看对话线程
      </a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { message } from 'ant-design-vue';
import {
  MessageOutlined,
  ReloadOutlined,
  ForwardOutlined,
  BranchesOutlined,
} from '@ant-design/icons-vue';
import { useSanitize } from '@/composables/useSanitize';
import type { Email } from '@/types/sales';

const { sanitizeHtml } = useSanitize();

const props = defineProps<{
  email: Email;
}>();

const emit = defineEmits<{
  (e: 'resend', email: Email): void;
  (e: 'reply', email: Email & { thread?: unknown }): void;
}>();

const defaultBody = `
<p>Dear ${props.email.recipientName},</p>
<p>I hope this email finds you well. I am writing to introduce our premium building materials that could greatly benefit your projects.</p>
<p>We are a leading manufacturer with over 15 years of experience in the industry. Our products are certified by CE, ASTM, and ISO standards.</p>
<p>Key advantages:</p>
<ul>
  <li>Excellent quality with competitive pricing</li>
  <li>Fast delivery within 30 days</li>
  <li>Professional after-sales support</li>
</ul>
<p>Would you be available for a brief call to discuss your requirements?</p>
<p>Best regards,<br/>Your Name</p>
`;

const trackingEvents = ref([
  {
    id: 1,
    title: '邮件已发送',
    time: props.email.sentAt ? formatDate(props.email.sentAt) : '-',
    color: 'blue',
  },
  {
    id: 2,
    title: props.email.openedAt ? '收件人已打开邮件' : '等待打开',
    time: props.email.openedAt ? formatDate(props.email.openedAt) : '-',
    color: props.email.openedAt ? 'green' : 'gray',
  },
  {
    id: 3,
    title: props.email.repliedAt ? '收件人已回复' : '等待回复',
    time: props.email.repliedAt ? formatDate(props.email.repliedAt) : '-',
    color: props.email.repliedAt ? 'green' : 'gray',
  },
]);

function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString('zh-CN');
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    draft: 'default',
    sent: 'blue',
    delivered: 'cyan',
    opened: 'green',
    clicked: 'green',
    replied: 'success',
    failed: 'error',
  };
  return colors[status] || 'default';
}

function getStatusText(status: string): string {
  const texts: Record<string, string> = {
    draft: '草稿',
    sent: '已发送',
    delivered: '已送达',
    opened: '已打开',
    clicked: '已点击',
    replied: '已回复',
    failed: '发送失败',
  };
  return texts[status] || status;
}

function getTypeText(type: string): string {
  const texts: Record<string, string> = {
    cold_outreach: '冷开发信',
    follow_up: '跟进邮件',
    quote: '报价邮件',
    welcome: '欢迎邮件',
    marketing: '营销邮件',
  };
  return texts[type] || type;
}

function handleReply() {
  emit('reply', props.email);
}

function handleResend() {
  emit('resend', props.email);
}

async function handleForward() {
  try {
    await fetch(`${import.meta.env.VITE_API_BASE_URL || '/api'}/v1/sales/emails/${props.email.id}/forward`, {
      method: 'POST',
    });
    message.success('邮件已转发');
  } catch (error) {
    console.error('转发邮件失败:', error);
    message.error('转发邮件失败');
  }
}

async function handleViewInThread() {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || '/api'}/v1/sales/emails/${props.email.id}/thread`);
    if (!response.ok) throw new Error(`API error: ${response.status}`);
    const data = await response.json();
    emit('reply', { ...props.email, thread: data });
  } catch (error) {
    console.error('查看对话线程失败:', error);
    message.error('查看对话线程失败');
  }
}
</script>

<style scoped>
.email-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.email-header {
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
}

.email-subject {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.email-subject h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.email-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.meta-item .label {
  color: #8c8c8c;
  min-width: 70px;
}

.meta-item .value {
  color: #1a1a1a;
}

.content-card,
.tracking-card,
.stats-card {
  border-radius: 8px;
}

.email-body {
  padding: 16px;
  background: #fafafa;
  border-radius: 4px;
  line-height: 1.8;
}

.event-item {
  display: flex;
  flex-direction: column;
}

.event-title {
  font-weight: 500;
}

.event-time {
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
