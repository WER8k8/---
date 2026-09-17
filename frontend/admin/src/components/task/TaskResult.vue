/**
 * Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
 */
<template>
  <div class="task-result">
    <div class="result-header">
      <h3 class="result-title">任务结果</h3>
      <div class="result-meta">
        <a-tag :color="resultTypeColor">{{ resultTypeText }}</a-tag>
        <span class="result-time" v-if="executionTime">
          执行时间: {{ formatExecutionTime(executionTime) }}
        </span>
      </div>
    </div>
    
    <div class="result-summary" v-if="result.summary">
      <h4>结果摘要</h4>
      <p>{{ result.summary }}</p>
    </div>
    
    <div class="result-content">
      <h4>详细结果</h4>
      
      <!-- 客户列表类型 -->
      <div v-if="result.type === 'customer_list'" class="customer-list">
        <a-table
          :data-source="result.data"
          :columns="customerColumns"
          :pagination="{ pageSize: 10 }"
          size="small"
        />
      </div>
      
      <!-- 邮件草稿类型 -->
      <div v-else-if="result.type === 'email_draft'" class="email-draft">
        <div class="email-header">
          <div class="email-field">
            <span class="field-label">收件人:</span>
            <span class="field-value">{{ result.data.to }}</span>
          </div>
          <div class="email-field">
            <span class="field-label">主题:</span>
            <span class="field-value">{{ result.data.subject }}</span>
          </div>
        </div>
        <div class="email-body" v-html="sanitizeHtml(result.data.body)" />
      </div>
      
      <!-- 研究报告类型 -->
      <div v-else-if="result.type === 'research_report'" class="research-report">
        <div class="report-content" v-html="sanitizeHtml(renderMarkdown(result.data.content))" />
      </div>
      
      <!-- 分析结果类型 -->
      <div v-else-if="result.type === 'analysis'" class="analysis-result">
        <a-tabs>
          <a-tab-pane key="overview" tab="概览">
            <div class="analysis-overview" v-html="sanitizeHtml(renderMarkdown(result.data.overview))" />
          </a-tab-pane>
          <a-tab-pane key="details" tab="详细分析">
            <div class="analysis-details" v-html="sanitizeHtml(renderMarkdown(result.data.details))" />
          </a-tab-pane>
          <a-tab-pane key="recommendations" tab="建议">
            <div class="analysis-recommendations" v-html="sanitizeHtml(renderMarkdown(result.data.recommendations))" />
          </a-tab-pane>
        </a-tabs>
      </div>
      
      <!-- 默认类型 -->
      <div v-else class="default-result">
        <pre class="result-json">{{ JSON.stringify(result.data, null, 2) }}</pre>
      </div>
    </div>
    
    <div class="result-actions">
      <a-button type="primary" @click="handleExport">
        <ExportOutlined />
        导出结果
      </a-button>
      <a-button @click="handleCopy">
        <CopyOutlined />
        复制内容
      </a-button>
      <a-button @click="handleShare">
        <ShareAltOutlined />
        分享结果
      </a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, h } from 'vue';
import { message } from 'ant-design-vue';
import {
  ExportOutlined,
  CopyOutlined,
  ShareAltOutlined,
} from '@ant-design/icons-vue';
import { useSanitize } from '@/composables/useSanitize';
import type { TaskResult } from '@/types/task';

const { sanitizeHtml } = useSanitize();

const props = defineProps<{
  result: TaskResult;
  executionTime?: number;
}>();

const emit = defineEmits<{
  (e: 'export'): void;
  (e: 'copy'): void;
  (e: 'share'): void;
}>();

const resultTypeColor = computed(() => {
  const colorMap: Record<string, string> = {
    customer_list: 'blue',
    email_draft: 'green',
    research_report: 'purple',
    analysis: 'orange',
  };
  return colorMap[props.result.type] || 'default';
});

const resultTypeText = computed(() => {
  const textMap: Record<string, string> = {
    customer_list: '客户列表',
    email_draft: '邮件草稿',
    research_report: '研究报告',
    analysis: '分析结果',
  };
  return textMap[props.result.type] || '未知类型';
});

const customerColumns = [
  {
    title: '客户名称',
    dataIndex: 'name',
    key: 'name',
  },
  {
    title: '公司',
    dataIndex: 'company',
    key: 'company',
  },
  {
    title: '邮箱',
    dataIndex: 'email',
    key: 'email',
  },
  {
    title: '电话',
    dataIndex: 'phone',
    key: 'phone',
  },
  {
    title: '意向度',
    dataIndex: 'score',
    key: 'score',
  },
];

function formatExecutionTime(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`;
  } else if (ms < 60000) {
    return `${(ms / 1000).toFixed(1)}秒`;
  } else {
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return `${minutes}分${seconds}秒`;
  }
}

function renderMarkdown(content: string): string {
  if (!content) return '';
  
  // 简单的Markdown渲染
  // NOTE: 如需引入 markdown-it 库，请务必配置 { html: false } 以防止 XSS 注入
  let rendered = content;
  
  // 处理标题
  rendered = rendered.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  rendered = rendered.replace(/^## (.*$)/gim, '<h2>$1</h2>');
  rendered = rendered.replace(/^# (.*$)/gim, '<h1>$1</h1>');
  
  // 处理粗体
  rendered = rendered.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  
  // 处理斜体
  rendered = rendered.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  
  // 处理代码块
  rendered = rendered.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>');
  
  // 处理行内代码
  rendered = rendered.replace(/`([^`]+)`/g, '<code>$1</code>');
  
  // 处理列表
  rendered = rendered.replace(/^\s*-\s*(.*)$/gim, '<li>$1</li>');
  rendered = rendered.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
  
  // 处理换行
  rendered = rendered.replace(/\n/g, '<br>');
  
  return rendered;
}

function handleExport() {
  emit('export');
  message.info('导出功能开发中...');
}

function handleCopy() {
  const content = JSON.stringify(props.result.data, null, 2);
  navigator.clipboard.writeText(content);
  message.success('内容已复制到剪贴板');
  emit('copy');
}

function handleShare() {
  emit('share');
  message.info('分享功能开发中...');
}
</script>

<style scoped>
.task-result {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.result-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1a1a1a;
}

.result-meta {
  display: flex;
  gap: 12px;
  align-items: center;
}

.result-time {
  font-size: 14px;
  color: #8c8c8c;
}

.result-summary h4,
.result-content h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.result-summary p {
  margin: 0;
  font-size: 14px;
  color: #52c41a;
  line-height: 1.6;
  padding: 12px;
  background: #f6ffed;
  border-radius: 4px;
  border: 1px solid #b7eb8f;
}

.result-content {
  flex: 1;
}

.customer-list {
  overflow-x: auto;
}

.email-draft {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  overflow: hidden;
}

.email-header {
  padding: 16px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

.email-field {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.email-field:last-child {
  margin-bottom: 0;
}

.field-label {
  font-size: 14px;
  color: #8c8c8c;
  min-width: 60px;
}

.field-value {
  font-size: 14px;
  color: #1a1a1a;
}

.email-body {
  padding: 16px;
  font-size: 14px;
  line-height: 1.6;
  color: #1a1a1a;
}

.research-report,
.analysis-result {
  font-size: 14px;
  line-height: 1.6;
}

.research-report :deep(h1),
.research-report :deep(h2),
.research-report :deep(h3),
.analysis-result :deep(h1),
.analysis-result :deep(h2),
.analysis-result :deep(h3) {
  margin-top: 16px;
  margin-bottom: 8px;
  font-weight: 600;
  color: #1a1a1a;
}

.research-report :deep(pre),
.analysis-result :deep(pre) {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
}

.research-report :deep(code),
.analysis-result :deep(code) {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
}

.default-result {
  background: #fafafa;
  border-radius: 4px;
  overflow: hidden;
}

.result-json {
  margin: 0;
  padding: 16px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
  color: #1a1a1a;
  overflow-x: auto;
}

.result-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

@media (max-width: 768px) {
  .result-header {
    flex-direction: column;
    gap: 12px;
  }
  
  .result-actions {
    flex-direction: column;
  }
  
  .result-actions .ant-btn {
    width: 100%;
  }
}
</style>